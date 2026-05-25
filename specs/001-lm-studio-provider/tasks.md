# Tasks: LM Studio Provider

## 1. Config

- [ ] Add `lmstudio` settings to `config/settings.yaml`.
- [ ] Add `lmstudio` to default fallback examples where appropriate.
- [ ] Ensure `AppConfig.provider_settings` includes `lmstudio`.
- [ ] Add `lmstudio` to CLI supported provider values.

## 2. Provider Implementation

- [ ] Create `src/photosage/providers/lmstudio_provider.py`.
- [ ] Inherit from `VisionProvider`.
- [ ] Implement image preprocessing with Pillow.
- [ ] Build OpenAI-compatible chat completion payloads.
- [ ] Include metadata context in the prompt.
- [ ] Parse response content safely.
- [ ] Normalize response through `response_normalizer.py`.
- [ ] Raise standardized provider exceptions.

## 3. Provider Registration

- [ ] Register `lmstudio` in `provider_factory.py`.
- [ ] Confirm provider manager fallback works with `lmstudio`.
- [ ] Confirm `local_only` allows LM Studio.
- [ ] Confirm cloud fallback is blocked in local-only mode.

## 4. Health Checks

- [ ] Add LM Studio health check support.
- [ ] Query `/v1/models`.
- [ ] Show endpoint and configured model in `photosage providers`.
- [ ] Return useful messages for unreachable server and missing model.

## 5. CLI

- [ ] Accept `--provider lmstudio`.
- [ ] Confirm scan and preview commands accept LM Studio.
- [ ] Confirm provider status output includes LM Studio.

## 6. Tests

- [ ] Add `tests/test_lmstudio_provider.py`.
- [ ] Test normalized response output.
- [ ] Test malformed JSON retry or repair.
- [ ] Test endpoint unavailable handling.
- [ ] Test provider factory selection.
- [ ] Test local-only enforcement.
- [ ] Test health check model listing.
- [ ] Run `python -m pytest`.

## 7. Documentation

- [ ] Update `README.md` with LM Studio setup.
- [ ] Update `CHANGELOG.md`.
- [ ] Update `assessment.md` after implementation.
- [ ] Document example config.
- [ ] Document vision-capable model requirement.

## 8. Acceptance

- [ ] `photosage providers` shows LM Studio.
- [ ] `photosage scan --input ./photos --provider lmstudio --local-only` accepts provider config.
- [ ] Full test suite passes.
- [ ] No provider code renames or moves files.
- [ ] No cloud provider is used when local-only mode is enabled.
