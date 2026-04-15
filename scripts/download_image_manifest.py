#!/usr/bin/env python3

import argparse
import json
import mimetypes
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = ROOT / "workspace" / "sources" / "imported"
DEFAULT_METADATA_DIR = ROOT / "workspace" / "source_metadata"
DEFAULT_USER_AGENT = "aac-image-memory/1.0"


def ensure_dir(path):
    path.mkdir(parents=True, exist_ok=True)


def load_manifest(path):
    text = path.read_text().strip()
    if not text:
        return []
    if path.suffix.lower() == ".jsonl":
        return [json.loads(line) for line in text.splitlines() if line.strip()]
    data = json.loads(text)
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and "items" in data:
        return data["items"]
    raise SystemExit("manifest must be a JSON array, JSONL file, or JSON object with an items array")


def safe_name(value):
    cleaned = "".join(ch if ch.isalnum() or ch in ("-", "_", ".") else "_" for ch in value)
    return cleaned.strip("._") or "image"


def infer_extension(url, content_type):
    path = urlparse(url).path
    suffix = Path(path).suffix.lower()
    if suffix in {".jpg", ".jpeg", ".png", ".gif", ".webp", ".tif", ".tiff", ".bmp"}:
        return suffix
    if content_type:
        ext = mimetypes.guess_extension(content_type.split(";")[0].strip())
        if ext:
            return ".jpg" if ext == ".jpe" else ext
    return ".jpg"


def fetch(entry):
    headers = dict(entry.get("headers") or {})
    headers.setdefault("User-Agent", DEFAULT_USER_AGENT)
    request = Request(entry["url"], headers=headers)
    with urlopen(request) as response:
        body = response.read()
        content_type = response.headers.get("Content-Type", "")
    return body, content_type


def build_base_name(entry, index):
    if entry.get("filename"):
        return safe_name(Path(entry["filename"]).stem)
    if entry.get("id"):
        return safe_name(str(entry["id"]))
    if entry.get("title"):
        return safe_name(str(entry["title"]))[:80]
    return f"image_{index:04d}"


def write_metadata(path, entry, image_path, content_type):
    payload = {
        "id": entry.get("id"),
        "source_api": entry.get("source_api"),
        "query": entry.get("query"),
        "title": entry.get("title"),
        "creator": entry.get("creator"),
        "license": entry.get("license"),
        "source_url": entry.get("source_url"),
        "metadata_url": entry.get("metadata_url"),
        "image_url": entry.get("url"),
        "saved_path": str(image_path.resolve()),
        "content_type": content_type,
    }
    path.write_text(json.dumps(payload, indent=2))


def main():
    parser = argparse.ArgumentParser(description="Download a normalized image manifest into workspace sources.")
    parser.add_argument("manifest", help="Path to JSON or JSONL manifest")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--metadata-dir", default=str(DEFAULT_METADATA_DIR))
    parser.add_argument("--skip-existing", action="store_true")
    args = parser.parse_args()

    manifest_path = Path(args.manifest)
    output_dir = Path(args.output_dir)
    metadata_dir = Path(args.metadata_dir)
    ensure_dir(output_dir)
    ensure_dir(metadata_dir)

    items = load_manifest(manifest_path)
    for index, entry in enumerate(items, start=1):
        if "url" not in entry:
            raise SystemExit(f"manifest entry {index} is missing url")
        base_name = build_base_name(entry, index)
        body, content_type = fetch(entry)
        extension = infer_extension(entry["url"], content_type)
        image_path = output_dir / f"{base_name}{extension}"
        metadata_path = metadata_dir / f"{base_name}.json"

        if args.skip_existing and image_path.exists():
            print(f"skip {image_path}")
            continue

        image_path.write_bytes(body)
        write_metadata(metadata_path, entry, image_path, content_type)
        print(f"saved {image_path}")


if __name__ == "__main__":
    main()
