# PhotoSage Assessment

Last reviewed: 2026-05-25

## Short Version

PhotoSage is a Python 3.11+ photo organization tool.

It is metadata first. It previews before renaming. It writes manifests. It supports undo.

The project is no longer just a scaffold. The main architecture is in place.

## What Works Now

- CLI: `photosage`
- GUI: `photosage-gui`
- Metadata extraction and scoring
- Safe rename preview
- Safe apply mode
- Manifest generation
- Manifest integrity validation
- Undo and rollback reports
- Provider abstraction
- Ollama local provider support
- Lightroom export folder support
- XMP sidecar parsing and rename sync
- Screenshot and document image labeling
- Pytest coverage across core modules

## Core Flow

1. Scan supported images.
2. Extract local metadata.
3. Score metadata quality.
4. Mark files as AI-needed when metadata is weak or forced.
5. Normalize AI output when provider data is supplied.
6. Build filenames locally.
7. Preview changes.
8. Write a manifest.
9. Rename only with `--apply`.
10. Undo from the manifest if needed.

## Non-Negotiable Safety Rules

- Never rename without `--apply`.
- Never overwrite files.
- Never delete source photos.
- Always write a manifest before apply mode.
- Undo must never overwrite files.
- `local_only: true` must block cloud providers.
- Providers must not rename or move files.
- Do not log API keys or image bytes.
- Do not modify Lightroom catalog databases.

## Main Files

- `README.md`: Start here.
- `config/settings.yaml`: User settings.
- `src/photosage/cli.py`: CLI commands.
- `src/photosage/scanner.py`: File scanning.
- `src/photosage/metadata/exif_reader.py`: Metadata extraction.
- `src/photosage/metadata/metadata_score.py`: Metadata scoring.
- `src/photosage/providers/provider_manager.py`: Provider fallback and local-only policy.
- `src/photosage/providers/ollama_provider.py`: Ollama provider.
- `src/photosage/rename/renamer.py`: Rename preview and apply.
- `src/photosage/manifest/undo.py`: Undo and rollback.
- `src/photosage/lightroom/exporter.py`: Lightroom export workflow.
- `src/photosage/gui/app.py`: GUI entry point.
- `tests/`: Test suite.

## Commands To Know

```powershell
photosage scan --input ./photos
photosage preview --input ./photos
photosage rename --input ./photos --apply
photosage undo --manifest ./manifests/rename_manifest.json
photosage manifest validate --manifest ./manifests/rename_manifest.json
photosage providers
photosage ollama models
photosage lightroom-process --input ./LightroomExports --preview
```

## Docs To Keep Current

- `README.md`
- `CHANGELOG.md`
- `assessment.md`
- `completed-upgrades.md`
- `docs/lightroom-integration.md`
- `specs/README.md`
- `specs/001-lm-studio-provider/`

`future-upgrades.md` is local-only and ignored by git.

## Tests

Run:

```powershell
python -m pytest
```

Most recent known result:

```text
87 passed, 1 skipped
```

The skipped test is expected when optional GUI pieces are unavailable.

## Known Gaps

Good next work:

1. Implement LM Studio provider from `specs/001-lm-studio-provider/`.
2. Add stronger end-to-end CLI smoke tests.
3. Add reverse geocoding cache.
4. Improve GUI performance for large folders.
5. Add duplicate detection.
6. Add folder watcher mode.

## Future Agent Checklist

Before changing behavior:

1. Read `README.md`.
2. Read this file.
3. Check `CHANGELOG.md`.
4. Check active specs under `specs/`.
5. Run `python -m pytest`.

If a change affects rename safety, manifests, providers, or user workflow, update docs and tests in the same pass.
