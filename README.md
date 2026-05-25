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

Provider stubs are included for:

- Anthropic Claude
- OpenAI vision models
- Google Gemini
- Ollama local vision models

The provider system is intentionally model agnostic. Provider implementations must normalize output into the shared JSON contract before PhotoSage builds filenames.

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
```

Copy `.env.example` to `.env` if you later add real provider API calls. Do not commit API keys.

## CLI Examples

Scan a folder:

```powershell
photosage scan --input ./photos
```

Preview proposed renames:

```powershell
photosage preview --input ./photos
```

Preview through the rename command:

```powershell
photosage rename --input ./photos
```

Apply renames:

```powershell
photosage rename --input ./photos --apply
```

Force AI fallback:

```powershell
photosage preview --input ./photos --force-ai
```

Undo a rename run:

```powershell
photosage undo --manifest ./manifests/rename_manifest.json
```

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
- Limit filename length to 180 characters.
- Preserve the original extension.
- Add counters to prevent overwrites.

Example:

```text
2026-05-25_dover-tn_shipping-container_deck-construction_001.jpg
```

## Manifest And Undo

Every preview or rename creates a manifest under `manifests/`.

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
