#!/usr/bin/env python3

import argparse
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE_DIR = ROOT / "workspace" / "sources"
DEFAULT_OUTPUT_DIR = ROOT / "workspace" / "image_memory"
VISUAL_INGEST_PATH = ROOT / "workspace" / "source_image_visual_ingest.json"
MODEL_INGEST_PATH = ROOT / "workspace" / "source_image_model_ingest.json"
PREVIEW_MAX_SIDE = 512


def utc_timestamp():
    return datetime.now(timezone.utc).isoformat()


def ensure_dir(path):
    path.mkdir(parents=True, exist_ok=True)


def sha256_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def create_preview(image, preview_path, max_side=PREVIEW_MAX_SIDE):
    preview = image.convert("RGB").copy()
    preview.thumbnail((max_side, max_side), Image.Resampling.LANCZOS)
    preview.save(preview_path, optimize=True)
    return preview


def dct_matrix(n):
    x = np.arange(n)
    k = np.arange(n).reshape(-1, 1)
    matrix = np.cos(np.pi * (2 * x + 1) * k / (2 * n))
    matrix[0] *= 1 / math.sqrt(n)
    matrix[1:] *= math.sqrt(2 / n)
    return matrix


DCT32 = dct_matrix(32)


def a_hash(image):
    gray = image.convert("L").resize((8, 8), Image.Resampling.LANCZOS)
    arr = np.asarray(gray, dtype=np.float32)
    mean = arr.mean()
    bits = "".join("1" if value >= mean else "0" for value in arr.flatten())
    return f"{int(bits, 2):016x}"


def d_hash(image):
    gray = image.convert("L").resize((9, 8), Image.Resampling.LANCZOS)
    arr = np.asarray(gray, dtype=np.float32)
    diff = arr[:, 1:] >= arr[:, :-1]
    bits = "".join("1" if value else "0" for value in diff.flatten())
    return f"{int(bits, 2):016x}"


def p_hash(image):
    gray = image.convert("L").resize((32, 32), Image.Resampling.LANCZOS)
    arr = np.asarray(gray, dtype=np.float32)
    dct = DCT32 @ arr @ DCT32.T
    low = dct[:8, :8]
    median = np.median(low[1:, 1:])
    bits = "".join("1" if value >= median else "0" for value in low.flatten())
    return f"{int(bits, 2):016x}"


def hex_hamming(a, b):
    return bin(int(a, 16) ^ int(b, 16)).count("1")


def normalize_text(text):
    return " ".join(str(text).lower().split())


def average_grid(arr, rows, cols):
    height, width = arr.shape[:2]
    result = []
    for row in range(rows):
        y0 = height * row // rows
        y1 = height * (row + 1) // rows
        result_row = []
        for col in range(cols):
            x0 = width * col // cols
            x1 = width * (col + 1) // cols
            block = arr[y0:y1, x0:x1]
            if arr.ndim == 3:
                mean = block.mean(axis=(0, 1))
                result_row.append([round(float(value), 2) for value in mean.tolist()])
            else:
                result_row.append(round(float(block.mean()), 2))
        result.append(result_row)
    return result


def color_hex_grid(rgb_arr, rows=16, cols=16):
    grid = average_grid(rgb_arr, rows, cols)
    hex_grid = []
    for row in grid:
        hex_row = []
        for value in row:
            r, g, b = [int(round(v)) for v in value]
            hex_row.append(f"#{r:02x}{g:02x}{b:02x}")
        hex_grid.append(hex_row)
    return hex_grid


def dominant_palette(image, count=8):
    small = image.convert("RGB").copy()
    quantized = small.quantize(colors=count, method=Image.Quantize.MEDIANCUT)
    raw = quantized.getpalette()
    colors = quantized.getcolors()
    colors = sorted(colors or [], reverse=True)
    palette = []
    for freq, index in colors[:count]:
        rgb = raw[index * 3:index * 3 + 3]
        palette.append(
            {
                "rgb": rgb,
                "hex": f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}",
                "weight": round(freq / max(1, image.width * image.height), 6),
            }
        )
    return palette


def histograms(rgb_arr):
    hist = {}
    for idx, channel in enumerate(("r", "g", "b")):
        values, _ = np.histogram(rgb_arr[:, :, idx], bins=16, range=(0, 256), density=True)
        hist[channel] = [round(float(v), 6) for v in values.tolist()]
    gray = np.dot(rgb_arr[..., :3], [0.299, 0.587, 0.114])
    values, _ = np.histogram(gray, bins=16, range=(0, 256), density=True)
    hist["luma"] = [round(float(v), 6) for v in values.tolist()]
    return hist


