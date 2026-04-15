---
name: aac-image-memory-patch
description: Integrate this repository into an ASCII Agent City checkout so inspiration images from the AAC-supported source APIs are imported, converted into token-efficient readable cache data, and queried before repeated visual-model analysis. Use this skill only for the image-ingestion and image-memory layer. Do not use it to change AAC aesthetics, composition guidance, dithering, review standards, plot logic, or on-chain submission behavior.
---

# AAC Image Memory Patch

Use this skill when you need to patch an existing ASCII Agent City checkout so repeated inspiration-image analysis becomes cheaper and more token-efficient.

## Read First

- Read [SKILL_PATCH_NOTES.md](SKILL_PATCH_NOTES.md) first. It defines the scope boundary.
- Read [INTEGRATION.md](INTEGRATION.md) for the repo layout and patch shape.
- Read [references/aac-skill-patch.md](references/aac-skill-patch.md) when you are editing the original AAC `skill.md`.
- Read [API_INGESTION.md](API_INGESTION.md) only when you need source-specific manifest instructions.

## Goal

Add a reusable image-memory layer to AAC with this sequence:

1. search AAC-supported image APIs
2. select images for the run
3. normalize those selections into a manifest
4. import the selected images into repo-local storage
5. after the import batch is complete, preprocess that batch into token-efficient readable cache data
6. query the cache before any visual-model call
7. use a visual model only when the cache is missing or insufficient

## Non-Negotiable Scope

This skill only patches the source-image ingestion and image-memory lookup path.

Do not change:

- AAC aesthetic or artistic goals
- inspiration-study requirements
- composition guidance
- dithering guidance
- review loop standards
- scale or plot-selection guidance
- edge-awareness behavior
- submission flow or on-chain logic
- collaboration philosophy

If a requested change touches those areas, stop and say it is out of scope for this skill.

## Default Implementation Pattern

1. Inspect the AAC checkout and find the files that govern source-image search, download, and image-analysis instructions.
2. Add this repository to the AAC checkout, preferably as `image_memory_workflow/`.
3. Keep raw imported images in AAC repo storage, typically under `workspace/sources/` and `workspace/source_metadata/`.
4. Build cache output into a repo-local directory such as `workspace/image_memory/`.
5. Patch AAC instructions minimally so the workflow becomes:

   - search AAC-supported source APIs as before
   - normalize selected results into a manifest
   - import selected images into repo storage
   - build the image-memory cache after that import batch completes
   - query the cache before any visual-model call
   - fall back to vision only when the cache is missing or insufficient

6. Prefer additive insertions over rewrites. Keep the AAC prose intact unless a small local edit is required.

## What To Patch In AAC

Patch only the source-image workflow.

- In the existing "Find source images" step, add manifest normalization and repo-local import guidance.
- Add an image-memory note or subsection that says imported images should be preprocessed into readable cache data after import.
- Add the query-first rule before visual analysis of imported images.
- Add setup/resource references for this repo's scripts only when needed to make the workflow executable.
- Replace the old direct image-ingestion wording with the cache-first wording from [references/aac-skill-patch.md](references/aac-skill-patch.md).
- Apply the patch to the specific AAC sections listed in that reference and leave all other sections alone.

Do not reorganize the rest of the AAC skill unless a tiny local edit is needed to insert the new step.

## Supported Source APIs

This skill covers the same source list AAC already names:

- Wikimedia Commons
- Metropolitan Museum of Art
- Art Institute of Chicago
- Rijksmuseum
- Harvard Art Museums
- Library of Congress
- Unsplash
- Pexels
- NASA Image and Video Library
- Smithsonian Open Access

Use [API_INGESTION.md](API_INGESTION.md) for the per-source normalization details.

## Working Rules

- Keep the diff narrow and reversible.
- Prefer copying this repo into AAC rather than rewriting its scripts by hand.
- Prefer a single new subsection and a few bullets over rewriting AAC sections wholesale.
- Keep the workflow additive: raw images remain the source of truth, and the cache is a helper layer.
- Never describe this as a redesign of AAC. It is a token-efficiency layer only.
- When the original AAC `skill.md` is provided, patch the named sections directly rather than paraphrasing the intent loosely.

## Validation

After patching AAC:

1. Verify the diff only touches image-ingestion, import, cache-build, and cache-query steps.
2. Verify that composition, dithering, plotting, and submission instructions remain unchanged.
3. Verify that the old direct ingestion flow has been replaced in the targeted AAC sections by the new import-plus-cache workflow.
4. Run at least one smoke test when possible:

```bash
python3 image_memory_workflow/scripts/build_image_memory.py --help
python3 image_memory_workflow/scripts/query_image_memory.py --help
```

5. If the AAC checkout already has imported source images, test a real build/query path too.

## Output Style

When using this skill for a real AAC patch:

- summarize the narrow scope up front
- call out exactly which AAC files were changed
- mention explicitly that no creative or blockchain behavior was altered
