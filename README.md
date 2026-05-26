# PhotoSage

PhotoSage is a safe photo renaming tool.

It reads photo metadata first. When metadata is weak, the CLI can call the configured vision provider for structured image understanding. The model never renames files directly.

The main goal is simple:

```text
IMG_4588.JPG
```

becomes something useful like:

```text
2026-05-25_dover-tn_shipping-container_deck-project_001.jpg
```

## What It Does

- Scans photo folders.
- Reads EXIF, GPS, camera, date, size, and tag metadata.
- Scores metadata quality.
- Builds clean filenames.
- Shows a preview before changing anything.
- Renames only when `--apply` is used.
- Writes a manifest before renaming.
- Supports undo from the manifest.
- Includes local Ollama provider support.
- Supports Lightroom export folders and XMP sidecars.
- Includes an early PySide6 desktop GUI.
- Watches incoming folders with an approval queue.
- Finds likely duplicate photos without deleting anything.
- Supports folder organization policies.
- Uses a local geocode cache for consistent GPS names.
- Supports astrophotography naming with FITS metadata and capture-night grouping.

## Safety Rules

PhotoSage is built to avoid data loss.

- No files are renamed unless you pass `--apply`.
- Preview mode does not change files.
- Existing files are never overwritten.
- A manifest is written before renames happen.
- Undo uses the manifest to restore names.
- Local-only mode blocks cloud AI providers.
- Lightroom catalog databases are never modified.

## Supported Files

PhotoSage scans:

- `jpg`
- `jpeg`
- `png`
- `heic`
- `webp`
- `tiff`
- `fits`
- `fit`

Other files are skipped.

## Install

From the repo root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pip install -e .
```

Check that the CLI works:

```powershell
photosage --help
```

## First Safe Run

Start with preview.

```powershell
photosage preview --input ./photos
```

This shows proposed filenames. It does not rename anything.

When the preview looks right:

```powershell
photosage rename --input ./photos --apply
```

If something goes wrong, undo the run:

```powershell
photosage undo --manifest ./manifests/rename_manifest.json
```

Use the actual manifest file created in your `manifests/` folder.

## Common Commands

Scan metadata scores:

```powershell
photosage scan --input ./photos
```

Preview renames:

```powershell
photosage preview --input ./photos
```

Apply renames:

```powershell
photosage rename --input ./photos --apply
```

Preview undo:

```powershell
photosage undo --manifest ./manifests/rename_manifest.json --dry-run
```

Validate a manifest before undo:

```powershell
photosage manifest validate --manifest ./manifests/rename_manifest.json
```

Find likely duplicates:

```powershell
photosage duplicates --input ./photos --output-json ./duplicates.json
```

Build a watch folder approval queue:

```powershell
photosage watch --input ./IncomingPhotos
```

Apply a watch folder run only after approval:

```powershell
photosage watch --input ./IncomingPhotos --apply
```

Save a GPS location alias:

```powershell
photosage geocode set --lat 36.50000 --lon -87.84000 --location dover-tn
```

Preview astrophotography naming:

```powershell
photosage astro --input ./AstroExports --profile deep-sky
```

Undo for real:

```powershell
photosage undo --manifest ./manifests/rename_manifest.json --force
```

Export command output to JSON:

```powershell
photosage preview --input ./photos --output-json ./preview.json
```

## Configuration

Edit [config/settings.yaml](config/settings.yaml).

Important settings:

```yaml
vision_provider: anthropic
metadata_threshold: 70
dry_run_default: true
local_only: false
filename_format: "{date}_{location}_{subject}_{context}_{counter}"
watch_stable_seconds: 5.0
duplicate_hash_distance: 5
folder_policy: date-first
geocode_cache_file: .photosage-cache/geocode_cache.json
```

`metadata_threshold` controls when a file is marked as needing AI help.

- `70` is the default.
- Higher values mark more files as AI-needed.
- Lower values rely on metadata more often.

## AI Providers

Provider architecture exists for:

- Anthropic
- OpenAI
- Gemini
- Ollama
- LM Studio

Preview and rename can call the selected provider when metadata is below the configured threshold or `--force-ai` is used.

The provider returns structured labels. PhotoSage still builds the filename locally.

### Anthropic Cloud Example

Create a local `.env` file:

```powershell
Copy-Item .env.example .env
```

Edit `.env`:

```text
ANTHROPIC_API_KEY=your_api_key_here
```

Set the provider in [config/settings.yaml](config/settings.yaml):

```yaml
vision_provider: anthropic
local_only: false

