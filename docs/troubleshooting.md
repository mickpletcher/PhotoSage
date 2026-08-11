# Troubleshooting

Start with read-only diagnostics:

```powershell
photosage config validate --config .\config.yaml
photosage doctor --config .\config.yaml
photosage providers --config .\config.yaml
```

Use `photosage --help` and the generated [CLI Reference](cli-reference.md) to
confirm syntax for the installed version.

## Configuration fails to load

Run `photosage config validate`. Compare the reported key with the
[Configuration Reference](configuration-reference.md). Check YAML indentation,
ensure provider sections are mappings, remove unsupported keys, and confirm
`filename_format` contains `{counter}`. Unknown keys are intentionally rejected.

## A cloud provider is disabled

Confirm `local_only: false` was intentional. Set the provider credential in the
same process that runs PhotoSage, then rerun `photosage doctor`. Provider variables
are `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY`, `MOONSHOT_API_KEY`, and
`OPENAI_API_KEY`. Never put them in command arguments or YAML.

## Local endpoint is rejected

Loopback endpoints work by default. A LAN server needs an exact
`endpoint_allowlist` entry and HTTPS. If a trusted LAN service only supports HTTP,
`allow_insecure_lan_endpoint: true` is a separate explicit risk acceptance.
Public addresses and redirects remain blocked.

## Ollama or LM Studio is unavailable

```powershell
photosage ollama info
photosage ollama models
photosage doctor --config .\config.yaml
```

Confirm the service is listening and the configured vision model is installed.
For LM Studio, start its local API server and use its exact model identifier. A
text-only model cannot analyze images.

## Kimi fails

```powershell
Get-Item Env:MOONSHOT_API_KEY
photosage doctor --config .\config.yaml
```

Do not print the variable value. Common causes are a missing key,
`local_only: true`, an unavailable model, a short timeout, or a low completion
limit. PhotoSage only accepts the official global Kimi endpoint. See
[Kimi Provider](kimi-provider.md).

## Preview contains poor names

Do not apply it. Check extracted metadata, the score, active provider/model,
`metadata_threshold`, and `filename_format`. Approve, reject, or edit entries in
review. Use a small representative test directory first. Keep `{counter}` in the
format because it is part of collision prevention.

## Apply reports `source-changed`

The source no longer matches the preview fingerprint. Another application may
have edited content, metadata, timestamp, or size. Do not modify the manifest.
Generate and review a new preview.

## Apply reports `overwrite-prevented`

The proposed destination already exists. PhotoSage did not replace it. Inspect
both files, resolve the conflict outside the active transaction, and create a new
preview. Matching names do not prove matching content.

## Run was interrupted

Inspect before rerunning anything:

```powershell
photosage recover --manifest .\manifests\apply-manifest.json
```

Resolve `collision`, `source-changed`, `destination-changed`, and `missing`
states. Resume only verified ready entries, or roll back. See
[Recovery and Review](recovery-and-review.md).

## Manifest checksum fails

The manifest was edited, truncated, or corrupted. Preserve it, find a known-good
backup, and do not recompute the checksum by hand. If no trusted manifest exists,
reconcile the filesystem manually from backups.

## Undo reports a collision

The original path is occupied, so PhotoSage will not overwrite it. Compare the
current file, renamed file, and manifest fingerprints. Move anything only after
verifying ownership and content.

## XMP sidecar warning

The media file and `.xmp` sidecar are missing a partner or the proposed sidecar
destination exists. Restore the pair and create a new preview. Avoid concurrent
catalog edits during apply, recovery, or undo.

## Video metadata is incomplete

Video probing depends on FFmpeg tools:

```powershell
ffprobe -version
Get-Command ffprobe
```

Restart the terminal after changing `PATH`.

## Search returns no results

```powershell
photosage search index --input C:\Photos --config .\config.yaml
photosage search query "sunset lake" --config .\config.yaml
```

Check `search_database`, `embedding_backend`, and the Ollama embedding model. The
hash backend is local and deterministic but less semantic than model embeddings.

## GUI does not start

Run the CLI health check, then launch the GUI from a terminal to capture a
sanitized error. Confirm GUI dependencies are installed and Windows has an
interactive desktop session. Do not post full logs because they may contain paths
and filenames.

## Catalog integration fails

Confirm the configured PhotoSage executable and target directory. Run the
equivalent CLI preview manually against a non-sensitive test folder. See
[Catalog Integrations](catalog-integrations.md) and
[Lightroom Integration](lightroom-integration.md).

## Release executable is blocked or unsigned

Do not bypass Windows security warnings. Verify the release SHA-256, Authenticode
signer, and provenance. Download again from the official release if any check
fails. Maintainers should follow [Packaging and Release](../packaging/README.md).

## Safe issue reports

Include the PhotoSage version, command, Windows/Python versions, provider/model,
exact sanitized error, and whether the run was preview, apply, recovery, or undo.

Exclude images, API keys, full manifests/logs, GPS coordinates, private filenames,
usernames, and absolute library paths unless a private support channel explicitly
requires them.
