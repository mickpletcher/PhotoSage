# PhotoSage Assessment

Last reviewed: 2026-08-11

## Status

PhotoSage is a production-ready local photo renaming application for reviewed workflows.

The CLI and GUI share the same safety contract. Preview creates a checksummed review target. Apply consumes that exact plan, journals its progress, and refuses changed source files.

## Verified Strengths

- Atomic, SHA256-protected manifest writes.
- Per-file rename journaling and interrupted-run rollback.
- Transactional Lightroom image and XMP sidecar handling.
- Exact reviewed-manifest apply in the CLI and GUI.
- Source SHA256, size, and modification-time verification before apply.
- No-overwrite and path-containment enforcement.
- Local-only AI is the default.
- Cloud prompts exclude paths, filenames, GPS, titles, descriptions, OCR text, and keywords by default.
- Provider retries and fallback survive expected and unexpected SDK failures.
- Concurrent AI requests use the configured limit.
- Duplicate matching uses a BK-tree instead of an all-pairs comparison.
- Duplicate analysis during normal rename planning is opt-in.
- Installable wheel includes runtime prompt resources and works outside the repository.
- Locked development dependencies and vulnerability auditing.
- Cross-platform CI for Linux, Windows, and macOS.
- Full Ruff lint and format enforcement.
- Branch coverage enforcement.
- Loopback-by-default local endpoint trust with explicit LAN allowlisting.
- Strict typed configuration validation and atomic config writes.
- Manual approve, reject, and filename-edit review history.
- Interrupted-run inspection, resume, rollback, and post-rename integrity verification.
- Provider benchmarking and generic local OpenAI-compatible support.
- Kimi K3 cloud vision support through Moonshot's official OpenAI-compatible API, with JSON mode and local-only blocking.
- Video metadata and temporary keyframe classification.
- Private local search plus offline timeline and GPS browser reports.
- Lightroom Classic, Capture One, and Apple Photos export handoffs.
- Fail-closed signed Windows release workflow with SBOM, checksums, and provenance.
- Generated CLI reference plus complete configuration, Kimi, recovery,
  architecture, troubleshooting, catalog, contributor, security, and release
  guides.
- Documentation checks fail when the CLI reference is stale or an application
  setting/provider is missing from the configuration reference.

## Safety Contract

1. Preview does not rename files.
2. Normal apply requires a reviewed manifest.
3. Unreviewed apply requires the explicit `--allow-unreviewed` override.
4. Every manifest is written atomically and protected by a SHA256 checksum.
5. Every source is fingerprinted during preview and rechecked before apply.
6. Every rename is journaled before the filesystem operation.
7. Existing destinations are never overwritten.
8. Undo never overwrites an original path.
9. Lightroom image and sidecar failures are rolled back together when possible.
10. Manifest paths cannot escape the recorded input directory.
11. Local-only mode blocks cloud providers.
12. Cloud metadata is allowlisted unless sensitive metadata is explicitly enabled.
13. Local provider endpoints cannot resolve to public addresses.
14. LAN provider endpoints require an exact allowlist and HTTPS by default.
15. Low-confidence AI and duplicate entries require review.
16. Destination content is fingerprinted after every rename.
17. Local search databases and browser reports remain ignored private artifacts.
18. Kimi is treated as cloud AI, uses only Moonshot's official global endpoint, and never receives sensitive metadata unless explicitly enabled.

## Normal Workflow

```powershell
photosage preview --input ./photos
photosage rename --manifest ./manifests/rename_manifest_YYYYMMDD_HHMMSS.json --apply
photosage undo --manifest ./manifests/rename_manifest_YYYYMMDD_HHMMSS.json --dry-run
photosage undo --manifest ./manifests/rename_manifest_YYYYMMDD_HHMMSS.json --force
```

## Verification

Verified on Windows 11 with Python 3.11:

- 172 tests pass.
- Branch coverage is 77% against a 75% gate.
- Ruff check and format checks pass.
- Pyright reports zero errors and warnings.
- The dependency audit reports no known vulnerabilities.
- Wheel and source distributions build and pass Twine checks.
- Standalone CLI and GUI executables build and pass startup smoke tests.
- The installed wheel works outside the repository and contains its prompt resources.
- CycloneDX SBOM generation succeeds.
- Documentation links, workflow YAML, PowerShell syntax, and Git whitespace checks pass.
- CLI and configuration references are checked against the live application.

Run:

```powershell
python -m pytest
python -m coverage run -m pytest
python -m coverage report
python -m ruff check src tests scripts
python -m ruff format --check src tests scripts
pyright src
python scripts/check_docs.py
python -m pip_audit -r requirements.lock --progress-spinner off
python -m build
python -m twine check dist/*
```

CI repeats these checks and installs the built wheel from outside the repository.

## Remaining Product Opportunities

The remaining roadmap is intentionally outside the current scope:

- OCR generation for scanned documents.
- Privacy-first unnamed face clustering.
- NAS and home-lab deployment.
- A third-party plugin API.
- Direct catalog write-back, which remains excluded because it weakens the safety boundary.

Any change affecting rename safety, manifests, providers, privacy, dependencies, or user workflow must update code, tests, and documentation in the same pass.
