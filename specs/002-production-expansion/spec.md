# Production Expansion Specification

## Objective

Complete the remaining privacy, recovery, review, provider, media, browsing, catalog, release, and verification work without weakening PhotoSage's reviewed-manifest safety model.

## Requirements

- Local provider endpoints must be loopback by default. LAN access requires exact allowlisting. Public addresses and redirects are blocked.
- Configuration must reject unknown, mistyped, or unsafe values and save atomically.
- Review manifests must support approve, reject, edit, and audit history.
- Interrupted runs must support inspect, resume, and rollback. Destination content must be verified after rename.
- Benchmark and generic local OpenAI-compatible provider workflows must preserve cloud opt-in boundaries.
- Kimi must use Moonshot's official global endpoint, OpenAI-compatible multimodal requests, structured JSON output, and the existing cloud privacy boundary.
- Duplicate and folder organization workflows must remain preview-first and non-deleting.
- Video support must use temporary keyframes and preserve the original video.
- Search, timeline, and map data must remain local by default.
- Catalog integrations must use export handoffs and never modify catalog databases.
- Release publication must require valid Authenticode signatures and include an SBOM, checksum, smoke test, and provenance.

## Acceptance

Code, tests, docs, lock files, CI, package builds, and outside-repository smoke tests must pass together.
