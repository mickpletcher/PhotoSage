# Kimi Provider

PhotoSage supports Moonshot AI's Kimi API as an opt-in cloud vision provider.
The integration uses Kimi's OpenAI-compatible chat completion interface and the
official global endpoint.

Kimi is disabled when `local_only` is true. Selecting Kimi sends the image and
an allowlisted metadata subset to Moonshot AI.

## Prerequisites

1. Create a key in the Moonshot AI platform.
2. Store it in `MOONSHOT_API_KEY`.
3. Set `local_only: false`.
4. Select `kimi` as the provider or add it to the fallback order.

PowerShell session setup:

```powershell
$env:MOONSHOT_API_KEY = Read-Host "Moonshot API key" -MaskInput
```

Do not add the key to `config.yaml`, command history, logs, manifests, screenshots,
or issue reports.

## Minimal configuration

```yaml
local_only: false
vision_provider: kimi
provider_settings:
  kimi:
    model: kimi-k3
    reasoning_effort: low
    max_completion_tokens: 1200
    timeout_seconds: 180
```

Validate and check readiness:

```powershell
photosage config validate --config .\config.yaml
photosage doctor --config .\config.yaml
photosage providers --config .\config.yaml
```

The readiness check verifies configuration and credential presence. It does not
submit a billable image analysis request.

## Model behavior

The default model is `kimi-k3`.

K3 always uses reasoning. Configure `reasoning_effort` as `low`, `high`, or
`max`. PhotoSage omits temperature for K3 because that model controls its own
reasoning behavior.

For configured K2.5 and K2.6 models, `thinking` may be `enabled` or `disabled`.
PhotoSage omits temperature when thinking is enabled. Model availability and
exact identifiers are account and API concerns. Confirm them in Moonshot AI's
current documentation before changing the default.

## Request contract

For each analysis request, PhotoSage:

1. Loads and normalizes the selected image.
2. Encodes the image as a base64 `image_url` content item.
3. Adds an instruction requesting the PhotoSage analysis schema.
4. Adds only the allowed metadata fields.
5. Requests a JSON object response.
6. Validates the returned JSON before using any suggestion.

Public image URLs are not used. The fixed API base URL is:

```text
https://api.moonshot.ai/v1
```

PhotoSage rejects a different `base_url`. This prevents a Kimi credential from
being redirected to an arbitrary OpenAI-compatible server.

## Data sent to Moonshot AI

The image itself is sent because Kimi must inspect it. Technical metadata may
also be sent. Paths, absolute paths, raw metadata collections, GPS data, OCR
text, titles, descriptions, and keywords are excluded by default.

Before enabling sensitive metadata:

1. Review the provider's data handling terms.
2. Confirm the images are allowed to leave the device.
3. Restrict `metadata_fields` to the smallest required set.
4. Run a preview and inspect local logs and manifests.

If cloud transfer is not acceptable, keep `local_only: true` and use Ollama, LM
Studio, or another approved local endpoint.

## Retry and fallback

`provider_retry_count` controls attempts against Kimi. The first retry delay is
`provider_retry_initial_delay`; later attempts back off.

Fallback is explicit and ordered:

```yaml
local_only: false
vision_provider: kimi
fallback_order:
  - ollama
  - lmstudio
```

If Kimi is unavailable or returns invalid analysis data, PhotoSage records the
failure and tries the next allowed provider. A fallback provider's privacy rules
still apply. PhotoSage does not silently enable a cloud provider that conflicts
with `local_only`.

## Safe verification

Use a non-sensitive test image:

```powershell
photosage preview --input C:\Photos\Test --config .\config.yaml
```

Confirm the preview manifest reports `kimi` as the provider. Inspect suggested
names and confidence values. Do not apply until the preview is correct.

For broader comparison:

```powershell
photosage benchmark providers --input C:\Photos\Test --provider kimi --allow-cloud --config .\config.yaml
```

Benchmarking can create chargeable requests for every enabled cloud provider.

## Error diagnosis

| Symptom | Likely cause | Action |
| --- | --- | --- |
| `MOONSHOT_API_KEY` is missing | Credential is not set in the current process | Set the environment variable in the same PowerShell session and rerun `photosage doctor`. |
| Kimi is blocked while the key exists | `local_only` is still true | Keep local mode or explicitly set `local_only: false` after reviewing the privacy impact. |
| Invalid `base_url` | Configuration points away from the official global endpoint | Remove `base_url` or restore `https://api.moonshot.ai/v1`. |
| Authentication error | Invalid, revoked, or unauthorized key | Replace the key in the environment. Do not paste it into logs or an issue. |
| Timeout | Large image, slow connection, provider load, or short timeout | Retry a small test image, check connectivity, then increase `timeout_seconds` if justified. |
| Truncated response | Completion limit is too low | Increase `max_completion_tokens` for K3 or `max_tokens` for other models. |
| Invalid JSON or empty response | Provider did not satisfy the analysis contract | Retry, inspect the sanitized error, and use an explicit fallback. |
| Model not found | Model identifier is unavailable to the account | Restore `kimi-k3` or use a model identifier shown by the current Moonshot AI documentation/account. |

## Credential cleanup

Remove a session-scoped key when finished:

```powershell
Remove-Item Env:MOONSHOT_API_KEY
```

If a key was committed, printed in CI, or included in a support artifact, revoke
it immediately and remove it from the exposed system. Deleting it from the latest
Git commit is not sufficient because history and logs may retain it.

## Official references

- [Kimi API quickstart](https://platform.kimi.ai/docs/overview)
- [Kimi vision guide](https://platform.kimi.ai/docs/guide/use-kimi-vision-model)
- [Kimi API errors](https://platform.kimi.ai/docs/api/errors)
- [Kimi API pricing](https://platform.kimi.ai/docs/pricing/chat)
