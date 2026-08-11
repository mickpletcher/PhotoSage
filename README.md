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
- Includes a PySide6 desktop GUI with reviewed-manifest apply.
- Watches incoming folders with an approval queue.
- Finds likely duplicate photos without deleting anything.
- Supports folder organization policies.
- Uses a local geocode cache for consistent GPS names.
- Supports astrophotography naming with FITS metadata and capture-night grouping.
- Supports common video formats with ffprobe metadata and optional ffmpeg keyframes.
- Includes approve, reject, and filename-edit review states.
- Includes private local search, offline timelines, and an offline GPS plot.
- Benchmarks providers and supports generic local OpenAI-compatible vision servers.

## Safety Rules

PhotoSage is built to avoid data loss.

- No files are renamed unless you pass `--apply`.
- Normal apply uses the exact reviewed preview manifest.
- Preview mode does not change files.
- Existing files are never overwritten.
- Atomic, checksummed manifests journal every rename state.
- Undo recovers completed and interrupted rename operations.
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
- `mp4`
- `mov`
- `m4v`
- `avi`
- `mkv`
- `webm`

Other files are skipped.

## Install

From the repo root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.lock
python -m pip install --no-deps -e .
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

The preview summary prints the manifest path. Inspect and edit the review queue when needed:

```powershell
photosage review --manifest ./manifests/rename_manifest_YYYYMMDD_HHMMSS.json
```

Low-confidence and duplicate entries remain blocked until approved or edited. Apply the exact manifest:

```powershell
photosage rename --manifest ./manifests/rename_manifest_YYYYMMDD_HHMMSS.json --apply
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

Apply a reviewed preview manifest:

```powershell
photosage rename --manifest ./manifests/rename_manifest_YYYYMMDD_HHMMSS.json --apply
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

Build a duplicate review manifest and CSV:

```powershell
photosage duplicates --input ./photos --output-csv ./duplicates.csv --review-folder ./photos/DuplicateReview
```

Inspect or resume an interrupted run:

```powershell
photosage recover --manifest ./manifests/rename_manifest.json
photosage recover --manifest ./manifests/rename_manifest.json --resume
```

Validate configuration and optional tools:

```powershell
photosage config validate
photosage doctor
```

Build a watch folder approval queue:

```powershell
photosage watch --input ./IncomingPhotos
```

Apply the exact watch queue only after approval:

```powershell
photosage watch --manifest ./manifests/rename_manifest_YYYYMMDD_HHMMSS.json --apply
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

Inside the repository, edit [config/settings.yaml](config/settings.yaml). Installed use defaults to `%LOCALAPPDATA%\PhotoSage\settings.yaml` on Windows. A missing config file uses privacy-safe defaults.

Important settings:

```yaml
vision_provider: ollama
metadata_threshold: 70
dry_run_default: true
local_only: true
filename_format: "{date}_{location}_{subject}_{context}_{counter}"
watch_stable_seconds: 5.0
duplicate_hash_distance: 5
detect_duplicates_during_rename: false
folder_policy: date-first
geocode_cache_file: .photosage-cache/geocode_cache.json
review_confidence_threshold: 0.7
require_manual_review_for_ai: true
search_database: .photosage-cache/search.sqlite3
embedding_backend: hash
embedding_model: nomic-embed-text
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
- Kimi through the Moonshot AI API
- Ollama
- LM Studio
- Generic local OpenAI-compatible servers such as llama.cpp, vLLM, LocalAI, and Jan

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
  include_sensitive_metadata: false
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
photosage rename --manifest ./manifests/rename_manifest_YYYYMMDD_HHMMSS.json --apply
```

Cloud providers receive the image and a strict technical metadata allowlist. Absolute paths, filenames, GPS coordinates, titles, descriptions, OCR text, and keywords are excluded by default. Set `include_sensitive_metadata: true` only when you explicitly want that provider to receive the extra metadata.

### Kimi Cloud Example

Create an API key in the [Kimi API Platform](https://platform.kimi.ai/docs/overview). Store it in your ignored `.env` file:

```text
MOONSHOT_API_KEY=your_api_key_here
```

Configure Kimi K3:

```yaml
vision_provider: kimi
local_only: false

kimi:
  base_url: https://api.moonshot.ai/v1
  model: kimi-k3
  reasoning_effort: low
  max_completion_tokens: 1200
  timeout_seconds: 180
  include_sensitive_metadata: false
```

Run `photosage providers` to confirm the key and OpenAI-compatible SDK are available without making a billable request. Then use `photosage preview --input ./photos --force-ai` to classify through Kimi. Kimi is a cloud provider, so the image is uploaded to Moonshot AI. `local_only: true` blocks it.

`kimi-k2.5` and `kimi-k2.6` are also supported. Set `thinking: disabled` under `kimi` when using either model for lower-latency photo classification. Kimi K3 always uses reasoning; control it with `reasoning_effort`.

Ollama, LM Studio, and generic OpenAI-compatible endpoints are the local provider paths.

Local provider names are not trusted by themselves. Loopback endpoints are accepted by default. LAN endpoints require an exact `endpoint_allowlist`, HTTPS, and explicit configuration. Public addresses are rejected for local providers. Redirects are disabled.

```yaml
openai_compatible_local:
  endpoint: https://ai-server.home.arpa/v1
  model: qwen-vl
  endpoint_allowlist:
    - ai-server.home.arpa
  allow_insecure_lan_endpoint: false
