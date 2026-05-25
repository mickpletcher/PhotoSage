# Changelog

All notable changes to PhotoSage will be documented in this file.

The format is based on Keep a Changelog, and this project follows semantic versioning once releases begin.

## [Unreleased]

### Added

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