def image_arrays(image):
    rgb = np.asarray(image.convert("RGB"), dtype=np.float32)
    gray = np.dot(rgb[..., :3], [0.299, 0.587, 0.114]).astype(np.float32)
    maxc = rgb.max(axis=2)
    minc = rgb.min(axis=2)
    saturation = np.divide(
        maxc - minc,
        maxc,
        out=np.zeros_like(maxc),
        where=maxc != 0,
    )
    saturation = (saturation * 255.0).astype(np.float32)
    edge = np.asarray(image.convert("L").filter(ImageFilter.FIND_EDGES), dtype=np.float32)
    return rgb, gray, saturation, edge


def feature_vector(gray_grid, sat_grid, edge_grid, aspect_ratio, palette):
    values = []
    values.extend(np.asarray(gray_grid, dtype=np.float32).flatten() / 255.0)
    values.extend(np.asarray(sat_grid, dtype=np.float32).flatten() / 255.0)
    values.extend(np.asarray(edge_grid, dtype=np.float32).flatten() / 255.0)
    values.append(float(aspect_ratio))
    for item in palette[:4]:
        values.extend([channel / 255.0 for channel in item["rgb"]])
        values.append(item["weight"])
    return [round(float(v), 6) for v in values]


def cosine_similarity(a, b):
    va = np.asarray(a, dtype=np.float32)
    vb = np.asarray(b, dtype=np.float32)
    denom = np.linalg.norm(va) * np.linalg.norm(vb)
    if denom == 0:
        return 0.0
    return float(np.dot(va, vb) / denom)


def load_semantic_cache(path, root_key):
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError:
        return {}
    entries = {}
    for item in data.get(root_key, []):
        entries[item.get("file")] = item
    return entries


def retrieval_text(record):
    text_parts = [
        record["source"]["file_name"],
        record["source"]["stem"],
        record["semantic_cache"]["quick_summary"],
        record["semantic_cache"]["scene_type"],
        " ".join(record["semantic_cache"]["primary_subjects"]),
        " ".join(record["semantic_cache"]["tokens"]),
        " ".join(record["semantic_cache"]["compressed_scene_tokens"]),
        " ".join(record["semantic_cache"]["look_order_focus"]),
    ]
    return normalize_text(" ".join(part for part in text_parts if part))


def build_record(image_path, visual_cache, model_cache, preview_dir):
    base = {
        "id": image_path.stem,
        "source": {
            "file_name": image_path.name,
            "stem": image_path.stem,
            "path": str(image_path.resolve()),
            "sha256": sha256_file(image_path),
            "file_size_bytes": image_path.stat().st_size,
        },
    }
    try:
        image = Image.open(image_path)
        image.load()
    except Exception as exc:
        base["status"] = "invalid_image_file"
        base["error"] = str(exc)
        return base

    rgb_arr, gray_arr, sat_arr, edge_arr = image_arrays(image)
    gray_grid = average_grid(gray_arr, 8, 8)
    sat_grid = average_grid(sat_arr, 8, 8)
    edge_grid = average_grid(edge_arr, 8, 8)
    palette = dominant_palette(image)

    visual_ingest = (visual_cache or {}).get("visual_ingest", {})
    model_ingest = model_cache or {}
    quick_summary = (
        model_ingest.get("gist")
        or visual_ingest.get("one_line_summary")
        or ""
    )
    scene_type = visual_ingest.get("scene_type", "")
    primary_subjects = visual_ingest.get("primary_subjects", [])
    tokens = visual_ingest.get("ingest_tokens", [])
    compressed_scene_tokens = model_ingest.get("compressed_scene_tokens", [])
    look_order_focus = [item.get("focus", "") for item in model_ingest.get("look_order", [])]

    ensure_dir(preview_dir)
    preview_path = preview_dir / f"{image_path.stem}_preview.png"
    preview = create_preview(image, preview_path)

    record = {
        **base,
        "status": "valid",
        "technical": {
            "width": image.width,
            "height": image.height,
            "aspect_ratio": round(image.width / image.height, 6),
            "mode": image.mode,
            "average_rgb": [round(float(v), 2) for v in rgb_arr.mean(axis=(0, 1)).tolist()],
            "luminance_mean": round(float(gray_arr.mean()), 2),
            "luminance_stddev": round(float(gray_arr.std()), 2),
        },
        "hashes": {
            "average_hash": a_hash(image),
            "difference_hash": d_hash(image),
            "perceptual_hash": p_hash(image),
        },
        "visual_features": {
            "dominant_palette": palette,
            "rgb_hex_grid_16x16": color_hex_grid(rgb_arr, 16, 16),
            "preview_rgb_hex_grid_32x32": color_hex_grid(np.asarray(preview.convert("RGB"), dtype=np.float32), 32, 32),
            "luminance_grid_8x8": gray_grid,
            "saturation_grid_8x8": sat_grid,
            "edge_density_grid_8x8": edge_grid,
            "histograms_16bin": histograms(rgb_arr),
        },
        "memory_assets": {
            "preview_png_path": str(preview_path.resolve()),
            "preview_size": [preview.width, preview.height],
            "preview_sha256": sha256_file(preview_path),
            "preview_max_side": PREVIEW_MAX_SIDE,
        },
        "semantic_cache": {
            "quick_summary": quick_summary,
            "scene_type": scene_type,
            "primary_subjects": primary_subjects,
            "tokens": tokens,
            "compressed_scene_tokens": compressed_scene_tokens,
            "look_order_focus": look_order_focus,
            "visual_ingest_ref": str(VISUAL_INGEST_PATH.resolve()) if visual_cache else None,
            "model_ingest_ref": str(MODEL_INGEST_PATH.resolve()) if model_cache else None,
        },
        "feature_vector": feature_vector(
            gray_grid,
            sat_grid,
            edge_grid,
            image.width / image.height,
            palette,
        ),
    }
    record["retrieval_text"] = retrieval_text(record)
    return record


