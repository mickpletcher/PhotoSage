# Security Policy

## Supported versions

Security fixes are applied to the latest code on `main` until versioned releases
begin. After releases begin, the latest release is the supported version.

## Reporting a vulnerability

Do not open a public issue, discussion, or pull request for a vulnerability that
could expose local files, credentials, photo metadata, or provider data. Use
GitHub private vulnerability reporting for this repository.

Include the affected version and command, expected boundary, synthetic
reproduction steps, actual result, security impact, and whether any files or
remote services were modified. Do not include API keys, access tokens, personal
photos, private paths, manifests, logs, GPS data, databases, signing certificates,
or provider response content.

If a secret was exposed during reproduction, revoke it before submitting the
report. Maintainers will validate the report, coordinate a fix and release, and
disclose it after affected users have a reasonable update path.

## Security boundaries

- PhotoSage does not delete source photos.
- Normal apply requires a reviewed, checksummed manifest.
- Existing files are never overwritten.
- Local-only provider mode is the default.
- Local providers accept loopback endpoints by default, require exact LAN
  allowlisting, and reject public addresses.
- Insecure LAN HTTP is a separate explicit opt-in.
- Provider HTTP redirects are disabled.
- Cloud metadata is allowlisted unless sensitive metadata is explicitly enabled.
- Kimi requests are restricted to `https://api.moonshot.ai/v1`; selecting Kimi
  uploads the image to Moonshot AI and requires `local_only: false`.
- API keys must remain in environment variables or ignored local secret files.

Selecting any cloud vision provider sends image content and an allowlisted
metadata subset to that provider. Keep `local_only: true` when media must not
leave the device.

## Filesystem safety

Rename operations use preview by default, source fingerprints, a journal
checkpoint before mutation, destination verification, recovery states, and safe
undo. Low-confidence AI suggestions and duplicate findings are review-gated.

Another application can still move, replace, lock, or alter files outside
PhotoSage. Maintain backups and avoid concurrent catalog or file operations during
apply, recovery, or undo. PhotoSage is not a backup system.

## Sensitive local artifacts

Manifests, logs, rollback reports, caches, thumbnails, geocoding data, browser
reports, video keyframes, benchmark reports, profiles, and search databases can
reveal filenames, directory layouts, locations, derived content, or processing
history. They are ignored by Git and should not be attached to public reports.
Temporary video keyframes are removed when analysis finishes.

Protect runtime artifacts with operating-system access controls and storage
encryption appropriate for the photo library.

## Dependency and release security

Release executables must pass Authenticode verification before publication.
Release output should also include SHA-256 checksums, an SBOM, and build provenance.
Verify checksum and signer identity before running a downloaded binary. Do not
bypass a failed signature or reputation warning without independently verifying
the artifact.

## Out of scope

Do not access systems without authorization or publish private user data to prove
an issue. Report vulnerabilities in third-party AI platforms through the
provider's own security process.
