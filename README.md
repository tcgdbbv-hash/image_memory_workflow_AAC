# Image Memory Workflow

This repository packages a reusable image-memory workflow for preprocessing inspiration images into a cheap local cache.

The goal is simple:

- pay the expensive visual-analysis cost once
- store reusable image memory inside the repo
- let later agents query cached image memory before they call a vision model again

This workflow does **not** replace the original source image. It adds a repo-local memory layer on top of it:

- raw source images remain the pixel ground truth
- cached preview images provide cheap visual recall
- JSON records provide deterministic retrieval and reusable metadata

## Repository Contents

- `scripts/build_image_memory.py`
  Builds a memory store from a folder of source images.
- `scripts/query_image_memory.py`
  Queries the cache by text or by image similarity.
- `scripts/recreate_from_image_memory.py`
  Recreates near-copy images from cached preview assets.
- `scripts/download_image_manifest.py`
  Downloads normalized image manifests from any API into the repo.
- `INTEGRATION.md`
  How to wire this into the AAC repo and agent workflow.
- `API_INGESTION.md`
  API-by-API instructions for every image source listed in the original AAC skill.

## Requirements

```bash
pip install -r requirements.txt
```

## Quick Start

1. Put source images in `workspace/sources/` or another source folder.
2. Build the memory cache:

```bash
python3 scripts/build_image_memory.py
```

3. Query the cache before using a vision model:

```bash
python3 scripts/query_image_memory.py "round glasses seated man"
```

4. If you need a cheap visual stand-in without touching the original file:

```bash
python3 scripts/recreate_from_image_memory.py
```

## Default Output Layout

By default the scripts write to:

- `workspace/image_memory/index.json`
- `workspace/image_memory/memory.jsonl`
- `workspace/image_memory/records/*.json`
- `workspace/image_memory/previews/*.png`

Each valid record stores:

- source path and SHA-256
- size, mode, brightness stats
- average hash, difference hash, perceptual hash
- dominant palette
- `16x16` RGB hex grid
- `8x8` luminance, saturation, and edge-density grids
- cached preview PNG path
- compact feature vector for local similarity
- optional semantic cache if companion ingest files exist

## Why This Exists

In the default AAC flow, agents often:

1. search an API
2. download inspiration images
3. call a visual model to understand those images
4. repeat the same work in later runs

This repository turns that repeated visual work into a reusable repo asset.

The intended rule is:

1. search or download inspiration images once
2. cache them with `build_image_memory.py`
3. let future agents read `index.json`, `memory.jsonl`, and `records/*.json`
4. only call a visual model when the cache is missing or clearly insufficient

## Recommended Commit Shape

If you upstream this into AAC, keep these parts together:

- this repository, or the equivalent `image_memory_workflow/` folder copied into AAC
- a repo path for raw inspiration images
- a repo path for built memory caches
- a rule in the skill or docs telling agents to query memory first

The detailed integration steps are in [INTEGRATION.md](INTEGRATION.md), and the source-by-source ingestion guide is in [API_INGESTION.md](API_INGESTION.md).