anthropic:
  model: claude-sonnet-4
```

Preview with live provider analysis when needed:

```powershell
photosage preview --input ./photos
```

Force provider analysis for every supported image:

```powershell
photosage preview --input ./photos --force-ai
```

Apply only after preview looks right:

```powershell
photosage rename --input ./photos --apply
```

Ollama and LM Studio are the local provider paths. They keep image data on your machine when used by provider workflows.

Check provider status:

```powershell
photosage providers
```

Local-only mode is shown in command summaries. When it is enabled, cloud providers are blocked from fallback.

Use Ollama only:

```powershell
photosage scan --input ./photos --provider ollama --local-only
```

Basic Ollama setup:

```powershell
ollama pull llava
ollama pull llava:13b
ollama pull qwen2.5vl
```

Recommended Ollama config:

```yaml
vision_provider: ollama
local_only: true

ollama:
  endpoint: http://localhost:11434
  model: llava:13b
  timeout_seconds: 180
```

### LM Studio Local Setup

LM Studio uses a local OpenAI-compatible server. No API key is needed.

In LM Studio:

1. Download a vision-capable model.
2. Load the model.
3. Start the local server.
4. Confirm the server exposes `/v1/models`.

Default endpoint:

```text
http://localhost:1234/v1
```

Example config:

```yaml
vision_provider: lmstudio
local_only: true

fallback_order:
  - lmstudio
  - ollama

lmstudio:
  endpoint: http://localhost:1234/v1
  model: qwen2.5-vl
  timeout_seconds: 180
  temperature: 0.1
  max_dimension: 1600
  jpeg_quality: 90
```

Use LM Studio only:

```powershell
photosage preview --input ./photos --provider lmstudio --local-only
```

The selected LM Studio model must be visible from `/v1/models`.

## Lightroom Workflow

PhotoSage works with Lightroom export folders.

Best workflow:

1. Export photos from Lightroom Classic to a separate folder.
2. Run PhotoSage on that exported folder.
3. Review the preview.
4. Apply only when the preview is correct.

Preview:

```powershell
photosage lightroom-process --input ./LightroomExports --preview
```

Apply:

```powershell
photosage lightroom-process --input ./LightroomExports --apply
```

Organize into folders:

```powershell
photosage lightroom-process --input ./LightroomExports --preview --organize
```

PhotoSage keeps matching XMP sidecars together:

```text
photo.jpg
photo.xmp
```

renames to:

```text
2026-05-25_dover-tn_container-home_001.jpg
2026-05-25_dover-tn_container-home_001.xmp
```

More detail: [docs/lightroom-integration.md](docs/lightroom-integration.md).

## Desktop GUI

Launch the GUI:

```powershell
photosage-gui
```

The GUI uses the same backend as the CLI.

Use it to:

- Pick a folder.
- Scan photos.
- Preview names.
- Apply safe renames.
- Undo from manifests.
- Change provider settings.

The GUI is functional but still early.

The GUI now includes thumbnail caching, faster large table loading, saved profile helpers, and recent manifest tracking for faster undo workflows.

## Filename Format

Default format:

```text
YYYY-MM-DD_location_subject_context_###.ext
```

Rules:

- Use EXIF date first.
- Fall back to file modified date.
- Keep the original extension.
- Lowercase names.
- Replace spaces with hyphens.
- Remove unsafe characters.
- Add counters to prevent overwrites.

## Watch Folders

Watch mode is for incoming folders, such as camera imports or synced folders.

Default behavior is safe:

- It only includes files that are stable.
- It writes an approval queue manifest.
- It does not rename unless `--apply` is passed.
- It groups each run into a normal PhotoSage manifest.

```powershell
photosage watch --input ./IncomingPhotos
photosage watch --input ./IncomingPhotos --apply
```

## Duplicate Detection

PhotoSage can find likely duplicate images with local perceptual hashing.

It does not delete anything.

```powershell
photosage duplicates --input ./photos --output-json ./duplicates.json
```

Duplicate group data is also added to rename manifests when matches are found.

## Folder Organization Policies

Organization policies choose folders when organization mode is used.

Supported policies:

- `date-first`
- `location-first`
- `project-first`
- `custom`

Example config:

```yaml
folder_policy: project-first
folder_keyword_map:
  construction: container-home
  astronomy: astrophotography
