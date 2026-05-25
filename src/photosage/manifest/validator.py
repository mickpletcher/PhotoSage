from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from photosage.manifest.manifest_reader import ManifestValidationError, load_manifest, resolved_input_directory, safe_restore_path


@dataclass(slots=True)
class ManifestIssue:
    severity: str
    code: str
    message: str
    path: str = ""
    index: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ManifestIntegrityReport:
    manifest_path: Path
    valid: bool
    summary: dict[str, int]
    issues: list[ManifestIssue]
    hashes: dict[str, str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "manifest_path": str(self.manifest_path),
            "valid": self.valid,
            "summary": self.summary,
            "issues": [issue.to_dict() for issue in self.issues],
            "hashes": self.hashes,
        }


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _add_issue(issues: list[ManifestIssue], severity: str, code: str, message: str, path: Path | None = None, index: int | None = None) -> None:
    issues.append(ManifestIssue(severity=severity, code=code, message=message, path=str(path) if path else "", index=index))


def validate_manifest_integrity(manifest_path: Path, include_hashes: bool = False) -> ManifestIntegrityReport:
    """Validate a PhotoSage manifest without moving files."""
    resolved_manifest_path = manifest_path.expanduser().resolve(strict=False)
    issues: list[ManifestIssue] = []
    hashes: dict[str, str] = {}

    try:
        manifest = load_manifest(resolved_manifest_path)
        base_directory = resolved_input_directory(manifest, resolved_manifest_path)
    except ManifestValidationError as error:
        issue = ManifestIssue("error", "malformed_manifest", str(error), str(resolved_manifest_path), None)
        return ManifestIntegrityReport(
            manifest_path=resolved_manifest_path,
            valid=False,
            summary={"errors": 1, "warnings": 0, "files": 0},
            issues=[issue],
            hashes={},
        )

    files = manifest.get("files", [])
    for index, item in enumerate(files):
        try:
            original_path = safe_restore_path(Path(str(item["original_path"])), base_directory)
            new_path = safe_restore_path(Path(str(item["new_path"])), base_directory)
        except ManifestValidationError as error:
            _add_issue(issues, "error", "unsafe_path", str(error), index=index)
            continue

        status = str(item.get("status") or "")
        if status == "renamed":
            if not new_path.exists():
                _add_issue(issues, "error", "missing_renamed_file", "Renamed file is missing.", new_path, index)
            if original_path.exists():
                _add_issue(issues, "warning", "undo_collision", "Original path already exists. Undo would skip this file.", original_path, index)
        elif status in {"planned", "pending", "unchanged"}:
            if not original_path.exists():
                _add_issue(issues, "warning", "missing_original_file", "Original file is missing.", original_path, index)
        elif status in {"missing", "overwrite-prevented", "error"}:
            _add_issue(issues, "warning", f"manifest_status_{status}", f"Manifest entry status is {status}.", new_path, index)

        xmp_path = item.get("xmp_path")
        new_xmp_path = item.get("new_xmp_path")
        sidecar_status = item.get("sidecar_status")
        if sidecar_status == "renamed" and xmp_path and new_xmp_path:
            try:
                original_sidecar = safe_restore_path(Path(str(xmp_path)), base_directory)
                new_sidecar = safe_restore_path(Path(str(new_xmp_path)), base_directory)
            except ManifestValidationError as error:
                _add_issue(issues, "error", "unsafe_sidecar_path", str(error), index=index)
                continue
            if not new_sidecar.exists():
                _add_issue(issues, "error", "missing_sidecar", "Renamed XMP sidecar is missing.", new_sidecar, index)
            if original_sidecar.exists():
                _add_issue(issues, "warning", "sidecar_undo_collision", "Original XMP sidecar already exists. Undo would skip or collide.", original_sidecar, index)
        elif item.get("xmp_detected") and not xmp_path:
            _add_issue(issues, "warning", "sidecar_path_missing", "XMP was detected but xmp_path is missing.", index=index)

        if include_hashes:
            for path in (new_path, original_path):
                if path.exists() and path.is_file():
                    hashes[str(path)] = _sha256(path)

    errors = sum(1 for issue in issues if issue.severity == "error")
    warnings = sum(1 for issue in issues if issue.severity == "warning")
    return ManifestIntegrityReport(
        manifest_path=resolved_manifest_path,
        valid=errors == 0,
        summary={"errors": errors, "warnings": warnings, "files": len(files)},
        issues=issues,
        hashes=hashes,
    )
