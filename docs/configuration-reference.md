# Configuration Reference

PhotoSage reads YAML configuration from `config.yaml` by default. Pass another
file with `--config PATH` on commands that accept it.

Validate a configuration before processing photos:

```powershell
photosage config validate --config .\config.yaml
```

Unknown top-level keys are rejected. Invalid values stop execution before any
files are changed.

## Complete example

```yaml
vision_provider: ollama
metadata_threshold: 70
dry_run_default: true
local_only: true
fallback_order:
  - ollama
  - lmstudio
filename_format: "{date}_{location}_{subject}_{context}_{counter}"
manifest_directory: manifests
log_file: logs/photosage.log
provider_retry_count: 3
provider_retry_initial_delay: 0.5
recursive_scanning: true
thumbnail_size: 128
log_level: INFO
max_concurrent_ai_requests: 2
watch_folders: []
watch_stable_seconds: 5.0
duplicate_hash_distance: 5
detect_duplicates_during_rename: false
geocode_cache_file: .photosage-cache/geocode_cache.json
geocode_cache_ttl_days: 365
folder_policy: date-first
folder_keyword_map: {}
thumbnail_cache_directory: .photosage-cache/thumbnails
profile_directory: .photosage-cache/profiles
recent_manifest_file: .photosage-cache/recent_manifests.json
astro_profile: deep-sky
astro_group_by_capture_night: true
review_confidence_threshold: 0.7
require_manual_review_for_ai: true
search_database: .photosage-cache/search.sqlite3
embedding_backend: hash
embedding_model: nomic-embed-text
provider_settings:
  ollama:
    endpoint: http://127.0.0.1:11434
    model: llava
```

All paths are resolved according to the command and current working directory.
Use explicit absolute paths in unattended jobs.

## Core settings

| Setting | Default | Allowed values and behavior |
| --- | --- | --- |
| `vision_provider` | `ollama` | `ollama`, `lmstudio`, `openai_compatible_local`, `anthropic`, `openai`, `gemini`, or `kimi` |
| `metadata_threshold` | `70` | Integer from 0 through 100. Files below this metadata score can be sent to the configured AI provider. |
| `dry_run_default` | `true` | When true, rename processing writes a preview manifest and does not rename files unless apply mode is explicitly selected. |
| `local_only` | `true` | Blocks cloud providers when true. Set it to false deliberately before using Anthropic, Gemini, Kimi, or OpenAI. |
| `fallback_order` | `[ollama, lmstudio]` | Ordered provider names tried after the primary provider fails. Unknown names are rejected. |
| `filename_format` | `{date}_{location}_{subject}_{context}_{counter}` | Filename template. It must contain `{counter}` to prevent accidental collisions. |
| `manifest_directory` | `manifests` | Directory for preview, apply, and recovery manifests. |
| `log_file` | `logs/photosage.log` | Application log path. Logs are local artifacts and may contain filenames. |
| `provider_settings` | `{}` | Mapping of provider names to provider-specific settings. See below. |
| `provider_retry_count` | `3` | Attempts per provider. Must be at least 1. |
| `provider_retry_initial_delay` | `0.5` | Initial retry delay in seconds. Must be zero or greater. Retries use backoff. |
| `recursive_scanning` | `true` | Includes supported files in subdirectories. |
| `thumbnail_size` | `128` | Thumbnail edge size from 32 through 2048 pixels. |
| `log_level` | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR`, or `CRITICAL`. |
| `max_concurrent_ai_requests` | `2` | Maximum simultaneous provider requests. Must be at least 1. |

## Automation and duplicate settings

| Setting | Default | Allowed values and behavior |
| --- | --- | --- |
| `watch_folders` | `[]` | Directories monitored by `photosage watch`. Use absolute paths for scheduled jobs. |
| `watch_stable_seconds` | `5.0` | Time a file must remain unchanged before processing. Must be zero or greater. |
| `duplicate_hash_distance` | `5` | Perceptual hash distance from 0 through 64. Lower values require closer visual similarity. |
| `detect_duplicates_during_rename` | `false` | Adds duplicate findings to rename previews when enabled. Duplicate groups require review. |

## Location, organization, and cache settings

| Setting | Default | Allowed values and behavior |
| --- | --- | --- |
| `geocode_cache_file` | `.photosage-cache/geocode_cache.json` | Local reverse-geocoding cache. It can contain sensitive location data. |
| `geocode_cache_ttl_days` | `365` | Cache lifetime in days. Must be zero or greater. |
| `folder_policy` | `date-first` | `date-first`, `location-first`, `project-first`, or `custom`. |
| `folder_keyword_map` | `{}` | Mapping used by custom organization rules. |
| `thumbnail_cache_directory` | `.photosage-cache/thumbnails` | Generated thumbnail cache. |
| `profile_directory` | `.photosage-cache/profiles` | Local profile storage. |
| `recent_manifest_file` | `.photosage-cache/recent_manifests.json` | GUI and CLI recent-manifest index. |

## Astrophotography settings

| Setting | Default | Allowed values and behavior |
| --- | --- | --- |
| `astro_profile` | `deep-sky` | `lunar`, `solar`, `planetary`, or `deep-sky`. |
| `astro_group_by_capture_night` | `true` | Groups sessions by capture night when applicable. |

## Review and search settings

| Setting | Default | Allowed values and behavior |
| --- | --- | --- |
| `review_confidence_threshold` | `0.7` | AI suggestions below this value require manual review. Range 0 through 1. |
| `require_manual_review_for_ai` | `true` | Requires approval of low-confidence AI suggestions before apply. Keep this enabled for unattended workflows. |
| `search_database` | `.photosage-cache/search.sqlite3` | Local semantic search database. It may contain filenames and extracted metadata. |
| `embedding_backend` | `hash` | `hash` for deterministic local embeddings or `ollama` for a configured local Ollama embedding model. |
| `embedding_model` | `nomic-embed-text` | Ollama model name when `embedding_backend` is `ollama`. |

## Filename tokens

`filename_format` supports these tokens:

| Category | Tokens |
| --- | --- |
| General | `{date}`, `{location}`, `{subject}`, `{context}`, `{counter}` |
| Documents | `{app}`, `{document_type}`, `{media_type}`, `{ocr_summary}` |
| Astronomy | `{astro_profile}`, `{astro_target}`, `{telescope}`, `{filter}`, `{exposure}`, `{capture_night}`, `{session}` |
| Video | `{duration}`, `{codec}` |

`{counter}` is mandatory. PhotoSage sanitizes generated names and preserves the
original extension. Preview the result before apply.

## Common provider settings

Provider-specific options belong below `provider_settings.<provider>`.

```yaml
provider_settings:
  openai:
    model: gpt-4.1-mini
    include_sensitive_metadata: false
    metadata_fields:
      - camera_make
      - camera_model
