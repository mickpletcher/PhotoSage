# Recovery and Review

PhotoSage treats every rename as a transaction with a durable manifest. The
normal path is preview, review, apply, verify, and retain the manifest for undo
or recovery.

## Safety model

PhotoSage does not overwrite an existing destination. Before apply, it checks
that the source still matches the preview fingerprint. After each rename, it
checks the destination fingerprint. A mismatch triggers rollback where possible
and records the result in the manifest.

Use this sequence for normal work:

```powershell
photosage preview --input C:\Photos\Incoming --config .\config.yaml
photosage review --manifest .\manifests\preview-manifest.json --approve sample.jpg
photosage rename --manifest .\manifests\preview-manifest.json --apply --config .\config.yaml
photosage manifest validate --manifest .\manifests\preview-manifest.json --hashes
```

Use the exact command options shown by `photosage COMMAND --help` for the installed
version. The generated [CLI Reference](cli-reference.md) documents every option.

## Manifest structure

Current manifests use schema version 2. Important top-level fields are:

| Field | Purpose |
| --- | --- |
| `schema_version` | Manifest contract version. |
| `run_id` | Unique processing run identifier. |
| `timestamp` | UTC creation time. |
| `input_directory` | Root directory processed by the run. Treat this as private local data. |
| `dry_run` | Whether the run was preview-only. |
| `provider_used` | Provider that produced AI results, if any. |
| `metadata_threshold` | Threshold used for the run. |
| `files` | Per-file plan, fingerprint, review, apply, and recovery state. |
| `manifest_sha256` | Integrity checksum over the manifest content. |

Manifests are written atomically through a temporary file, a flush to stable
storage, and replacement of the target. The checksum detects later edits or
partial corruption.

Manifests contain local paths and filenames. Keep them out of public repositories
and support attachments unless sanitized.

## Review states

Review applies to dry-run preview manifests. Each file selector must identify one
and only one entry by original path or original name.

Supported decisions are:

| Decision | Result |
| --- | --- |
| Approve | Keeps the proposed filename and marks it review-approved. |
| Reject | Prevents that proposed rename from being applied. |
| Edit | Replaces the proposed base filename, preserves the extension, sanitizes the result, and then approves it. |

PhotoSage blocks an edited name when it collides with another plan entry or an
existing file. Every decision records a timestamp, reviewer identifier, selector,
action, and old/new proposal in review history.

AI suggestions require review when `require_manual_review_for_ai` is true and
their confidence is below `review_confidence_threshold`. Duplicate groups always
require review because visual similarity is not proof that files are disposable.

## Apply states

Each planned file advances independently. Typical statuses are:

| Status | Meaning |
| --- | --- |
| `planned` | Preview entry has not entered apply. |
| `pending` | Approved entry is eligible for apply or resume. |
| `unchanged` | Proposed and original names are equivalent. |
| `missing` | Source did not exist when apply attempted. |
| `overwrite-prevented` | Destination already existed. Nothing was replaced. |
| `source-changed` | Size, modification time, or SHA-256 no longer matches preview. |
| `rename-started` | Journal checkpoint written immediately before the filesystem operation. |
| `renamed` | Rename completed and destination fingerprint verified. |
| `integrity-rollback` | Destination verification failed and the source was restored. |
| `integrity-error` | Verification failed and automatic restoration could not be confirmed. Manual inspection is required. |
| `error` | An unexpected error was recorded for that entry. |

PhotoSage skips entries not eligible for apply. It does not treat a failed item as
permission to overwrite or ignore integrity checks.

## Source fingerprints

Preview records the source SHA-256, size, and modification time. Apply checks the
fingerprint again. If another program edits, replaces, or retimestamps the source,
the entry becomes `source-changed`.

Do not force past that state. Generate a new preview from the current file. This
prevents an approved name from being applied to different content.

## Inspecting an interrupted run

Start with read-only inspection:

```powershell
photosage recover --manifest .\manifests\apply-manifest.json
```

Recovery classifies each entry from the filesystem and recorded fingerprint:

| Filesystem state | Recovery result |
| --- | --- |
| Original exists, destination absent, fingerprint matches | `ready` |
| Original exists, destination absent, fingerprint differs | `source-changed` |
| Destination exists, original absent, fingerprint matches | `completed` |
| Destination exists, original absent, fingerprint differs | `destination-changed` |
| Both original and destination exist | `collision` |
| Neither path exists | `missing` |

Inspection does not rename anything.

## Resuming

After inspection, resolve every collision, changed file, and missing path manually.
Then resume eligible entries:

```powershell
photosage recover --manifest .\manifests\apply-manifest.json --resume
```

Resume marks verified `ready` entries as pending, preserves verified completed
entries as renamed, records other recovery classifications, and applies only the
pending subset with the normal integrity checks.

Run inspect again after resume and validate the manifest:

```powershell
photosage recover --manifest .\manifests\apply-manifest.json
photosage manifest validate --manifest .\manifests\apply-manifest.json --hashes
```

## Rolling back and undoing

Recovery rollback uses the recorded transaction state:

```powershell
photosage recover --manifest .\manifests\apply-manifest.json --rollback
```

The separate undo command supports dry-run inspection and explicit application:

```powershell
photosage undo --manifest .\manifests\apply-manifest.json --dry-run
photosage undo --manifest .\manifests\apply-manifest.json --force
```

Undo never overwrites an existing original path. It reports collisions, missing
renamed files, and per-file errors. Use force only after inspecting the exact
manifest and command help. Force does not make destructive collisions safe.

## Manifest validation

Basic validation checks schema, checksum, statuses, path relationships, and
unsafe conditions:

```powershell
photosage manifest validate --manifest .\manifests\apply-manifest.json
```

Filesystem verification additionally checks renamed and original paths, undo
collisions, and optional fingerprints:

```powershell
photosage manifest validate --manifest .\manifests\apply-manifest.json --hashes
```

Validator findings include malformed records, unsafe paths, missing renamed
files, undo collisions, missing originals, inconsistent statuses, fingerprint
mismatches, and XMP sidecar problems.

## XMP sidecars

When a supported media file has an associated XMP sidecar, keep the pair together.
Validation reports a missing sidecar or destination collision. Do not repair the
manifest by hand. Restore the expected pair or create a new preview.

## Incident procedure

If an apply is interrupted:

1. Stop other photo organizers and catalog synchronization.
2. Copy the manifest to a separate local backup.
3. Run recovery inspection.
4. Record the reported states without editing the manifest.
5. Resolve external collisions and changed files.
6. Resume or roll back one manifest at a time.
7. Validate with filesystem checks.
8. Back up the final manifest with the affected photo set.

Do not rerun a fresh rename over a partially completed directory before inspecting
the interrupted manifest.