```

## Geocode Cache

The geocode cache stores local GPS to location names.

It avoids repeated lookups later and keeps filenames consistent.

```powershell
photosage geocode set --lat 36.50000 --lon -87.84000 --location dover-tn
photosage geocode list
```

If PhotoSage sees matching GPS coordinates, it uses the cached location in filenames.

## Astrophotography

Astro mode is for telescope sessions, stacked images, lunar, solar, planetary, and deep sky work.

It can read:

- filenames
- normal photo metadata
- direct `.fits` and `.fit` files
- matching FITS sidecars such as `moon.jpg` and `moon.fits`

Preview:

```powershell
photosage astro --input ./AstroExports --profile lunar
```

Apply:

```powershell
photosage astro --input ./AstroExports --profile lunar --apply
```

Profiles:

- `lunar`
- `solar`
- `planetary`
- `deep-sky`

Astro filename tokens:

- `{capture_night}`
- `{astro_target}`
- `{telescope}`
- `{filter}`
- `{exposure}`
- `{session}`
- `{astro_profile}`

Example:

```text
2026-05-25_orion-nebula_seestar-s50_h-alpha_10_001.jpg
```

Capture night groups images after midnight with the previous evening, which matches normal astronomy session handling.

## Screenshot And Document Mode

PhotoSage can label common non-photo images from local metadata and filenames.

It can detect:

- screenshots
- receipts
- invoices
- statements
- bills
- forms
- scanned documents
- notes
- email screenshots
- spreadsheet or presentation images

For screenshots, PhotoSage tries to identify the source app when it is obvious, such as Chrome, Edge, Outlook, Teams, Excel, Word, VS Code, Slack, or Lightroom.

For documents, PhotoSage adds document labels such as `receipt`, `invoice`, or `statement`.

These labels are added to metadata and can affect generated filenames:

```text
Screenshot 2026-05-25 Chrome.png
```

can become:

```text
2026-05-25_digital_screenshot_chrome_001.png
```

Extra filename tokens are available:

- `{media_type}`
- `{document_type}`
- `{app}`
- `{ocr_summary}`

`{ocr_summary}` uses embedded OCR-like metadata only when it already exists. PhotoSage does not run OCR yet.

## Manifests And Undo

Every preview or apply run writes a manifest in:

```text
manifests/
```

Undo reports are written in:

```text
rollback_reports/
```

Keep these files if you may need to undo a rename.

Validate a manifest:

```powershell
photosage manifest validate --manifest ./manifests/rename_manifest.json
```

Add hashes for existing referenced files:

```powershell
photosage manifest validate --manifest ./manifests/rename_manifest.json --hashes
```

The validator checks:

- missing files
- unsafe paths
- undo collisions
- sidecar mismatches
- optional SHA256 hashes

## Project Docs

- [assessment.md](assessment.md): Current project state for future agents.
- [CHANGELOG.md](CHANGELOG.md): What changed.
- [completed-upgrades.md](completed-upgrades.md): Finished roadmap work.
- [docs/lightroom-integration.md](docs/lightroom-integration.md): Lightroom workflow.
- [specs/README.md](specs/README.md): Spec workflow for larger changes.
- `future-upgrades.md`: Local-only roadmap. It is intentionally ignored by git.

## Run Tests

```powershell
python -m pytest
```

CI also runs:

- pytest
- basic Ruff lint checks
- Markdown link checks
- spec folder checks

## Privacy Notes

- Metadata is used before AI.
- Files are marked as AI-needed when metadata is weak or `--force-ai` is passed.
- `local_only: true` blocks cloud providers.
- Providers return structured classification only.
- Providers do not rename or move files.
- API keys belong in `.env`, not in source control.