```

The following options are common where the provider supports them:

| Setting | Behavior |
| --- | --- |
| `model` | Model identifier sent to the provider. |
| `include_sensitive_metadata` | Opts into sending sensitive metadata. The default is false. Review the privacy impact first. |
| `metadata_fields` | Explicit metadata keys to include. This narrows the default allowlist; it does not bypass blocked path data. |

Cloud provider credentials are read from environment variables. Do not place API
keys in YAML:

| Provider | Environment variable |
| --- | --- |
| `anthropic` | `ANTHROPIC_API_KEY` |
| `openai` | `OPENAI_API_KEY` |
| `gemini` | `GOOGLE_API_KEY` |
| `kimi` | `MOONSHOT_API_KEY` |

## Local provider settings

Ollama example:

```yaml
provider_settings:
  ollama:
    endpoint: http://127.0.0.1:11434
    model: llava
    healthcheck_timeout_seconds: 5
    timeout_seconds: 180
    temperature: 0.1
    max_dimension: 1600
    jpeg_quality: 90
```

LM Studio example:

```yaml
provider_settings:
  lmstudio:
    endpoint: http://127.0.0.1:1234/v1
    model: local-vision-model
```

Generic OpenAI-compatible local endpoint example:

```yaml
provider_settings:
  openai_compatible_local:
    endpoint: http://127.0.0.1:8000/v1
    model: local-vision-model
```

Local provider options include:

| Setting | Behavior |
| --- | --- |
| `endpoint` | API base URL. Loopback addresses are allowed by default. |
| `model` | Installed model identifier. |
| `healthcheck_timeout_seconds` | Timeout for readiness checks. |
| `timeout_seconds` | Analysis request timeout. |
| `temperature` | Sampling temperature where supported. |
| `max_dimension` | Maximum image edge before upload to the local provider. |
| `jpeg_quality` | JPEG conversion quality used for provider input. |
| `endpoint_allowlist` | Exact non-loopback endpoint URLs explicitly permitted. Must be a list of strings. |
| `allow_insecure_lan_endpoint` | Allows allowlisted LAN endpoints over HTTP. Default false. |
| `allow_sensitive_embeddings` | Permits sensitive data in local embedding requests. Default false. |

Loopback endpoints are allowed by default. Public endpoints are blocked. A LAN
endpoint must be an exact member of `endpoint_allowlist` and must use HTTPS unless
`allow_insecure_lan_endpoint` is explicitly true. Redirects are disabled.

## Kimi settings

```yaml
local_only: false
vision_provider: kimi
provider_settings:
  kimi:
    model: kimi-k3
    timeout_seconds: 180
    reasoning_effort: high
    max_completion_tokens: 1200
```

| Setting | Behavior |
| --- | --- |
| `model` | Defaults to `kimi-k3`. Vision-capable Kimi K2.5 and K2.6 identifiers may also be configured. |
| `base_url` | Fixed to the official global API endpoint `https://api.moonshot.ai/v1`. Other values are rejected. |
| `timeout_seconds` | Request timeout. Default 180 seconds. |
| `reasoning_effort` | K3 reasoning setting: `low`, `high`, or `max`. Default `low`. |
| `max_completion_tokens` | Completion limit used for K3 models. Default 1200. |
| `max_tokens` | Completion limit used for other supported Kimi models. Default 1200. |
| `thinking` | For K2.5 and K2.6, `enabled` or `disabled`. Omit to use the model default. |

See [Kimi Provider](kimi-provider.md) for setup, request behavior, and failure
diagnosis.

## Metadata privacy boundary

Cloud requests use a conservative allowlist by default. Typical permitted values
are technical attributes such as extension, dimensions, camera and lens data,
exposure data, orientation, media type, codec, and non-location astronomy capture
settings.

PhotoSage excludes paths, raw metadata blobs, GPS coordinates, titles,
descriptions, OCR text, and keywords unless a documented setting explicitly opts
into the relevant data. Provider-bound images are still sent to the selected
cloud service. `local_only: true` is the hard stop for cloud use.

## Environment-specific files

Keep machine-specific configuration outside Git when it contains private paths,
endpoint names, or workflow details. Commit a sanitized example instead.

Recommended PowerShell pattern:

```powershell
$env:MOONSHOT_API_KEY = Read-Host "Moonshot API key" -MaskInput
photosage doctor --config .\config.yaml
photosage preview --input C:\Photos\Incoming --config .\config.yaml
Remove-Item Env:MOONSHOT_API_KEY
```

Use your normal secret manager for unattended jobs. Process-level environment
variables are preferable to plaintext scripts or scheduled-task arguments.
