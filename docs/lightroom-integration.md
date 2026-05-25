# Lightroom Integration

PhotoSage can process photos exported from Lightroom Classic.

It does not edit Lightroom catalog databases.

## Recommended Workflow

Use an export folder.

1. Open Lightroom Classic.
2. Export selected photos to a separate folder.
3. Run a PhotoSage preview on that folder.
4. Review the proposed filenames.
5. Apply only when the preview is correct.
6. Keep the manifest in case you need undo.

## Preview First

```powershell
photosage lightroom-process --input ./LightroomExports --preview
```

Preview mode does not rename files.

## Apply Renames

```powershell
photosage lightroom-process --input ./LightroomExports --apply
```

Apply mode writes a manifest before changing files.

## Organize Folders

Use `--organize` to sort files into year, month, and category folders.

```powershell
photosage lightroom-process --input ./LightroomExports --preview --organize
```

Example output structure:

```text
LightroomExports/
  2026/
    2026-05/
      Construction/
```

## Presets

Use a preset when a folder has a clear purpose.

```powershell
photosage lightroom-process --input ./LightroomExports --preview --preset astronomy
```

Available presets:

- `documentary`
- `travel`
- `astronomy`
- `wildlife`
- `construction`
- `family`
- `minimalist`
- `metadata-only`
- `ai-heavy`

## XMP Sidecars

PhotoSage reads `.xmp` sidecars when they exist.

Example before rename:

```text
photo.jpg
photo.xmp
```

Example after rename:

```text
2026-05-25_dover-tn_container-home_001.jpg
2026-05-25_dover-tn_container-home_001.xmp
```

PhotoSage keeps the sidecar name matched to the image name.

It can read:

- title
- caption
- keywords
- rating
- color label
- creator
- copyright
- GPS values
- Lightroom collection data when available

If no sidecar exists, PhotoSage tries embedded XMP metadata.

## Metadata Scoring

Lightroom metadata can reduce the need for AI.

Extra scoring:

- keywords: `+20`
- title: `+15`
- caption: `+10`
- rating: `+5`

## Catalog Safety

Do not point PhotoSage at an active Lightroom catalog folder.

PhotoSage blocks folders that look like catalog folders, including:

- `.lrcat` files
- `.lrdata` folders
- Lightroom preview folders

Override only if you understand the risk:

```powershell
photosage lightroom-process --input ./CatalogFolder --apply --force-catalog-modify
```

PhotoSage still does not edit `.lrcat` databases. The risk is breaking Lightroom file references by renaming tracked files.

## Astrophotography

Use the astronomy preset:

```powershell
photosage lightroom-process --input ./AstroExports --preview --preset astronomy --organize
```

Example names:

```text
2026-05-25_orion-nebula_seestar-s50_001.jpg
2026-05-25_solar-prominence_h-alpha_001.jpg
```

## Undo

Use the manifest created during apply mode:

```powershell
photosage undo --manifest ./manifests/rename_manifest.json --dry-run
photosage undo --manifest ./manifests/rename_manifest.json --force
```

Undo restores renamed images and matching sidecars when possible.

## Troubleshooting

If PhotoSage blocks a folder, export from Lightroom to a separate folder and process that.

If a sidecar was not renamed, check whether the `.xmp` file existed before apply mode.

If too many files require AI, add Lightroom keywords, titles, captions, or ratings before export.

If categories look wrong, use stronger Lightroom keywords or a preset.
