# Spec: LM Studio Provider

## Goal

Add LM Studio as a local vision provider.

LM Studio should work like Ollama: local, privacy-friendly, and provider-agnostic.

## User Story

As a PhotoSage user, I want to use a local LM Studio vision model so I can classify photos without sending images to a cloud provider.

## Example Config

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

## User Commands

```powershell
photosage providers
photosage scan --input ./photos --provider lmstudio --local-only
photosage preview --input ./photos --provider lmstudio --local-only
```

## Requirements

- Add `lmstudio` as a provider.
- Add `src/photosage/providers/lmstudio_provider.py`.
- Use LM Studio's OpenAI-compatible local API.
- Default endpoint: `http://localhost:1234/v1`.
- Read settings from `config/settings.yaml`.
- Support model, timeout, temperature, resize limit, and JPEG quality.
- Send image data and metadata context to LM Studio.
- Normalize responses into the existing PhotoSage provider schema.
- Retry invalid JSON and transient local server failures.
- Add health checks using `/v1/models`.
- Show LM Studio in `photosage providers`.
- Respect `local_only: true`.

## Response Contract

Every response must become:

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

## Out Of Scope

- Do not add rename logic to the provider.
- Do not bypass metadata scoring.
- Do not require LM Studio for metadata-only workflows.
- Do not cache image bytes.
- Do not allow cloud fallback when `local_only: true`.

## Safety Rules

- LM Studio is local.
- No API key should be required.
- Do not log image bytes or base64 data.
- Do not log secrets.
- Provider failure must not rename files.

## Tests Required

- Provider factory creates LM Studio.
- Local-only mode allows LM Studio.
- Local-only mode blocks cloud fallback.
- Health check handles reachable and unreachable endpoints.
- `/v1/models` response is parsed.
- Bad JSON is repaired or retried.
- Timeouts produce clear errors.
- Output matches the provider schema.

## Acceptance Criteria

- `--provider lmstudio` works.
- `photosage providers` shows LM Studio.
- `local_only: true` allows LM Studio and blocks cloud providers.
- Invalid model output does not escape normalization.
- `python -m pytest` passes.
