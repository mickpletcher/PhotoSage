# Plan: LM Studio Provider

## Implementation Approach

Add LM Studio as another provider under the existing provider abstraction.

Do not create a separate pipeline. LM Studio should plug into the same provider factory, provider manager, response normalizer, retry handler, health check, CLI, and config flow used by the other providers.

## Files To Change

Provider system:

- `src/photosage/providers/lmstudio_provider.py`
- `src/photosage/providers/provider_factory.py`
- `src/photosage/providers/provider_manager.py`
- `src/photosage/providers/healthcheck.py`
- `src/photosage/providers/__init__.py`

Configuration and CLI:

- `config/settings.yaml`
- `src/photosage/config.py`
- `src/photosage/cli.py`

Docs:

- `README.md`
- `CHANGELOG.md`
- `assessment.md`

Tests:

- `tests/test_lmstudio_provider.py`
- `tests/test_provider_factory.py`
- `tests/test_provider_fallback.py`
- `tests/test_provider_healthcheck.py`
- `tests/test_local_only_mode.py`

## Data Flow

1. CLI or config selects `lmstudio`.
2. Provider factory creates `LMStudioProvider`.
3. Provider reads endpoint, model, timeout, temperature, and image preprocessing settings.
4. Provider preprocesses image locally when needed.
5. Provider sends image and metadata prompt to LM Studio's local OpenAI-compatible endpoint.
6. Provider parses model response.
7. Response normalizer validates and fills the standard schema.
8. Provider manager returns normalized image understanding data to the caller.
9. Filename generation remains outside the provider.

## API Shape

Expected default endpoint:

```text
http://localhost:1234/v1
```

Expected health endpoint:

```text
GET /v1/models
```

Expected inference endpoint:

```text
POST /v1/chat/completions
```

LM Studio should use a local placeholder API key only if the client requires an authorization value.

## Image Handling

Reuse the Ollama image preprocessing approach where possible:

- Read local image with Pillow.
- Convert unsupported modes to RGB.
- Resize to configured `max_dimension`.
- Encode as JPEG or PNG.
- Do not log image bytes.

## Error Handling

Treat these as retryable:

- Connection reset
- Local server temporarily unavailable
- Timeout
- Invalid JSON response
- Empty response content

Treat these as non-retryable:

- Missing model setting
- Unsupported provider name
- Invalid endpoint configuration
- Model not found response

## Local Only Policy

LM Studio is local.

When `local_only: true`:

- LM Studio is allowed.
- Ollama is allowed.
- Anthropic, OpenAI, and Gemini are blocked.
- Fallback must not jump from LM Studio to a cloud provider.

## Verification

Run:

```powershell
python -m pytest
```

Manual checks:

```powershell
$env:PYTHONPATH='src'
python -m photosage.cli providers
python -m photosage.cli scan --input ./photos --provider lmstudio --local-only
```

Manual LM Studio checks require the local LM Studio server and a vision-capable model loaded.

## Risks

- LM Studio model names and image support vary by installed model.
- Some local models may return markdown or invalid JSON.
- Users may select text-only models and expect image classification.
- Large image payloads can be slow or fail on small systems.

Mitigations:

- Validate models through health checks.
- Keep response normalization strict.
- Add useful error messages for missing or incompatible models.
- Keep image preprocessing configurable.
