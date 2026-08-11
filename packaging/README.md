# Windows Packaging and Release

The `Signed Windows Release` workflow builds signed CLI and GUI executables,
creates an SBOM and archive checksum, attests build provenance, and publishes a
GitHub release for a pushed `v*` tag. It fails closed when signing is unavailable
or invalid.

## Release outputs

The workflow publishes:

| Artifact | Contents or purpose |
| --- | --- |
| `PhotoSage-Windows.zip` | Signed CLI, signed GUI, SBOM, README, license, catalog integrations, and integration documentation. |
| `SHA256SUMS.txt` | SHA-256 for the ZIP archive. |
| GitHub build provenance | Attestation for the ZIP produced by GitHub Actions. |

The archive contains `PhotoSage.exe` and `PhotoSage-GUI.exe`. Both must have a
valid Authenticode signature before packaging continues.

## Workflow inputs

Configure these GitHub Actions secrets before creating a release tag:

| Secret | Value |
| --- | --- |
| `WINDOWS_SIGNING_CERTIFICATE_BASE64` | Base64 encoding of the code-signing PFX bytes. |
| `WINDOWS_SIGNING_CERTIFICATE_PASSWORD` | PFX password. |

Create the Base64 value locally in PowerShell:

```powershell
$pfxPath = 'C:\Secure\PhotoSage-CodeSigning.pfx'
$base64 = [Convert]::ToBase64String([IO.File]::ReadAllBytes($pfxPath))
$base64 | Set-Clipboard
Remove-Variable base64
```

Store the value directly as the GitHub secret, clear the clipboard, and keep the
PFX outside the repository. Do not print the certificate password or place it in
a shell script.

The certificate must support Windows code signing and chain to the intended trust
root. The workflow timestamps signatures through DigiCert so a valid timestamped
signature can remain verifiable after certificate expiration.

## Local preflight

Run the full repository gate before tagging:

```powershell
python -m pip install -r requirements.lock
python -m pip install --no-deps -e .
python -m ruff check src tests scripts
python -m ruff format --check src tests scripts
python -m pyright src
python -m coverage run -m pytest
python -m coverage report
python scripts\check_docs.py
python -m pip_audit -r requirements.lock --progress-spinner off
python -m build
python -m twine check dist\*
```

Build both specifications locally when changing packaging:

```powershell
pyinstaller --clean --noconfirm packaging\photosage-cli.spec
pyinstaller --clean --noconfirm packaging\photosage-gui.spec
.\dist\PhotoSage.exe --help
```

A local unsigned build is only a packaging test. Do not publish it as a release.

## Release procedure

1. Confirm the working tree contains only intended, reviewed changes.
2. Confirm version metadata and changelog are current.
3. Run the local preflight.
4. Confirm both signing secrets exist in the repository Actions settings.
5. Create a signed version tag and push it.
6. Watch the entire `Signed Windows Release` workflow.
7. Download the published ZIP and checksum from the release.
8. Verify checksum, Authenticode signatures, CLI smoke test, SBOM, and attestation
   on a clean Windows system.

Example tag commands after the release commit is on the intended branch:

```powershell
git tag -s v0.3.0 -m "PhotoSage v0.3.0"
git push origin v0.3.0
```

Use the actual release version. Do not reuse or move a published version tag.

## CI release stages

The workflow:

1. Checks out the tagged commit.
2. Installs Python 3.11 and `requirements.lock`.
3. Runs the test suite.
4. Builds CLI and GUI with PyInstaller specs.
5. Decodes the PFX in the runner's temporary directory.
6. Signs and verifies both executables.
7. Deletes the temporary PFX.
8. Smoke-tests the signed CLI.
9. Creates a reproducible CycloneDX JSON SBOM.
10. Packages executables, documentation, license, and integrations.
11. Computes the ZIP SHA-256.
12. Creates build provenance.
13. Uploads artifacts and publishes the GitHub release.

Any missing signing secret, invalid signature, failed test, failed build, or failed
smoke test stops publication.

## Verifying a downloaded release

```powershell
$releaseDir = 'C:\Downloads\PhotoSage-Release'
Set-Location $releaseDir
Get-FileHash .\PhotoSage-Windows.zip -Algorithm SHA256
Get-Content .\SHA256SUMS.txt
Expand-Archive .\PhotoSage-Windows.zip -DestinationPath .\expanded
Get-AuthenticodeSignature .\expanded\PhotoSage.exe | Format-List Status,SignerCertificate,TimeStamperCertificate
Get-AuthenticodeSignature .\expanded\PhotoSage-GUI.exe | Format-List Status,SignerCertificate,TimeStamperCertificate
.\expanded\PhotoSage.exe --help
```

The computed checksum must match exactly and both signature statuses must be
`Valid`. Verify the signer subject belongs to the expected publisher. Also verify
the GitHub attestation for the archive through the release page or GitHub CLI.

## Failure handling

- Missing signing secret: add the repository secret, then publish a new tag only
  after confirming no release was created.
- Invalid signature: stop. Check certificate purpose, password, trust chain, and
  timestamp connectivity. Never publish the unsigned output.
- PyInstaller failure: reproduce with the same lock file and spec. Do not add
  broad hidden imports without identifying the missing runtime module.
- Smoke-test failure: run the executable from `dist` and capture a sanitized
  traceback. A successful build is not proof the frozen app starts.
- Release creation failure after artifacts build: keep the tag immutable. Repair
  the workflow and use the repository's release policy to rerun or create a new
  patch version.

Do not manually upload unverified executables to work around a failed workflow.
