# Integration Guide

This document explains how to implement the image-memory workflow in the upstream AAC repository.

## What Problem This Solves

AAC agents often browse or download inspiration images and then spend money or latency on repeated visual analysis.

That is avoidable when the same inspiration images are reused across runs.

The right architecture is:

- keep the original image in the repo or workspace
- build a deterministic local memory record for it
- save a preview PNG for cheap visual recall
- query that memory first in later agent runs

## Recommended Repo Layout

Add these folders at repo root:

```text
image_memory_workflow/
  README.md
  INTEGRATION.md
  API_INGESTION.md
  scripts/

workspace/
  sources/
  source_metadata/
  image_memory/
```

If the upstream repo prefers a different layout, keep the same separation:

- raw images
- metadata sidecars
- built memory cache
- workflow scripts

## Minimum Integration Steps

1. Copy this `image_memory_workflow/` folder into the upstream repo.
2. Decide the canonical raw-image directory.
   Recommended: `workspace/sources/`
3. Decide the canonical cache directory.
   Recommended: `workspace/image_memory/`
4. Update the agent instructions so image memory is checked before vision.
5. Add one build step after any new inspiration images are downloaded.

## Scope Guardrail

This workflow is intentionally narrow.

It should only change the way inspiration images are:

- downloaded into repo-local storage
- preprocessed into cached readable data
- queried before a visual model is used

It should **not** change any other AAC behavior.

Do not use this workflow to modify:

- the artistic goals of AAC
- the inspiration study requirement
- the composition process
- the dithering process
- plot selection logic
- edge-awareness behavior
- submission or on-chain draw flow
- review standards for whether art is strong enough to submit

This is a token-efficiency and cost-efficiency layer only.

## Agent Workflow Change

Before:

1. search source API
2. download image
3. inspect image with a visual model
4. compose

After:

1. search source API
2. download image
3. run `build_image_memory.py`
4. query `image_memory`
5. only use a visual model if the memory record is missing or insufficient
6. compose

## Suggested Skill Change

Add a rule like this to the AAC skill:

```md
Before using a vision model on any image in `workspace/sources/`, check the image-memory cache first.

1. Query `workspace/image_memory/index.json` or run `image_memory_workflow/scripts/query_image_memory.py`.
2. Read the matching `workspace/image_memory/records/*.json`.
3. Use the cached preview in `workspace/image_memory/previews/` when a cheap visual reference is enough.
4. Only call a vision model if the image is not in the cache or the cache is not detailed enough for the task.
5. After any new inspiration image is downloaded, rebuild the cache.
```

The skill patch should be minimal:

- insert an image-memory check before visual-model analysis
- add the manifest-download step for newly selected inspiration images
- build the readable cache after the selected API images have been imported for that run or batch
- leave every other part of the skill unchanged

## When to Rebuild the Cache

Rebuild when:

- new inspiration images are added
- existing source files change
- you improve the cache schema
- you add semantic sidecar data

Command:

```bash
python3 image_memory_workflow/scripts/build_image_memory.py
```

You can also target a different collection:

```bash
python3 image_memory_workflow/scripts/build_image_memory.py \
  --source-dir inspiration \
  --output-dir workspace/inspiration_memory
```

## How to Handle Bundled Inspiration Pages

The same workflow works for the bundled `inspiration/` pages from Zen and the Art of the Macintosh.

Example:

```bash
python3 image_memory_workflow/scripts/build_image_memory.py \
  --source-dir inspiration \
  --output-dir workspace/inspiration_memory
```

This creates a searchable memory layer for the entire book without repeated visual-model calls.

## How to Handle Downloaded API Images

Use the generic manifest downloader:

```bash
python3 image_memory_workflow/scripts/download_image_manifest.py \
  path/to/manifest.jsonl \
  --output-dir workspace/sources/imported \
  --metadata-dir workspace/source_metadata
```

Then build memory:

```bash
python3 image_memory_workflow/scripts/build_image_memory.py \
  --source-dir workspace/sources/imported \
  --output-dir workspace/image_memory/imported
```

## Manifest Format

Each manifest entry should normalize API results into this shape:

```json
{
  "id": "met_12345",
  "url": "https://images.metmuseum.org/CRDImages/ad/web-large/DP123.jpg",
  "filename": "met_12345.jpg",
  "source_api": "met",
  "query": "roman bust",
  "title": "Bust of a Man",
  "creator": "Unknown",
  "license": "public domain",
  "source_url": "https://www.metmuseum.org/art/collection/search/12345",
  "metadata_url": "https://collectionapi.metmuseum.org/public/collection/v1/objects/12345",
  "headers": {
    "Authorization": "Client-ID ... only when required"
  }
}
```

Only `url` is required by the downloader, but the other fields are strongly recommended because they make the repo memory useful later.

## How Future Agents Should Use the Cache

If the task is retrieval or inspiration selection:

1. run `query_image_memory.py` by text
2. inspect the matching record JSON
3. open the cached preview PNG if needed
4. only open the original full-size image if exact detail is needed

If the task is image similarity:

1. run `query_image_memory.py --image ...`
2. inspect the nearest neighbors
3. only use a vision model if the local similarity result is not enough

## Carbon Copy vs Semantic Summary

There are two different cache levels:

- semantic cache:
  good for search, tagging, and prompt scaffolding
- preview cache:
  good for near-copy visual recall without re-running expensive analysis

If you want later agents to be able to visually re-open the image cheaply, the preview cache is the important part.

## What To Commit

Commit:

- `image_memory_workflow/`
- cached memory records if the repo wants deterministic shared reuse
- cached preview PNGs if their size is acceptable

Do not commit:

- secret API keys
- temporary manifests containing private credentials

## Recommended Next Upstream Patch

After copying this folder upstream, update the skill and any download helpers so that:

1. all new inspiration images are normalized into manifests
2. downloads go through the manifest downloader
3. memory build runs after the selected API images have been imported into repo storage
4. later agents query memory first
