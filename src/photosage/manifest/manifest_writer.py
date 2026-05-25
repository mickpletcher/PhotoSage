from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4


def create_manifest(
    input_directory: Path,
    dry_run: bool,
    provider_used: str | None,
    metadata_threshold: int,
    files: list[dict[str, Any]],
) -> dict[str, Any]:
    """Create a rename manifest dictionary."""
    return {
        "run_id": str(uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "input_directory": str(input_directory.resolve()),
        "dry_run": dry_run,
        "provider_used": provider_used,
        "metadata_threshold": metadata_threshold,
        "files": files,
    }


def write_manifest(manifest: dict[str, Any], output_directory: Path, manifest_path: Path | None = None) -> Path:
    """Write a JSON rename manifest."""
    output_directory.mkdir(parents=True, exist_ok=True)
    if manifest_path is None:
        timestamp = datetime.fromisoformat(str(manifest["timestamp"]).replace("Z", "+00:00"))
        path = output_directory / f"rename_manifest_{timestamp.strftime('%Y%m%d_%H%M%S')}.json"
        if path.exists():
            path = output_directory / f"rename_manifest_{timestamp.strftime('%Y%m%d_%H%M%S')}_{manifest['run_id'][:8]}.json"
    else:
        path = manifest_path
    with path.open("w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2, default=str)
    return path
