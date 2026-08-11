from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any, Literal

from photosage.manifest.manifest_reader import load_manifest
from photosage.manifest.manifest_writer import write_manifest
from photosage.manifest.undo import rollback_all
from photosage.rename.renamer import apply_rename_manifest, source_fingerprint

RecoveryAction = Literal["inspect", "resume", "rollback"]


def _matches(item: dict[str, Any], path: Path) -> bool:
    try:
        actual = source_fingerprint(path)
    except OSError:
        return False
    return all(actual.get(key) == item.get(key) for key in ("source_sha256", "source_size", "source_mtime_ns"))


def inspect_recovery(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    operations: list[dict[str, Any]] = []
    for item in manifest["files"]:
        original = Path(item["original_path"])
        destination = Path(item["new_path"])
        original_exists = original.exists()
        destination_exists = destination.exists()
        if original_exists and not destination_exists:
            state = "ready" if _matches(item, original) else "source-changed"
        elif destination_exists and not original_exists:
            state = "completed" if _matches(item, destination) else "destination-changed"
        elif original_exists and destination_exists:
            state = "collision"
        else:
            state = "missing"
        operations.append(
            {
                "original_path": str(original),
                "new_path": str(destination),
                "recorded_status": item.get("status"),
                "recovery_state": state,
            }
        )
    return operations


def recover_manifest(manifest_path: Path, action: RecoveryAction = "inspect") -> dict[str, Any]:
    manifest_path = manifest_path.resolve()
    manifest = load_manifest(manifest_path)
    operations = inspect_recovery(manifest)
    if action == "inspect":
        return {"action": action, "operations": operations}
    if action == "rollback":
        result = rollback_all(manifest_path)
        return {
            "action": action,
            "operations": [asdict(operation) for operation in result.operations],
            "report_path": str(result.report_path),
        }

    states = {operation["original_path"]: operation["recovery_state"] for operation in operations}
    for item in manifest["files"]:
        state = states[item["original_path"]]
        if state == "ready":
            item["status"] = "pending"
        elif state == "completed":
            item["status"] = "renamed"
        else:
            item["status"] = f"recovery-{state}"
    write_manifest(manifest, manifest_path.parent, manifest_path)
    result = apply_rename_manifest(manifest, manifest_path)
    return {"action": action, "operations": inspect_recovery(result.manifest), "manifest_path": str(manifest_path)}
