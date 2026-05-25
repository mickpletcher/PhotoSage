# PhotoSage Assessment

Last reviewed: 2026-05-25

## Current State

PhotoSage is a Python 3.11+ metadata-first photo organization project.

The repo currently includes:

- CLI entry point: `photosage`
- GUI entry point: `photosage-gui`
- Metadata extraction and scoring engine
- Provider abstraction for cloud and local vision models
- Ollama local vision support
- Rename preview and apply engine
- Manifest generation
- Undo and rollback reporting
- Lightroom export folder workflow support
- XMP sidecar parsing and synchronization
- Pytest coverage across core modules

The project is functional as a safe local photo rename tool. The core safety model is already in place.

## Core Architecture

PhotoSage follows this order:

1. Scan supported image files.
2. Extract local filesystem, EXIF, GPS, embedded metadata, and XMP metadata.
3. Score metadata quality.
4. Use AI only when metadata is below the configured threshold or forced.
5. Normalize any AI response into the internal provider contract.
6. Build filenames locally with deterministic code.
7. Preview all changes.
8. Write a manifest before apply mode.
9. Rename only when explicitly requested.
10. Use manifests and rollback reports for undo.

AI providers classify images only. They must not rename files, move files, or generate final filenames.

## Safety Rules

These rules are important and should not be weakened:

- Never rename files unless `--apply` is explicitly provided.
- Never overwrite existing files.
- Never delete original images.
- Always write a manifest before applying renames.
- Undo must never overwrite existing files.
- Do not upload images when `local_only: true`.
- Do not log API keys or raw image data.
- Do not directly modify Lightroom catalog databases.
- Block probable Lightroom catalog paths unless `--force-catalog-modify` is used.
- Sanitize all metadata and AI-derived filename parts before using them in paths.

## Implemented Modules

Main package layout:

```text
src/photosage/
  cli.py
  scanner.py
  config.py
  logging_config.py
  metadata/
  providers/
  rename/
  manifest/
  lightroom/
  gui/
```

Important files:

- `src/photosage/cli.py`: Typer CLI commands.
- `src/photosage/config.py`: YAML settings model and loader.
- `src/photosage/scanner.py`: Supported file scanning.
- `src/photosage/metadata/exif_reader.py`: Metadata extraction.
- `src/photosage/metadata/metadata_score.py`: Metadata confidence scoring.
- `src/photosage/providers/provider_manager.py`: Provider fallback and local-only policy.
- `src/photosage/providers/ollama_provider.py`: Local Ollama vision provider.
- `src/photosage/rename/renamer.py`: Preview and apply rename orchestration.
- `src/photosage/rename/filename_builder.py`: Deterministic filename generation.
- `src/photosage/manifest/manifest_writer.py`: Manifest creation.
- `src/photosage/manifest/undo.py`: Rollback and undo.
- `src/photosage/lightroom/exporter.py`: Lightroom export processing.
- `src/photosage/gui/app.py`: GUI entry point.

## CLI Status

Implemented commands:

```powershell
photosage scan --input ./photos
photosage preview --input ./photos
photosage rename --input ./photos --apply
photosage undo --manifest ./manifests/rename_manifest.json
photosage providers
photosage ollama models
photosage ollama info
photosage lightroom-process --input ./LightroomExports --preview
photosage lightroom-process --input ./LightroomExports --apply
```

The CLI uses Rich output for tables, warnings, progress, and summaries.

## GUI Status

The GUI is scaffolded with PySide6 and uses backend services instead of duplicating business logic.

Current GUI capabilities include:

- Folder selection
- Scan workflow
- Preview workflow
- Preview table
- Image and metadata panels
- Provider settings
- Undo dialog
- Logging console
- Worker-based long-running operations

The GUI is functional but still early. Visual polish, thumbnail caching, and high-volume performance tuning remain future work.

## Provider Status

Implemented provider architecture:

- Base `VisionProvider` interface
- Provider factory
- Provider manager
- Retry handler
- Response normalizer
- Provider exceptions
- Local-only enforcement
- Health checks

Provider implementations:

- Anthropic
- OpenAI
- Gemini
- Ollama

Recommended next provider addition:

- LM Studio local provider using its OpenAI-compatible local API.

## Lightroom Status

Implemented Lightroom support is export-folder based.

Supported:

- XMP sidecar parsing
- Embedded XMP fallback
- Lightroom metadata mapping
- Metadata score bonuses from Lightroom fields
- Sidecar rename synchronization
- Optional folder organization
- Presets
- Catalog safety checks
- Manifest additions for Lightroom data
- Undo support for renamed sidecars

Not implemented:

- Native Lightroom plugin
- Direct Adobe SDK integration
- Lightroom catalog database modification

Direct catalog modification should stay out of scope unless a future feature has strong safety controls.

## Documentation Status

Primary docs:

- `README.md`: Main usage, architecture, CLI, GUI, privacy, and safety documentation.
- `CHANGELOG.md`: Keep a Changelog style change tracking.
- `completed-upgrades.md`: Completed roadmap items.
- `docs/lightroom-integration.md`: Lightroom workflow documentation.
- `specs/README.md`: Spec workflow for larger changes.
- `specs/001-lm-studio-provider/`: First active provider spec package.
- `future-upgrades.md`: Local-only ignored planning roadmap.

`future-upgrades.md` is intentionally ignored by git.

## Test Status

Current test command:

```powershell
python -m pytest
```

Most recent known result:

```text
87 passed, 1 skipped
```

The skipped test is expected when optional GUI runtime pieces are unavailable.

## Known Gaps

High-value next work:

1. Add LM Studio as a local OpenAI-compatible vision provider.
2. Add GitHub Actions for pytest and basic quality checks.
3. Add stronger end-to-end CLI smoke tests with temp photo folders.
4. Add local-only workflow hardening across all provider entry points.
5. Add reverse geocoding cache for stable location labels.
6. Add thumbnail caching and batch update performance improvements for the GUI.
7. Add duplicate detection with perceptual hashing.
8. Add folder watcher mode with approval queue.

## Future Agent Starting Points

Read these first:

1. `README.md`
2. `CHANGELOG.md`
3. `assessment.md`
4. `specs/README.md`
5. `config/settings.yaml`
6. `src/photosage/cli.py`
7. `src/photosage/rename/renamer.py`
8. `src/photosage/manifest/undo.py`
9. `src/photosage/providers/provider_manager.py`
10. `src/photosage/lightroom/exporter.py`
11. `tests/`

Before making behavioral changes, run:

```powershell
python -m pytest
```

For CLI checks without installing the package in editable mode:

```powershell
$env:PYTHONPATH='src'
python -m photosage.cli --help
```

## Assessment

The project is past initial scaffold stage and now has a real architecture.

The strongest parts are the metadata-first design, rename safety model, manifest rollback system, provider abstraction, and test coverage.

The main risk is feature growth outpacing integration tests and documentation. Keep adding tests with every new workflow. Keep README, CHANGELOG, and this assessment synced when major behavior changes.