def build_memory(source_dir, output_dir):
    ensure_dir(output_dir)
    records_dir = output_dir / "records"
    ensure_dir(records_dir)
    previews_dir = output_dir / "previews"
    ensure_dir(previews_dir)

    visual_cache = load_semantic_cache(VISUAL_INGEST_PATH, "images")
    model_cache = load_semantic_cache(MODEL_INGEST_PATH, "images")

    records = []
    search_rows = []
    for path in sorted(source_dir.iterdir()):
        if path.is_dir():
            continue
        record = build_record(path, visual_cache.get(path.name), model_cache.get(path.name), previews_dir)
        record_path = records_dir / f"{path.stem}.json"
        record_path.write_text(json.dumps(record, indent=2))
        summary = {
            "id": record["id"],
            "file_name": path.name,
            "status": record["status"],
            "record_path": str(record_path.resolve()),
        }
        if record["status"] == "valid":
            summary["quick_summary"] = record["semantic_cache"]["quick_summary"]
            summary["tokens"] = (
                record["semantic_cache"]["tokens"][:]
                + record["semantic_cache"]["compressed_scene_tokens"][:]
            )
            summary["aspect_ratio"] = record["technical"]["aspect_ratio"]
            summary["hashes"] = record["hashes"]
            summary["preview_png_path"] = record["memory_assets"]["preview_png_path"]
            search_rows.append(
                {
                    "id": record["id"],
                    "file_name": path.name,
                    "text": record["retrieval_text"],
                    "record_path": str(record_path.resolve()),
                }
            )
        else:
            summary["error"] = record.get("error")
        records.append(summary)

    valid_records = [
        json.loads(Path(item["record_path"]).read_text())
        for item in records
        if item["status"] == "valid"
    ]

    similarity = []
    for i, left in enumerate(valid_records):
        row = {"id": left["id"], "neighbors": []}
        for j, right in enumerate(valid_records):
            if i == j:
                continue
            score = cosine_similarity(left["feature_vector"], right["feature_vector"])
            hash_penalty = (
                hex_hamming(left["hashes"]["perceptual_hash"], right["hashes"]["perceptual_hash"]) / 64.0
            )
            composite = round(score * 0.8 + (1.0 - hash_penalty) * 0.2, 6)
            row["neighbors"].append({"id": right["id"], "score": composite})
        row["neighbors"].sort(key=lambda item: item["score"], reverse=True)
        row["neighbors"] = row["neighbors"][:5]
        similarity.append(row)

    index = {
        "schema_version": "1.0",
        "generated_at": utc_timestamp(),
        "description": "Repo-local hybrid image memory cache. Read this before using a vision model on workspace/sources.",
        "source_dir": str(source_dir.resolve()),
        "records_dir": str(records_dir.resolve()),
        "image_count": len(records),
        "valid_image_count": len(valid_records),
        "records": records,
        "similarity_index": similarity,
    }

    (output_dir / "index.json").write_text(json.dumps(index, indent=2))
    with (output_dir / "memory.jsonl").open("w") as handle:
        for row in search_rows:
            handle.write(json.dumps(row) + "\n")
    return index


def main():
    parser = argparse.ArgumentParser(description="Build a repo-local memory store for images.")
    parser.add_argument("--source-dir", default=str(DEFAULT_SOURCE_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()

    source_dir = Path(args.source_dir)
    output_dir = Path(args.output_dir)
    index = build_memory(source_dir, output_dir)
    print(
        f"built image memory for {index['valid_image_count']} valid images "
        f"({index['image_count']} total) at {output_dir.resolve()}"
    )


if __name__ == "__main__":
    main()
