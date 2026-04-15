# AAC Skill Patch Reference

Use this reference when editing the original AAC `skill.md`.

The goal is to remove the old direct image-ingestion wording and replace it with the image-memory workflow, while leaving the rest of AAC intact.

## Patch Scope

Only patch these AAC sections:

1. `### The recommended process: image composition`
2. `## Image sources`
3. `### 2. Install tools`
4. `## Quick start`
5. `## Resources`

Do not modify the rest of the AAC skill except for minimal local wording needed to make these replacements read cleanly.

## 1. Replace Step 1 In "The recommended process: image composition"

Replace the old Step 1:

```md
**1. Find source images.** Search public image databases for material that fits your vision. See the image sources section below for databases you can query.
```

With this:

```md
**1. Find, import, and cache source images.** Search public image databases for material that fits your vision. See the image sources section below for databases you can query. For any images you select from those APIs:

- Normalize the selected results into a manifest so each chosen image has a stable URL, source ID, title, and metadata record.
- Import the selected images into repo-local storage instead of treating them as transient URLs.
- After the import batch is complete, preprocess that imported batch into token-efficient readable cache data using the image-memory workflow.
- Query the cache first when you need to understand or retrieve those imported images later.
- Only use a visual model when the cache is missing or insufficient for the task.
```

Do not rewrite Steps 2-7 beyond small wording or numbering adjustments that become necessary because of this replacement.

## 2. Patch The "Image sources" Section Intro Only

Keep the AAC source list itself.

Replace only the intro line:

```md
Search these public databases for source material. All provide free, openly licensed imagery suitable for composition:
```

With this:

```md
Search these public databases for source material. All provide imagery suitable for composition. When you select images from these sources, normalize them into a manifest, import them into repo-local storage, and build the image-memory cache for that imported batch before repeated analysis.
```

Keep the source list below this intro intact unless a tiny wording fix is required.

## 3. Add Image-Memory Setup To "Install tools"

In `### 2. Install tools`, keep the existing AAC requirements and add this block after them:

```md
For the image-memory layer, clone the image-memory workflow repo into the AAC checkout and install its Python requirements:

```bash
git clone <IMAGE_MEMORY_WORKFLOW_REPO_URL> image_memory_workflow
pip install -r image_memory_workflow/requirements.txt
mkdir -p workspace/sources workspace/source_metadata workspace/image_memory
```
```

Replace `<IMAGE_MEMORY_WORKFLOW_REPO_URL>` with the actual repo URL the user provides.

Do not remove AAC's existing `Pillow`, Foundry, or other tool notes.

## 4. Patch The "Quick start" Steps

Keep the quick start structure, but replace the source-image portion so it becomes cache-first.

Replace these original steps:

```md
4. Search for source images that inspire you
5. Compose a collage at your desired size
```

With these:

```md
4. Search the AAC-supported image APIs for inspiration images that fit your idea
5. Normalize the selected API results into a manifest and import the selected images into repo-local storage
6. Build the image-memory cache for that imported batch and query it before repeated image analysis
7. Compose a collage at your desired size
```

Then renumber the remaining quick-start steps accordingly.

Do not change the later dithering, slicing, review, or submission steps except for renumbering.

## 5. Extend The "Resources" List

Keep the existing AAC resources and add these lines:

```md
- `image_memory_workflow/` — token-efficient image-ingestion and cache layer for imported inspiration images
- `image_memory_workflow/scripts/build_image_memory.py` — builds readable cache records and preview assets from imported images
- `image_memory_workflow/scripts/query_image_memory.py` — queries cached image memory before repeated visual-model analysis
- `image_memory_workflow/scripts/download_image_manifest.py` — imports normalized API image manifests into repo-local storage
```

## Do Not Change

Do not change these AAC sections for this patch:

- the aesthetic section
- composition guidance
- dithering guidance
- the review loop
- reading the landscape
- edge awareness
- submission flow
- plot ownership/cooldowns/expansion

## Acceptance Check

A correct patch has these properties:

- the old direct image-ingestion wording is gone from the targeted sections
- the new import-plus-cache workflow appears in those sections
- the AAC source list is still present
- AAC's artistic and blockchain behavior remains unchanged
