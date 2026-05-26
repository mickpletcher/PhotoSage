# Changelog

All notable changes to PhotoSage will be documented in this file.

The format is based on Keep a Changelog, and this project follows semantic versioning once releases begin.

## [Unreleased]

### Added

- Added watch folder processing with file stability checks, approval queue manifests, and explicit apply mode.
- Added local duplicate detection with perceptual hashing, duplicate preview output, JSON export, and manifest duplicate group fields.
- Added GUI performance helpers for thumbnail caching, faster table loading, saved profiles, and recent manifest tracking.
- Added folder organization policies for date-first, location-first, project-first, and custom keyword-to-folder mapping.
- Added local reverse geocoding cache with TTL settings and GPS alias commands.
- Added astrophotography support with capture-night grouping, telescope/filter/target/exposure filename tokens, lunar/solar/planetary/deep-sky profiles, and lightweight FITS metadata parsing.
- Added live AI analysis during preview and apply planning for files below the metadata threshold or when `--force-ai` is used.
- Added safe provider failure handling with `ai-unavailable` manifest status so apply mode skips files that required AI but could not be analyzed.
- Added lightweight `.env` loading for local provider API keys without overriding shell environment variables.
- Added screenshot and document mode with local metadata labels, source app detection, document type hints, OCR summary metadata support, and new filename tokens.
- Added GitHub Actions CI for pytest, basic Ruff lint checks, Markdown link checks, and spec folder checks.
- Added `photosage manifest validate` with missing file checks, safe path validation, sidecar mismatch detection, undo collision warnings, and optional SHA256 hashes.
- Hardened local-only provider selection with registered local provider detection, blocked provider audit logs, and local-only status in CLI summaries.
- Added a concise novice-focused documentation pass across README, Lightroom docs, assessment, specs, and completed upgrade tracking.
- Added a repo-local specs workflow under `specs/` with a seeded `001-lm-studio-provider` requirements, plan, and task package.
- Added Lightroom export workflow support with XMP sidecar parsing, embedded XMP fallback, metadata score bonuses, sidecar synchronization, optional folder organization, catalog safety blocking, Lightroom presets, and `photosage lightroom-process`.
- Added Lightroom integration documentation and tests for XMP parsing, metadata mapping, folder organization, catalog safety, CLI preview, and sidecar rename behavior.
- Built the first PySide6 desktop GUI scaffold with a functional main window, folder picker, provider controls, scan and preview table, image and metadata detail panels, settings dialog, undo dialog, worker threads, progress panel, and logging console.
- Added a GUI service layer that reuses the existing metadata, provider, rename, manifest, and undo backends without duplicating business logic.
- Added `photosage-gui` entry point and GUI service tests.
- Added full Ollama local vision support with image preprocessing, supported model validation, configurable endpoint/model/timeouts, malformed JSON retry, and local REST API integration.
- Added provider health checks plus `photosage providers`, `photosage ollama models`, and `photosage ollama info` commands.
- Added tests for Ollama endpoint handling, JSON normalization, malformed response retry, timeout handling, health checks, model discovery, and CLI provider output.
- Built the phase 6 CLI with Rich scan, preview, rename, and undo screens, provider overrides, local-only mode, recursive controls, verbose logging, JSON exports, and apply safety enforcement.
- Added CLI tests for argument handling, provider overrides, JSON output, rename safety, preview output, and undo dry-run behavior.
- Built the phase 5 undo system with manifest parsing, rollback validation, dry-run support, collision prevention, partial rollback handling, and rollback reports.
- Added `photosage undo` options for `--dry-run`, `--verbose`, and `--continue-on-error/--stop-on-error`.
- Added rollback report generation under `rollback_reports/` and tests for malformed manifests, invalid paths, collisions, dry runs, partial rollback, and report output.
- Built the phase 4 rename engine with deterministic filename building, hardened sanitization, cached collision prevention, dry-run previews, apply mode, manifests, and rollback support.
- Added Rich CLI output for scan, preview, rename, and undo summaries.
- Added tests for rename preview, apply, rollback, Unicode sanitization, reserved Windows names, duplicate handling, and dry-run undo behavior.
- Added `completed-upgrades.md` to track upgrades moved from `future-upgrades.md` after completion.
- Built the phase 3 provider abstraction layer with factory, manager, retry handling, response normalization, provider exceptions, and local only enforcement.
- Added provider implementations for Anthropic, OpenAI, Gemini, and local Ollama with normalized structured JSON output.
- Added provider tests for selection, fallback, retry behavior, invalid JSON repair, unsupported providers, and local only mode.
- Built the phase 2 metadata engine with normalized `PhotoMetadata`, richer EXIF extraction, GPS parsing, metadata score details, and metadata-only filename generation.
- Added support dependencies for HEIC metadata, EXIF tag reading, date parsing, and rich CLI output.
- Added tests for normalized image metadata extraction, GPS parsing, and metadata-driven filenames.
- Created the Python 3.11+ PhotoSage CLI project scaffold.
- Added metadata first scan, scoring, preview, rename, manifest, and undo modules.
- Added model agnostic vision provider stubs for Anthropic, OpenAI, Gemini, and Ollama.
- Added deterministic filename building, sanitization, duplicate prevention, and safe dry run behavior.
- Added pytest coverage for scoring, sanitization, filename building, duplicate handling, manifests, and undo.
- Added README, configuration, prompt, future upgrades, and sample manifest files.

### Removed

- Removed `future-upgrades.md` from version control and added ignore protection to prevent accidental re-commit.

### Changed

- Ensured `future-upgrades.md` is ignored in `.gitignore` and untracked from git index so it will not be pushed.
- Reworked `future-upgrades.md` into a three tier roadmap with clearer, action oriented upgrade suggestions.
