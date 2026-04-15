#!/usr/bin/env python3

import argparse
import json
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MEMORY_DIR = ROOT / "workspace" / "image_memory"
DEFAULT_OUTPUT_DIR = ROOT / "workspace" / "recreated_from_memory"


def ensure_dir(path):
    path.mkdir(parents=True, exist_ok=True)


def fit_contain(image, size, fill=(255, 255, 255)):
    target_w, target_h = size
    scale = min(target_w / image.width, target_h / image.height)
    resized = image.resize(
        (max(1, int(round(image.width * scale))), max(1, int(round(image.height * scale)))),
        Image.Resampling.LANCZOS,
    )
    canvas = Image.new("RGB", size, fill)
    left = (target_w - resized.width) // 2
    top = (target_h - resized.height) // 2
    canvas.paste(resized, (left, top))
    return canvas


def save_contact_sheet(images, target_path, title, columns=1):
    if not images:
        return
    thumb_w = 760
    thumb_h = 320
    padding = 20
    label_h = 34
    rows = math.ceil(len(images) / columns)
    width = columns * thumb_w + (columns + 1) * padding
    height = 70 + rows * (thumb_h + label_h) + (rows + 1) * padding
    sheet = Image.new("RGB", (width, height), (247, 245, 241))
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()
    draw.text((padding, 20), title, fill=(30, 30, 30), font=font)
    for index, (label, image) in enumerate(images):
        row = index // columns
        col = index % columns
        x = padding + col * (thumb_w + padding)
        y = 60 + padding + row * (thumb_h + label_h + padding)
        thumb = fit_contain(image, (thumb_w, thumb_h))
        sheet.paste(thumb, (x, y))
        draw.rectangle((x, y, x + thumb_w - 1, y + thumb_h - 1), outline=(190, 186, 176), width=1)
        draw.text((x, y + thumb_h + 10), label, fill=(40, 40, 40), font=font)
    sheet.save(target_path)


def recreate_from_record(record):
    preview_path = Path(record["memory_assets"]["preview_png_path"])
    preview = Image.open(preview_path).convert("RGB")
    target_size = (record["technical"]["width"], record["technical"]["height"])
    recreated = preview.resize(target_size, Image.Resampling.LANCZOS)
    recreated = recreated.filter(ImageFilter.UnsharpMask(radius=1.6, percent=135, threshold=2))
    return recreated


def build_comparison_pair(record, recreated):
    source = Image.open(record["source"]["path"]).convert("RGB")
    width = 360
    left = fit_contain(source, (width, width))
    right = fit_contain(recreated, (width, width))
    combo = Image.new("RGB", (width * 2 + 18, width), (248, 246, 242))
    combo.paste(left, (0, 0))
    combo.paste(right, (width + 18, 0))
    draw = ImageDraw.Draw(combo)
    font = ImageFont.load_default()
    draw.rectangle((0, 0, width - 1, width - 1), outline=(195, 190, 180), width=1)
    draw.rectangle((width + 18, 0, width * 2 + 17, width - 1), outline=(195, 190, 180), width=1)
    draw.text((12, 12), "source", fill=(30, 30, 30), font=font)
    draw.text((width + 30, 12), "from cached preview", fill=(30, 30, 30), font=font)
    return combo


def main():
    parser = argparse.ArgumentParser(description="Recreate images from cached image-memory preview assets.")
    parser.add_argument("--memory-dir", default=str(DEFAULT_MEMORY_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()

    memory_dir = Path(args.memory_dir)
    output_dir = Path(args.output_dir)
    ensure_dir(output_dir)

    index = json.loads((memory_dir / "index.json").read_text())
    comparison_images = []
    recreated_list = []

    for item in index["records"]:
        if item["status"] != "valid":
            continue
        record = json.loads(Path(item["record_path"]).read_text())
        recreated = recreate_from_record(record)
        target = output_dir / f"{record['source']['stem']}_recreated.png"
        recreated.save(target)
        print(f"saved {target}")
        recreated_list.append((record["source"]["file_name"], recreated))
        comparison_images.append((record["source"]["file_name"], build_comparison_pair(record, recreated)))

    save_contact_sheet(
        recreated_list,
        output_dir / "recreated_contact_sheet.png",
        "Images Recreated From Cached Preview Assets",
        columns=2,
    )
    save_contact_sheet(
        comparison_images,
        output_dir / "comparison_sheet.png",
        "Source vs Recreation From Cached Preview Assets",
        columns=1,
    )


if __name__ == "__main__":
    main()
