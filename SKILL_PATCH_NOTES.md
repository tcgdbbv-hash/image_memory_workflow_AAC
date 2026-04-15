# AAC Skill Patch Notes

These notes define the intended scope of the AAC `skill.md` patch that will consume this repository.

## Goal

Add a lightweight image-memory layer to AAC so repeated inspiration images do not need repeated visual-model analysis.

## Allowed Changes

The AAC skill patch should only add or clarify behavior in this part of the workflow:

1. search or collect inspiration images
2. normalize results into a manifest
3. download images into repo storage
4. after the selected images from the supported APIs have been imported, preprocess that imported batch into cached readable data
5. query that cache before any visual-model call
6. fall back to a visual model only when the cache is missing or insufficient

## Disallowed Changes

The patch should not change AAC's existing creative or blockchain behavior.

Do not alter:

- aesthetic goals
- composition guidance
- dithering guidance
- review loop standards
- plot selection or scale guidance
- on-chain submission flow
- ownership/cooldown logic
- collaboration philosophy

## Recommended Insertion Point

Patch only the "find source images" and "look at the images" portion of the skill.

The safest shape is:

- before: image search -> download -> visual analysis
- after: image search -> import selected API images -> build/query image memory -> visual analysis only if needed

## One-Line Principle

This repository should be integrated as a **token-efficiency layer**, not as a redesign of AAC.
