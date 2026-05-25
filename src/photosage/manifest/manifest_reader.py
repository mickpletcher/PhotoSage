from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

REQUIRED_MANIFEST_KEYS = {"run_id", "timestamp", "input_directory", "files"}
REQUIRED_FILE_KEYS = {"original_path", "new_path", "status"}


class ManifestValidationError(ValueError):
    """Manifest is malformed or unsafe to process."""


def load_manifest(manifest_path: Path) -> dict[str, Any]:
    """Load and validate a PhotoSage manifest file."""
    path = manifest_path.expanduser().resolve(strict=False)
    if not path.exists():
        raise ManifestValidationError(f"Manifest does not exist: {manifest_path}")
    if not path.is_file():
        raise ManifestValidationError(f"Manifest is not a file: {manifest_path}")

    try:
        with path.open("r", encoding="utf-8") as handle:
            manifest = json.load(handle)
    except json.JSONDecodeError as error:
        raise ManifestValidationError(f"Manifest is not valid JSON: {error}") from error

    validate_manifest(manifest, path)
    logger.info("manifest loaded path=%s run_id=%s", path, manifest.get("run_id"))
    return manifest


def validate_manifest(manifest: dict[str, Any], manifest_path: Path | None = None) -> None:
    """Validate PhotoSage manifest structure."""
    if not isinstance(manifest, dict):
        raise ManifestValidationError("Manifest must be a JSON object")

    missing = REQUIRED_MANIFEST_KEYS.difference(manifest)
    if missing:
        raise ManifestValidationError(f"Manifest missing required keys: {sorted(missing)}")

    files = manifest.get("files")
    if not isinstance(files, list):
        raise ManifestValidationError("Manifest files must be an array")

    base_directory = resolved_input_directory(manifest, manifest_path)

    for index, item in enumerate(files):
        if not isinstance(item, dict):
            raise ManifestValidationError(f"Manifest file entry {index} must be an object")
        missing_item_keys = REQUIRED_FILE_KEYS.difference(item)
        if missing_item_keys:
            raise ManifestValidationError(f"Manifest file entry {index} missing keys: {sorted(missing_item_keys)}")
        safe_restore_path(Path(str(item["new_path"])), base_directory)
        safe_restore_path(Path(str(item["original_path"])), base_directory)


def resolved_input_directory(manifest: dict[str, Any], manifest_path: Path | None = None) -> Path:
    """Resolve the manifest input directory consistently."""
    input_directory = Path(str(manifest["input_directory"])).expanduser()
    if input_directory.is_absolute():
        return input_directory.resolve(strict=False)
    if manifest_path is not None:
        return (manifest_path.parent / input_directory).resolve(strict=False)
    return input_directory.resolve(strict=False)


def safe_restore_path(path: Path, base_directory: Path) -> Path:
    """Normalize a manifest path and reject traversal or symlink escapes."""
    raw = str(path)
    if ".." in Path(raw).parts:
        raise ManifestValidationError(f"Unsafe path traversal detected: {path}")

    candidate = path.expanduser()
    if not candidate.is_absolute():
        candidate = base_directory / candidate
    resolved = candidate.resolve(strict=False)
    base = base_directory.resolve(strict=False)

    try:
        resolved.relative_to(base)
    except ValueError as error:
        raise ManifestValidationError(f"Path escapes manifest input directory: {path}") from error

    return resolved
