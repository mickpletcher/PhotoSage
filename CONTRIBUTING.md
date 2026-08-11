# Contributing to PhotoSage

Changes must preserve the local-first privacy boundary and transactional rename
guarantees. A feature is incomplete until its tests and documentation pass.

## Development setup

```powershell
git clone https://github.com/OWNER/PhotoSage.git
Set-Location .\PhotoSage
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Use Python 3.11 or the version declared by project metadata. Use the locked
environment for final verification when the repository provides one.

## Working rules

- Keep preview as the default for filesystem changes.
- Never overwrite a destination.
- Preserve fingerprint checks, journaling, recovery, and undo.
- Keep cloud processing opt-in through `local_only: false`.
- Keep secrets out of config, logs, manifests, exceptions, fixtures, and docs.
- Keep runtime artifacts and private photo data out of Git.
- Do not weaken endpoint allowlisting or redirect protections.
- Reject unknown configuration instead of silently ignoring it.

## Quality gate

```powershell
python -m ruff check src tests scripts
python -m ruff format --check src tests scripts
python -m pyright src
python -m coverage run -m pytest
python -m coverage report
python scripts\check_docs.py
python scripts\generate_cli_reference.py --check
python -m pip_audit -r requirements.lock --progress-spinner off
python -m build
python -m twine check dist\*
```

New behavior requires tests for success, validation errors, failure handling, and
privacy boundaries.

## Documentation contract

The CLI reference comes from the live Typer command tree:

```powershell
python scripts\generate_cli_reference.py
```

Commit the generated `docs/cli-reference.md` with every CLI change. Do not edit
that file by hand. Configuration changes also require an update to
`docs/configuration-reference.md`; the docs checker verifies every `AppConfig`
field and provider name appears there.

Update the closest task guide for behavior changes. Keep `README.md` focused on
the main workflow and documentation navigation.

## Adding a provider

A provider change requires:

1. The common analysis result contract.
2. Provider factory and configuration registration.
3. A non-chargeable readiness check where possible.
4. CLI and GUI selection where applicable.
5. Environment-based credentials and redacted errors.
6. Retry, timeout, malformed response, and fallback tests.
7. Local/cloud policy and endpoint safety tests.
8. Configuration, privacy, troubleshooting, and provider documentation.

Cloud providers use conservative metadata filtering. Local-compatible endpoints
use the shared endpoint validator.

## Changing rename behavior

Every mutation path needs a durable pre-change plan, source identity verification,
no-overwrite protection, a pre-mutation journal checkpoint, result verification,
recovery classification, and safe undo. Do not mutate files directly from CLI or
GUI handlers.

## Tests

Use temporary directories and synthetic media. Tests must not read personal
libraries, user profiles, or real API keys. Mock network clients unless a test is
explicitly isolated as an integration test.

Provider tests must assert outbound payloads exclude paths, raw metadata, GPS,
OCR, and secrets by default.

## Pull requests

Keep a pull request scoped. State the visible behavior, safety/privacy impact,
commands run, and documentation updated. Use only sanitized screenshots.

Do not commit `manifests/`, `logs/`, `.photosage-cache/`, API keys, local config,
personal images, search databases, signing certificates, or build outputs.
