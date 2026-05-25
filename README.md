# PhotoSage

PhotoSage is a Python 3.11+ CLI for metadata first photo organization and safe intelligent file renaming.

It reads local photo metadata first. It only asks a vision LLM for structured image understanding when metadata is not good enough or when `--force-ai` is used.

## Why Metadata First

Photo metadata is usually safer, cheaper, faster, and more accurate than sending images to a model.

PhotoSage uses EXIF dates, GPS data, camera details, dimensions, existing keywords, and useful original filenames before any AI fallback. The default metadata threshold is `70`. Scores below that threshold can trigger the configured provider unless `local_only` is enabled.

The metadata engine normalizes filesystem data, image dimensions, camera details, EXIF dates, GPS coordinates, altitude, GPS timestamps, title, description, keywords, and tags into a `PhotoMetadata` dataclass before the rest of the app makes decisions.

## Core Safety Model

- No file is renamed unless `--apply` is passed.
- `preview` shows proposed names without changing files.
- `rename` without `--apply` also stays in dry run mode.
- A manifest is written before applying renames.
- Existing files are never overwritten.
- Undo uses the manifest to move files back.
- Images are not uploaded to a provider when `local_only: true`.

## Supported Image Types

- `jpg`
- `jpeg`
- `png`
- `heic`
- `webp`
- `tiff`

Unsupported files are skipped and logged.

## Supported Providers

The provider system is model agnostic. Providers can be swapped by editing `config/settings.yaml`.

- Anthropic Claude
- OpenAI vision models
- Google Gemini
- Ollama local vision models

All providers normalize output into the same internal contract:

```json
{
  "primary_subject": "string",
  "secondary_subject": "string",
  "activity": "string",
  "environment": "string",
  "location_guess": "string",
  "confidence": 0.0,
  "tags": [],
  "description": "string",
  "provider": "string",
  "model": "string"
}
```

Providers classify image content only. They do not rename files, move files, or build final filenames.

### Fallback Behavior

PhotoSage starts with `vision_provider`, then tries each configured provider in `fallback_order` if a provider fails.

```yaml
vision_provider: anthropic

fallback_order:
  - anthropic
  - openai
  - gemini
  - ollama
```

Retry logic handles invalid JSON, transient provider failures, timeouts, and local Ollama availability issues. Authentication and invalid configuration failures are not retried.

### Local Only Mode

When `local_only: true`, cloud providers are blocked. Only local providers such as Ollama are allowed.

```yaml
local_only: true
vision_provider: ollama
```

This prevents PhotoSage from uploading images to Anthropic, OpenAI, or Gemini.

### Ollama Setup

Install Ollama and pull a local multimodal model:

```powershell
ollama pull llava
```

Supported local model targets include:

- `llava`
- `minicpm-v`
- `qwen-vl`
- future Ollama vision models

## Install

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pip install -e .
```

## Configuration

Edit [config/settings.yaml](config/settings.yaml).

```yaml
vision_provider: anthropic
metadata_threshold: 70
dry_run_default: true
local_only: false

fallback_order:
  - anthropic
  - openai
  - gemini
  - ollama

filename_format: "{date}_{location}_{subject}_{context}_{counter}"
provider_retry_count: 3
provider_retry_initial_delay: 0.5

anthropic:
  model: claude-sonnet-4

openai:
  model: gpt-4.1-mini

gemini:
  model: gemini-2.5-pro

ollama:
  endpoint: http://localhost:11434
  model: llava
