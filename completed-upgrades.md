# Completed Upgrades

This file tracks roadmap items that are finished.

Use it with `future-upgrades.md`.

## How To Update

When an upgrade is completed:

1. Remove it from `future-upgrades.md`.
2. Add it here.
3. Include the date.
4. Link related specs, commits, or notes when useful.

## Completed

### 2026-08-11

- Added community health templates, code ownership, full-SHA workflow pinning,
  release tag validation, cross-platform setup guidance, and package metadata.
- Added a generated CLI reference, exhaustive configuration reference, and
  detailed operational, provider, architecture, contribution, security, catalog,
  troubleshooting, and release documentation with drift enforcement.
- Added Kimi K3 cloud vision support with Moonshot API authentication, JSON mode, privacy filtering, health checks, and local-only enforcement.
- Added local, LAN, and cloud endpoint trust enforcement.
- Added strict configuration validation and installation diagnostics.
- Added manual review editing and audit history in CLI and GUI workflows.
- Added interrupted-run recovery and post-rename integrity checks.
- Added provider benchmarking and generic local OpenAI-compatible support.
- Added duplicate review manifests and folder policy comparison.
- Added video metadata and temporary keyframe classification.
- Added private local search, offline timelines, and GPS views.
- Added native export handoffs for Lightroom Classic, Capture One, and Apple Photos.
- Added signed Windows release packaging, SBOM, checksums, and provenance.
- Added GUI, endpoint, recovery, scale, fault, video, search, and browsing tests.
- Added atomic, checksummed, crash-recoverable rename manifests.
- Added exact reviewed-manifest apply across CLI, GUI, watch, astro, and Lightroom workflows.
- Added source and sidecar fingerprints with apply-time change detection.
- Added transactional Lightroom sidecar failure rollback.
- Made local-only AI the default and allowlisted cloud metadata.
- Hardened provider exception normalization, fallback, and health reporting.
- Added concurrent AI analysis and scalable BK-tree duplicate matching.
- Repaired installed configuration and packaged prompt resource handling.
- Added locked dependencies and security auditing.
- Expanded CI across operating systems and supported Python versions.
- Enforced full Ruff checks, formatting, coverage, package validation, and installed-wheel smoke tests.

### 2026-05-25

- Created this tracking file.
- Added the metadata engine.
- Added the provider system.
- Added the rename engine.
- Added undo and rollback reports.
- Added the Typer CLI.
- Added Ollama support.
- Added the first PySide6 GUI.
- Added Lightroom export folder support.
- Added the repo spec workflow.
- Added `assessment.md` for future agents.
- Added GitHub Actions CI for tests, basic lint checks, docs links, and spec folder checks.
- Added manifest integrity validation.
- Hardened local-only provider selection and CLI visibility.
- Added screenshot and document mode for mixed image libraries.
- Added live AI analysis pipeline for preview and apply planning.
- Added folder watcher approval queues.
- Added duplicate detection with perceptual hashing and JSON reports.
- Added GUI performance helpers for thumbnail caching and recent manifests.
- Added folder organization policies.
- Added local reverse geocoding cache.
- Added astrophotography expansion with FITS metadata, capture-night grouping, astro profiles, and filename tokens.
- Added LM Studio local vision provider support.