```

Benchmark providers with an explicit sample limit. Cloud calls require `--allow-cloud`:

```powershell
photosage benchmark providers --input ./sample-photos --provider ollama --provider lmstudio --limit 10 --output-json ./benchmark.json --output-markdown ./benchmark.md
```

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
photosage lightroom-process --manifest ./manifests/rename_manifest_YYYYMMDD_HHMMSS.json --apply
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
- Approve, reject, or edit proposed filenames.
- Open offline timeline and GPS views.

The GUI applies the exact reviewed manifest. It blocks apply if the selected folder changed and rechecks source SHA256, size, and modification time before every rename.

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
- Apply requires the reviewed queue manifest and confirmation.
- It groups each run into a normal PhotoSage manifest.

```powershell
photosage watch --input ./IncomingPhotos
photosage watch --manifest ./manifests/rename_manifest_YYYYMMDD_HHMMSS.json --apply
```

## Duplicate Detection

PhotoSage can find likely duplicate images with local perceptual hashing.

It does not delete anything.

```powershell
photosage duplicates --input ./photos --output-json ./duplicates.json
```

Normal rename planning only performs duplicate analysis when `detect_duplicates_during_rename` is enabled. The dedicated duplicate command always performs the analysis. It recommends a keeper but never deletes a file. Optional review-folder moves use the same checksummed manifest workflow as renames.

## Video Support

PhotoSage reads MP4, MOV, M4V, AVI, MKV, and WebM metadata. When `ffprobe` is installed it captures duration, codec, dimensions, frame rate, and embedded creation time. `{duration}` and `{codec}` are available as filename tokens.

When video AI analysis is requested, PhotoSage uses `ffmpeg` to extract a temporary local keyframe. The temporary frame is removed after classification. Videos are never uploaded unless a cloud provider is explicitly enabled.

## Private Search, Timeline, And Map

Build and query the ignored local SQLite index:

```powershell
photosage search index --input ./photos
photosage search query "container home construction"
```

The default `hash` backend is offline. Set `embedding_backend: ollama` to use a loopback Ollama embedding model for semantic similarity. LAN embedding requests require the additional explicit `ollama.allow_sensitive_embeddings: true` setting because indexed text can contain private labels.

Generate a standalone offline browser report:

```powershell
photosage browse --input ./photos --output-html ./photosage-browser.html --output-json ./photosage-browser.json
```

The report contains timeline groups and an embedded GPS coordinate plot. It does not load online map tiles.

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
photosage astro --manifest ./manifests/rename_manifest_YYYYMMDD_HHMMSS.json --apply
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

Every preview or apply run writes an atomic, checksummed manifest in:

```text
manifests/
```

Undo reports are written in:

```text
rollback_reports/
```

Keep these files if you may need to undo a rename. Apply journals each operation before moving a file, allowing recovery after an interrupted run.

Every completed rename is fingerprinted again at its destination. A mismatch triggers an immediate rollback attempt. `photosage recover` reconciles interrupted states and can resume or roll back a manifest.

Validate a manifest:

```powershell
photosage manifest validate --manifest ./manifests/rename_manifest.json
```

Recompute hashes for existing referenced files in a validation report:

```powershell
photosage manifest validate --manifest ./manifests/rename_manifest.json --hashes
```

The validator checks:

- missing files
- manifest tampering
- unsafe paths
- undo collisions
- sidecar mismatches
- source SHA256 mismatches

## Project Docs

Start with the guide for the task:

- [CLI reference](docs/cli-reference.md): Generated command and option reference.
- [Configuration reference](docs/configuration-reference.md): Every setting,
  validation rule, provider option, and privacy boundary.
- [Recovery and review](docs/recovery-and-review.md): Manifest states, approval,
  apply integrity, resume, rollback, and undo.
- [Troubleshooting](docs/troubleshooting.md): Symptom-based diagnosis and safe
  support collection.
- [Kimi provider](docs/kimi-provider.md): Moonshot API setup, models, privacy,
  verification, and errors.
- [Architecture](docs/architecture.md): Processing flow, components, trust
  boundaries, and extension rules.
- [Lightroom integration](docs/lightroom-integration.md): Detailed Lightroom
  Classic workflow.
- [Catalog integrations](docs/catalog-integrations.md): Lightroom Classic,
  Capture One, and Apple Photos handoffs.
- [Windows packaging and release](packaging/README.md): Signing, build, publishing,
  and independent verification.
- [Contributing](CONTRIBUTING.md): Development rules and complete quality gate.
- [Security policy](SECURITY.md): Supported versions, private reporting, and
  trust boundaries.
- [Assessment](assessment.md): Current verified project state.
- [Changelog](CHANGELOG.md): User-visible changes.
- [Completed upgrades](completed-upgrades.md): Finished roadmap work.
- [Spec workflow](specs/README.md): Requirements, plan, and task workflow for
  larger changes.
- `future-upgrades.md`: Local-only roadmap. It is intentionally ignored by Git.

## Run Tests

```powershell
python -m pytest
```

CI also runs:

- pytest on Linux, Windows, macOS, Python 3.11, and Python 3.13
- full configured Ruff lint and formatting checks
- Pyright static type checks
- branch coverage with a 75 percent minimum for testable application logic
- Markdown link and spec checks
- locked dependency vulnerability auditing
- wheel build, metadata validation, installation, and outside-repository smoke tests
- tag-gated signed Windows executables, SBOM, checksums, and build provenance

## Privacy Notes

- Metadata is used before AI.
- Files are marked as AI-needed when metadata is weak or `--force-ai` is passed.
- Local-only mode is the default and blocks cloud providers.
- Cloud prompts exclude paths, filenames, GPS, titles, descriptions, OCR text, and keywords by default.
- Sensitive metadata requires an explicit per-provider `include_sensitive_metadata: true` setting.
- Kimi uses `MOONSHOT_API_KEY`, the official Moonshot API endpoint, base64 image input, and JSON mode.
- Providers return structured classification only.
- Providers do not rename or move files.
- API keys belong in `.env`, not in source control.
