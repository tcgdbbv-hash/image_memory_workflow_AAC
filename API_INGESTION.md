# API Ingestion Guide

This guide covers every image source listed in the original AAC skill and shows how to turn those images into reusable repo memory.

The pattern is the same for every source:

1. search the source API
2. normalize the chosen results into a manifest
3. download the images with `download_image_manifest.py`
4. build memory with `build_image_memory.py`

## Universal Workflow

### 1. Search

Use the source API to find images that fit your composition.

### 2. Normalize into a manifest

Write one manifest row per image:

```json
{
  "id": "source_unique_id",
  "url": "https://example.com/image.jpg",
  "filename": "source_unique_id.jpg",
  "source_api": "source_name",
  "query": "search phrase",
  "title": "Human-readable title",
  "creator": "Artist or photographer",
  "license": "license string",
  "source_url": "human-facing page URL",
  "metadata_url": "API metadata URL"
}
```

### 3. Download

```bash
python3 image_memory_workflow/scripts/download_image_manifest.py \
  path/to/manifest.jsonl \
  --output-dir workspace/sources/imported \
  --metadata-dir workspace/source_metadata
```

### 4. Build memory

```bash
python3 image_memory_workflow/scripts/build_image_memory.py \
  --source-dir workspace/sources/imported \
  --output-dir workspace/image_memory/imported
```

## Wikimedia Commons

Search:

```bash
curl -s "https://commons.wikimedia.org/w/api.php?action=query&list=search&srsearch=YOUR_QUERY&srnamespace=6&srlimit=10&format=json" \
  -H "User-Agent: aac-agent-kit/2.0"
```

Resolve file to image URL:

```bash
curl -s "https://commons.wikimedia.org/w/api.php?action=query&titles=FILE_TITLE&prop=imageinfo&iiprop=url&iiurlwidth=1200&format=json" \
  -H "User-Agent: aac-agent-kit/2.0"
```

Normalize each chosen result:

- `id`: Wikimedia page ID or file title slug
- `url`: `query.pages.*.imageinfo[0].thumburl` or `url`
- `source_api`: `wikimedia`
- `source_url`: Commons file page URL
- `metadata_url`: the API URL used above

Notes:

- always send a `User-Agent`
- if you want a stable cheaper cache input, prefer `thumburl` at a fixed width

## Metropolitan Museum of Art Open Access

Search:

```bash
curl -s "https://collectionapi.metmuseum.org/public/collection/v1/search?q=YOUR_QUERY&hasImages=true"
```

Resolve an object:

```bash
curl -s "https://collectionapi.metmuseum.org/public/collection/v1/objects/OBJECT_ID"
```

Normalize each chosen result:

- only use objects where `isPublicDomain` is `true`
- `id`: `met_OBJECT_ID`
- `url`: `primaryImageSmall` for cache-first workflows, `primaryImage` if you need full size
- `source_api`: `met`
- `source_url`: `objectURL`
- `metadata_url`: object endpoint

## Art Institute of Chicago

Search:

```bash
curl -s "https://api.artic.edu/api/v1/artworks/search?q=YOUR_QUERY&fields=id,title,image_id,artist_display&limit=10"
```

Build the image URL:

```text
https://www.artic.edu/iiif/2/IMAGE_ID/full/1200,/0/default.jpg
```

Normalize each chosen result:

- `id`: `aic_ID`
- `url`: the IIIF URL above
- `source_api`: `aic`
- `metadata_url`: artwork search or artwork detail endpoint
- `creator`: `artist_display`

## Rijksmuseum

Search:

```bash
curl -s "https://www.rijksmuseum.nl/api/en/collection?q=YOUR_QUERY&key=YOUR_KEY"
```

Normalize each chosen result:

- `id`: `rijksmuseum_objectNumber`
- `url`: `webImage.url`
- `source_api`: `rijksmuseum`
- `source_url`: object page URL when available
- `metadata_url`: collection API URL

Notes:

- requires an API key
- store the key outside the repo and inject it at runtime

## Harvard Art Museums

Search:

```bash
curl -s "https://api.harvardartmuseums.org/object?q=YOUR_QUERY&apikey=YOUR_KEY&size=10"
```

Normalize each chosen result:

