# Plan: LM Studio Provider

## Approach

Add LM Studio to the existing provider system.

Do not create a new workflow. Use the same factory, manager, retry handler, response normalizer, health checks, CLI options, and config patterns already used by other providers.

## Files To Change

Provider files:

- `src/photosage/providers/lmstudio_provider.py`
- `src/photosage/providers/provider_factory.py`
- `src/photosage/providers/provider_manager.py`
- `src/photosage/providers/healthcheck.py`
- `src/photosage/providers/__init__.py`

Config and CLI:

- `config/settings.yaml`
- `src/photosage/config.py`
- `src/photosage/cli.py`

Docs and tests:

- `README.md`
- `CHANGELOG.md`
- `assessment.md`
- `tests/test_lmstudio_provider.py`
- Existing provider tests as needed

## Data Flow

1. User selects `lmstudio`.
2. Provider factory creates `LMStudioProvider`.
3. Provider reads endpoint, model, timeout, and image settings.
4. Provider prepares the local image.
5. Provider sends image plus metadata to LM Studio.
6. Provider parses the model response.
7. Response normalizer enforces the schema.
8. Filename generation happens elsewhere.

## LM Studio API

Default base URL:

```text
http://localhost:1234/v1
```

Health check:

```text
GET /v1/models
```

Image analysis:

```text
POST /v1/chat/completions
```

## Image Handling

- Read with Pillow.
- Convert to RGB when needed.
- Resize to `max_dimension`.
- Encode safely.
- Do not log image bytes.

## Retry Rules

Retry:

- Timeout
- Connection reset
- Temporary local server failure
- Empty response
- Invalid JSON

Do not retry:

- Bad provider name
- Bad endpoint config
- Missing model setting
- Model not found

## Local-Only Behavior

When `local_only: true`:

- LM Studio is allowed.
- Ollama is allowed.
- Anthropic, OpenAI, and Gemini are blocked.
- Fallback must not jump from local providers to cloud providers.

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

Manual LM Studio checks require LM Studio running with a vision-capable model loaded.
