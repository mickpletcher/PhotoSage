# Spec: LM Studio Provider

## Status

Draft

## Objective

Add LM Studio as a local vision provider for PhotoSage.

LM Studio should let users run local multimodal models through its OpenAI-compatible API while preserving PhotoSage's metadata-first architecture, safe rename model, and provider-agnostic response contract.

## User Workflow

Users should be able to configure PhotoSage like this:

```yaml
vision_provider: lmstudio
local_only: true

fallback_order:
  - lmstudio
  - ollama

lmstudio:
  endpoint: http://localhost:1234/v1
  model: qwen2.5-vl-7b-instruct
  timeout_seconds: 180
  temperature: 0.1
  max_dimension: 1600
  jpeg_quality: 90
```

Then run:

```powershell
photosage providers
photosage scan --input ./photos --provider lmstudio --local-only
photosage preview --input ./photos --provider lmstudio --local-only
```

## Requirements

- Add `lmstudio` as a supported provider name.
- Add `src/photosage/providers/lmstudio_provider.py`.
- Use LM Studio's OpenAI-compatible local API.
- Default endpoint should be `http://localhost:1234/v1`.
- Load provider settings from `config/settings.yaml`.
- Support configurable model, timeout, temperature, resize limit, and JPEG quality.
- Encode local images safely for the request.
- Send metadata context with the image.
- Reuse the existing image classification prompt requirements.
- Normalize responses into the existing provider schema.
- Retry invalid JSON and transient local server failures.
- Do not retry invalid configuration or unsupported model errors.
- Add health checks using the local models endpoint.
- Show LM Studio in `photosage providers`.
- Enforce `local_only: true` correctly.
- Keep fallback behavior provider agnostic.

## Response Contract

LM Studio responses must normalize to:

```json
{
  "primary_subject": "string",
  "secondary_subject": "string",
  "activity": "string",
  "environment": "string",
  "location_guess": "string",
  "confidence": 0.0,
  "tags": [],
  "description": "string",
  "provider": "lmstudio",
  "model": "string"
}
```

## Non-Goals

- Do not add rename logic to the provider.
- Do not bypass metadata scoring.
- Do not require LM Studio for normal metadata-only workflows.
- Do not add a GUI-specific implementation.
- Do not cache image bytes.
- Do not add cloud fallback when `local_only: true`.

## Safety Requirements

- LM Studio must be treated as a local provider.
- Images must not be sent to cloud providers when `local_only: true`.
- API keys must not be required for LM Studio.
- Logs must not include image bytes, base64 data, or secrets.
- Provider failures must not cause files to be renamed.

## Tests

Add pytest coverage for:

- Provider factory supports `lmstudio`.
- Local-only mode permits LM Studio.
- Local-only mode blocks cloud fallback after LM Studio failure.
- Health check handles reachable and unreachable LM Studio endpoints.
- Model listing parses `/v1/models`.
- Malformed JSON response is repaired or retried.
- Timeout and connection failure are reported cleanly.
- Normalized response matches the provider contract.

## Documentation

Update:

- `README.md`
- `CHANGELOG.md`
- `config/settings.yaml`
- `.env.example` only if needed, but LM Studio should not require an API key.

## Acceptance Criteria

- `photosage providers` shows LM Studio status.
- `--provider lmstudio` is accepted by CLI commands.
- `local_only: true` allows LM Studio and blocks cloud providers.
- Invalid LM Studio responses do not escape normalization.
- Existing provider tests still pass.
- Full test suite passes with `python -m pytest`.
