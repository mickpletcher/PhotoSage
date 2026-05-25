# Lightroom Integration

PhotoSage supports Lightroom export workflows without touching Lightroom catalog databases.

The first implementation works on exported folders. Export photos from Lightroom Classic to a separate directory, then let PhotoSage read EXIF, embedded XMP, and `.xmp` sidecars before generating safe filenames and manifests.

## Supported Workflows

Preview exported photos:

```powershell
photosage lightroom-process --input ./LightroomExports --preview
```

Apply safe renames:

```powershell
photosage lightroom-process --input ./LightroomExports --apply
```

Organize into year, month, and category folders:

```powershell
photosage lightroom-process --input ./LightroomExports --preview --organize
```

Use a Lightroom preset:

```powershell
photosage lightroom-process --input ./LightroomExports --preview --preset astronomy
```

## Export Recommendation

Use an export first workflow.

1. Export selected photos from Lightroom Classic to a working folder.
2. Enable metadata export and sidecars when needed.
3. Run `photosage lightroom-process --preview`.
4. Review the manifest.
5. Run with `--apply` only when the preview is correct.
6. Import the renamed export folder elsewhere if needed.

Do not run PhotoSage directly against an active Lightroom catalog folder unless you explicitly accept the catalog reference risk.

## XMP Sidecars

PhotoSage reads `.xmp` sidecars with the same stem as the image:

```text
photo.jpg
photo.xmp
```

When the image is renamed, the sidecar is renamed to match:

```text
2026-05-25_dover-tn_container-home_001.jpg
2026-05-25_dover-tn_container-home_001.xmp
```

PhotoSage extracts:

- title
- caption
- keywords
- rating
- color label
- creator
- copyright
- GPS latitude and longitude
- Lightroom collection or hierarchical subject values where available

If no sidecar exists, PhotoSage attempts to read embedded XMP from the image file.

## Metadata Scoring

Lightroom metadata increases the metadata score before AI fallback decisions:

- Lightroom keywords: `+20`
- Lightroom title: `+15`
- Lightroom caption: `+10`
- Lightroom rating: `+5`

This keeps the system metadata first and reduces unnecessary AI calls.

## Folder Organization

Organization is optional. When enabled, PhotoSage writes files under:

```text
Photos/
  2026/
    2026-05/
      Construction/
```

Categories come from metadata first:

1. Lightroom keywords and collections
2. Existing EXIF or embedded tags
3. Optional normalized AI classification data

Common categories include travel, landscape, astrophotography, wildlife, architecture, construction, hiking, portraits, pets, vehicles, screenshots, and documents.

## Catalog Safety

PhotoSage blocks probable Lightroom catalog locations by default.

Blocked signals include:

- `.lrcat` catalog files in the target tree
- `.lrdata` support folders
- Lightroom previews folders

Override only when you understand the risk:

```powershell
photosage lightroom-process --input ./CatalogFolder --apply --force-catalog-modify
```

PhotoSage still never modifies `.lrcat` files. The risk is breaking Lightroom file references by renaming files that Lightroom tracks.

## Presets

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

Presets define metadata thresholds, filename format, organization defaults, and AI usage policy.

## Astrophotography

Use the astronomy preset for telescope, lunar, solar, stacked, and deep sky image exports:

```powershell
photosage lightroom-process --input ./AstroExports --preview --preset astronomy --organize
```

Example filenames:

```text
2026-05-25_orion-nebula_seestar-s50_001.jpg
2026-05-25_solar-prominence_h-alpha_001.jpg
```

The current implementation prioritizes capture date, Lightroom title, keywords, camera or telescope metadata, and session grouping through folder organization.

## Manifests

Lightroom mode extends the normal manifest with:

- `lightroom_mode`
- `xmp_detected`
- `xmp_path`
- `new_xmp_path`
- `organization_applied`
- `category`
- `sidecar_status`

Manifests are still written before apply mode changes files.

## Troubleshooting

If PhotoSage blocks a folder, export from Lightroom to a separate directory and process that folder instead.

If a sidecar is not renamed, check whether the source `.xmp` exists and whether the destination `.xmp` already existed.

If AI is marked as required, add Lightroom keywords, title, caption, or rating to improve metadata confidence.

If category assignment is wrong, use stronger Lightroom keywords or a preset.
