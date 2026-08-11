from __future__ import annotations

import hashlib
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

MANIFEST_SCHEMA_VERSION = 2


def manifest_checksum(manifest: dict[str, Any]) -> str:
    payload = dict(manifest)
    payload.pop("manifest_sha256", None)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def create_manifest(
    input_directory: Path,
    dry_run: bool,
    provider_used: str | None,
    metadata_threshold: int,
    files: list[dict[str, Any]],
) -> dict[str, Any]:
    """Create a rename manifest dictionary."""
    return {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "run_id": str(uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "input_directory": str(input_directory.resolve()),
        "dry_run": dry_run,
        "provider_used": provider_used,
        "metadata_threshold": metadata_threshold,
        "files": files,
    }


def write_manifest(manifest: dict[str, Any], output_directory: Path, manifest_path: Path | None = None) -> Path:
    """Atomically write a checksummed JSON rename manifest."""
    output_directory.mkdir(parents=True, exist_ok=True)
    if manifest_path is None:
        timestamp = datetime.fromisoformat(str(manifest["timestamp"]).replace("Z", "+00:00"))
        path = output_directory / f"rename_manifest_{timestamp.strftime('%Y%m%d_%H%M%S')}.json"
        if path.exists():
            path = output_directory / f"rename_manifest_{timestamp.strftime('%Y%m%d_%H%M%S')}_{manifest['run_id'][:8]}.json"
    else:
        path = manifest_path
    manifest["schema_version"] = MANIFEST_SCHEMA_VERSION
    manifest["manifest_sha256"] = manifest_checksum(manifest)
    content = json.dumps(manifest, indent=2, default=str)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, path)
    finally:
        temporary_path.unlink(missing_ok=True)
    return path
