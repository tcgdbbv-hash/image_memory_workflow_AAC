#!/usr/bin/env python3

import argparse
import json
import re
import tempfile
from pathlib import Path

from build_image_memory import DEFAULT_OUTPUT_DIR, DEFAULT_SOURCE_DIR, build_record, cosine_similarity, hex_hamming


def tokenize(text):
    return [token for token in re.split(r"[^a-z0-9]+", text.lower()) if token]


def load_index(output_dir):
    index_path = output_dir / "index.json"
    if not index_path.exists():
        raise SystemExit(
            f"image memory index not found at {index_path}. "
            "Run build_image_memory.py first."
        )
    return json.loads(index_path.read_text())


def load_record(path):
    return json.loads(Path(path).read_text())


def text_score(record, query_terms):
    haystack = record.get("retrieval_text", "")
    score = 0.0
    for term in query_terms:
        if term in record["source"]["stem"].lower():
            score += 5.0
        if term in haystack:
            score += 2.0
        for token in record["semantic_cache"]["tokens"] + record["semantic_cache"]["compressed_scene_tokens"]:
            if term == token.lower():
                score += 3.0
    return score


def print_text_results(results, limit):
    for item in results[:limit]:
        record = item["record"]
        print(f"{item['score']:.2f}  {record['source']['file_name']}")
        print(f"  path: {record['source']['path']}")
        print(f"  summary: {record['semantic_cache']['quick_summary']}")
        print(
            "  tags: "
            + ", ".join(
                record["semantic_cache"]["compressed_scene_tokens"][:6]
                or record["semantic_cache"]["tokens"][:6]
            )
        )


def print_image_results(results, limit):
    for item in results[:limit]:
        record = item["record"]
        print(f"{item['score']:.4f}  {record['source']['file_name']}")
        print(f"  path: {record['source']['path']}")
        print(f"  summary: {record['semantic_cache']['quick_summary']}")
        print(
            "  phash distance: "
            f"{item['phash_distance']}  cosine: {item['cosine']:.4f}"
        )


def main():
    parser = argparse.ArgumentParser(description="Query the repo-local image memory cache.")
    parser.add_argument("query", nargs="?", help="Keyword query against cached image memory.")
    parser.add_argument("--image", help="Path to an image to query by visual similarity.")
    parser.add_argument("--top", type=int, default=5)
    parser.add_argument("--memory-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()

    output_dir = Path(args.memory_dir)
    index = load_index(output_dir)
    valid_records = [
        load_record(item["record_path"])
        for item in index["records"]
        if item["status"] == "valid"
    ]

    if args.image:
        query_path = Path(args.image)
        with tempfile.TemporaryDirectory(prefix="image_memory_query_") as temp_dir:
            query_record = build_record(query_path, None, None, Path(temp_dir))
        if query_record["status"] != "valid":
            raise SystemExit(f"unable to process query image: {query_record.get('error', 'unknown error')}")
        results = []
        for record in valid_records:
            cosine = cosine_similarity(query_record["feature_vector"], record["feature_vector"])
            phash_distance = hex_hamming(
                query_record["hashes"]["perceptual_hash"],
                record["hashes"]["perceptual_hash"],
            )
            score = cosine * 0.8 + (1.0 - phash_distance / 64.0) * 0.2
            results.append(
                {
                    "record": record,
                    "score": score,
                    "cosine": cosine,
                    "phash_distance": phash_distance,
                }
            )
        results.sort(key=lambda item: item["score"], reverse=True)
        print_image_results(results, args.top)
        return

    if not args.query:
        raise SystemExit("provide a text query or --image")

    terms = tokenize(args.query)
    results = []
    for record in valid_records:
        score = text_score(record, terms)
        if score > 0:
            results.append({"record": record, "score": score})
    results.sort(key=lambda item: item["score"], reverse=True)
    print_text_results(results, args.top)


if __name__ == "__main__":
    main()
