## Summary

Describe the user-visible change and why it is needed.

## Safety and privacy

- [ ] Preview remains the default for filesystem changes.
- [ ] Existing files cannot be overwritten.
- [ ] Manifest, recovery, and undo guarantees are preserved.
- [ ] Cloud processing remains explicit and opt-in.
- [ ] No credentials, personal media, private paths, manifests, logs, or provider responses are included.

Explain any safety or privacy impact that is not covered above.

## Validation

- [ ] Tests added or updated where behavior changed.
- [ ] `python -m ruff check src tests scripts`
- [ ] `python -m ruff format --check src tests scripts`
- [ ] `python -m pyright src`
- [ ] `python -m coverage run -m pytest && python -m coverage report`
- [ ] `python scripts/check_docs.py`
- [ ] `python -m pip_audit -r requirements.lock --progress-spinner off`
- [ ] `python -m build && python -m twine check dist/*`

List any intentionally skipped checks and why.

## Documentation

List the README, generated reference, configuration guide, changelog, or other documentation updated by this change.
