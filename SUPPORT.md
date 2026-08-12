# PhotoSage Support

PhotoSage is independently maintained. Support is best-effort and focuses on the
latest code on `main` until versioned releases begin.

## Before opening an issue

1. Read the [troubleshooting guide](docs/troubleshooting.md).
2. Run `photosage doctor` and `photosage config validate`.
3. Confirm the problem still occurs with the latest supported version.
4. Reproduce the problem with synthetic media and a minimal configuration.
5. Search existing issues before creating a new report.

Use the structured bug or feature template when an issue is needed. Include the
PhotoSage version or commit, operating system, Python version, installation
method, exact sanitized command, expected result, and actual result.

## Protect private data

Do not publish API keys, access tokens, signing material, personal photos, GPS
coordinates, private paths, manifests, logs, search databases, geocode caches,
or AI provider response content. Redact diagnostics and use synthetic examples.

Security and privacy vulnerabilities must be reported through
[GitHub private vulnerability reporting](https://github.com/mickpletcher/PhotoSage/security/advisories/new),
not a public issue.

## Scope

The project can help diagnose PhotoSage behavior and documented integrations.
Third-party AI accounts, model quality, camera firmware, operating-system
support, Lightroom, Capture One, Apple Photos, ffmpeg, Ollama, and LM Studio may
require support from their respective vendors.
