# Tasks: LM Studio Provider

## 1. Config

- [x] Add `lmstudio` settings to `config/settings.yaml`.
- [x] Add `lmstudio` to default fallback examples where appropriate.
- [x] Ensure `AppConfig.provider_settings` includes `lmstudio`.
- [x] Add `lmstudio` to CLI supported provider values.

## 2. Provider Implementation

- [x] Create `src/photosage/providers/lmstudio_provider.py`.
- [x] Inherit from `VisionProvider`.
- [x] Implement image preprocessing with Pillow.
- [x] Build OpenAI-compatible chat completion payloads.
- [x] Include metadata context in the prompt.
- [x] Parse response content safely.
- [x] Normalize response through `response_normalizer.py`.
- [x] Raise standardized provider exceptions.

## 3. Provider Registration

- [x] Register `lmstudio` in `provider_factory.py`.
- [x] Confirm provider manager fallback works with `lmstudio`.
- [x] Confirm `local_only` allows LM Studio.
- [x] Confirm cloud fallback is blocked in local-only mode.

## 4. Health Checks

- [x] Add LM Studio health check support.
- [x] Query `/v1/models`.
- [x] Show endpoint and configured model in `photosage providers`.
- [x] Return useful messages for unreachable server and missing model.

## 5. CLI

- [x] Accept `--provider lmstudio`.
- [x] Confirm scan and preview commands accept LM Studio.
- [x] Confirm provider status output includes LM Studio.

## 6. Tests

- [x] Add `tests/test_lmstudio_provider.py`.
- [x] Test normalized response output.
- [x] Test malformed JSON retry or repair.
- [x] Test endpoint unavailable handling.
- [x] Test provider factory selection.
- [x] Test local-only enforcement.
- [x] Test health check model listing.
- [x] Run `python -m pytest`.

## 7. Documentation

- [x] Update `README.md` with LM Studio setup.
- [x] Update `CHANGELOG.md`.
- [x] Update `assessment.md` after implementation.
- [x] Document example config.
- [x] Document vision-capable model requirement.

## 8. Acceptance

- [x] `photosage providers` shows LM Studio.
- [x] `photosage scan --input ./photos --provider lmstudio --local-only` accepts provider config.
- [x] Full test suite passes.
- [x] No provider code renames or moves files.
- [x] No cloud provider is used when local-only mode is enabled.