- `id`: `harvard_ID`
- `url`: image URL from the primary image field
- `source_api`: `harvard`
- `metadata_url`: object endpoint

Notes:

- requires an API key
- save both the human title and artist when available

## Library of Congress

Search:

```bash
curl -s "https://www.loc.gov/search/?q=YOUR_QUERY&fo=json"
```

Or the pictures endpoint:

```bash
curl -s "https://www.loc.gov/pictures/search/?q=YOUR_QUERY&fo=json&c=10"
```

Normalize each chosen result:

- `id`: `loc_ID` or slug
- `url`: `image.full` when available, otherwise `image.thumb`
- `source_api`: `loc`
- `source_url`: item page URL
- `metadata_url`: search response or item JSON URL

## Unsplash

Search:

```bash
curl -s "https://api.unsplash.com/search/photos?query=YOUR_QUERY" \
  -H "Authorization: Client-ID YOUR_ACCESS_KEY"
```

Normalize each chosen result:

- `id`: `unsplash_ID`
- `url`: `urls.regular` or `urls.full`
- `source_api`: `unsplash`
- `creator`: photographer name
- `source_url`: HTML page URL
- `headers.Authorization`: `Client-ID YOUR_ACCESS_KEY`

Notes:

- requires an API key
- keep API credentials out of the repo

## Pexels

Search:

```bash
curl -s "https://api.pexels.com/v1/search?query=YOUR_QUERY" \
  -H "Authorization: YOUR_API_KEY"
```

Normalize each chosen result:

- `id`: `pexels_ID`
- `url`: `src.large`, `src.large2x`, or `src.original`
- `source_api`: `pexels`
- `creator`: photographer name
- `headers.Authorization`: API key

Notes:

- requires an API key

## NASA Image and Video Library

Search:

```bash
curl -s "https://images-api.nasa.gov/search?q=YOUR_QUERY&media_type=image"
```

Normalize each chosen result:

- `id`: NASA item `nasa_id`
- `url`: `collection.items[].links[0].href`
- `source_api`: `nasa`
- `title`: from `collection.items[].data[0].title`
- `source_url`: NASA item page when available
- `metadata_url`: search response or asset endpoint

Notes:

- NASA often returns many similarly named image variants
- decide whether you want preview-sized or largest-available assets before download

## Smithsonian Open Access

Search:

```bash
curl -s "https://api.si.edu/openaccess/api/v1.0/search?q=YOUR_QUERY&api_key=YOUR_KEY"
```

Normalize each chosen result:

- `id`: Smithsonian record ID
- `url`: preferred media content URL
- `source_api`: `smithsonian`
- `metadata_url`: record endpoint or search URL

Notes:

- requires an API key
- store the object title and museum/unit when possible

## Processing Every Image, Not Just One

To build memory for **all** inspiration images you choose from an API search:

1. normalize each chosen result into its own manifest row
2. run the manifest downloader once on the whole manifest
3. after the import batch is complete, build memory on the entire downloaded folder

For a multi-source AAC run, the same rule applies:

1. collect the chosen images from Wikimedia, Met, NASA, Library of Congress, or any other supported AAC source
2. import those selected images into repo storage
3. then build the token-efficient readable cache across that imported set
4. only after that let later agent steps query the cache or fall back to a visual model

That gives you one reusable cache for the whole batch.

Example:

```bash
python3 image_memory_workflow/scripts/download_image_manifest.py \
  manifests/met_faces.jsonl \
  --output-dir workspace/sources/met_faces \
  --metadata-dir workspace/source_metadata/met_faces

python3 image_memory_workflow/scripts/build_image_memory.py \
  --source-dir workspace/sources/met_faces \
  --output-dir workspace/image_memory/met_faces
```

## Recommended Storage Convention

For large projects, store by source or theme:

```text
workspace/
  sources/
    wikimedia_faces/
    met_busts/
    nasa_clouds/
  image_memory/
    wikimedia_faces/
    met_busts/
    nasa_clouds/
```

That keeps caches small and makes later retrieval faster and easier to reason about.

## Suggested Agent Rule

When using any source API from the AAC skill:

1. normalize chosen images into a manifest
2. download them into repo storage
3. build image memory immediately
4. query memory first on later runs
5. only call a visual model if the cache is missing or insufficient