```

Copy `.env.example` to `.env` if you later add real provider API calls. Do not commit API keys.

## CLI Examples

Scan a folder:

```powershell
photosage scan --input ./photos
```

Scan only the top-level folder:

```powershell
photosage scan --input ./photos --no-recursive
```

Preview proposed renames:

```powershell
photosage preview --input ./photos
```

Export preview results:

```powershell
photosage preview --input ./photos --output-json ./preview.json
```

Preview through the rename command:

```powershell
photosage rename --input ./photos
```

The rename command does not rename anything unless `--apply` is present. Without `--apply`, it exits with a safety warning.

Apply renames:

```powershell
photosage rename --input ./photos --apply
```

Force AI fallback:

```powershell
photosage preview --input ./photos --force-ai
```

Override provider and block cloud providers:

```powershell
photosage scan --input ./photos --provider ollama --local-only
```

Undo a rename run:

```powershell
photosage undo --manifest ./manifests/rename_manifest.json
```

Preview undo without moving files:

```powershell
photosage undo --manifest ./manifests/rename_manifest.json --dry-run --verbose
```

Stop on the first rollback error:

```powershell
photosage undo --manifest ./manifests/rename_manifest.json --stop-on-error
```

All main commands support:

- `--recursive` and `--no-recursive`
- `--provider anthropic|openai|gemini|ollama`
- `--force-ai`
- `--local-only`
- `--verbose`
- `--output-json ./file.json`
- `--config ./config/settings.yaml`

`undo` accepts these shared options for command consistency, but it restores from manifest paths and does not call providers or AI.

## CLI Output

PhotoSage uses Rich tables, panels, progress indicators, and colored statuses.

- Green means success or metadata-only handling.
- Yellow means warning, dry run, or AI-required handling.
- Red means errors, skipped files, missing files, or collisions.

Verbose mode enables console logs. File logs are always written to `logs/photosage.log`.

## Rename Workflow

The rename engine does not call live LLM providers. It works from extracted metadata, optional normalized AI classification JSON, and local filesystem state.

Use this workflow:

1. Run `photosage preview --input ./photos`.
2. Review proposed filenames and the generated dry-run manifest.
3. Run `photosage rename --input ./photos --apply` only when the preview is acceptable.
4. Use `photosage undo --manifest ./manifests/file.json` if you need to restore renamed files.

Metadata-only rename example:

```text
IMG_0001.jpg -> 2026-05-25_gps-location_shipping-container_canon-r5_001.jpg
```

Metadata plus AI classification example:

```json
{
  "primary_subject": "shipping container",
  "activity": "deck construction",
  "location_guess": "dover tn"
}
```

```text
IMG_0001.jpg -> 2026-05-25_dover-tn_shipping-container_deck-construction_001.jpg
```

Preview mode writes a manifest with `status: planned` and does not rename files. Apply mode writes a manifest before changing files, then records `renamed`, `missing`, `overwrite-prevented`, `unchanged`, or `error` for each item.

Collision handling never overwrites files. PhotoSage scans target names once per directory, tracks planned names during the batch, and advances counters as needed:

```text
2026-05-25_dover-tn_deck_001.jpg
2026-05-25_dover-tn_deck_002.jpg
```

Undo reads the manifest and safely reverses renamed files. It skips missing files, prevents overwrite conflicts, supports partial rollback, writes a rollback report, and logs every result.

## Filename Format

PhotoSage builds filenames locally with deterministic code.

Format:

```text
YYYY-MM-DD_location_subject_context_###.ext
```

Rules:

- Use EXIF date first.
- Fall back to file modified date.
- Use metadata location first.
- Fall back to LLM `location_guess`.
- Sanitize every filename part.
- Lowercase filenames.
- Replace spaces with hyphens.
- Remove unsafe characters.
- Normalize Unicode to portable ASCII.
- Prevent Windows reserved filenames like `CON`, `PRN`, `AUX`, `NUL`, `COM1`, and `LPT1`.
- Limit filename length to 180 characters.
- Preserve the original extension.
- Add counters to prevent overwrites.

Example:

```text
2026-05-25_dover-tn_shipping-container_deck-construction_001.jpg
```

## Manifest And Undo

Every preview or rename creates a manifest under `manifests/`.

Manifest filename format:

```text
rename_manifest_YYYYMMDD_HHMMSS.json
```

The manifest records:

- run ID
- timestamp
- input directory
- dry run state
- provider used
- metadata threshold
- original and new paths
- metadata score
- whether AI was used
- extracted metadata
- normalized AI response
- status

Undo reads the manifest, skips missing files, prevents overwrites, and logs each result.

Rollback reports are written under:

```text
rollback_reports/
```

Report filename format:

```text
rollback_YYYYMMDD_HHMMSS.json
```

Rollback statuses:

- `restored`: file was moved back to its original path, or dry run verified that it could be restored.
- `skipped_missing`: renamed file was missing.
- `skipped_collision`: original path already exists, so PhotoSage did not overwrite it.
- `failed`: manifest entry was invalid, unsafe, or not rollbackable.

Undo safety rules:

- Never overwrite existing files.
- Never delete files.
- Do not append counters during undo.
- Reject malformed manifests.
- Reject path traversal and paths outside the manifest input directory.
- Continue processing remaining entries unless `--stop-on-error` is used.

## Logs

PhotoSage writes logs to:

```text
logs/photosage.log
```

The log includes scanned files, skipped files, metadata scores, AI fallback decisions, suggested filenames, applied renames, undo operations, and errors.

## Privacy Notes

- Metadata is the primary source of truth.
- Images are not sent to providers unless metadata is insufficient or `--force-ai` is used.
- Images are never sent to providers when `local_only: true`.
- The LLM is only allowed to return structured classification data.
- The LLM does not rename files.
- Prompts instruct providers not to identify private people unless names already exist in metadata.
- API keys belong in `.env`, never in source control.

## Roadmap

See [future-upgrades.md](future-upgrades.md).
