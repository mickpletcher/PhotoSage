from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from photosage.manifest.manifest_reader import load_manifest
from photosage.manifest.manifest_writer import write_manifest
from photosage.rename.sanitizer import sanitize_filename


def _find_item(manifest: dict[str, Any], selector: str) -> dict[str, Any]:
    matches = [
        item
        for item in manifest["files"]
        if selector in {item.get("original_path"), item.get("original_filename"), Path(str(item.get("original_path", ""))).name}
    ]
    if len(matches) != 1:
        raise ValueError(f"Review selector must match exactly one file: {selector}")
    return matches[0]


def _validate_destinations(manifest: dict[str, Any]) -> None:
    destinations: set[str] = set()
    for item in manifest["files"]:
        if item.get("status") == "rejected":
            continue
        destination = Path(item["new_path"])
        key = str(destination.resolve(strict=False)).casefold()
        if key in destinations:
            raise ValueError(f"Reviewed filenames collide: {destination}")
        destinations.add(key)
        original = Path(item["original_path"])
        if destination.exists() and destination.resolve() != original.resolve():
            raise ValueError(f"Reviewed destination already exists: {destination}")


def apply_review_decisions(
    manifest_path: Path,
    decisions: list[dict[str, str]],
    reviewer: str = "local-user",
) -> dict[str, Any]:
    manifest_path = manifest_path.resolve()
    manifest = load_manifest(manifest_path)
    if not manifest.get("dry_run"):
        raise ValueError("Only an unapplied preview manifest can be reviewed")
    history = manifest.setdefault("review_history", [])
    for decision in decisions:
        selector = str(decision.get("selector") or "")
        action = str(decision.get("action") or "").lower()
        if action not in {"approve", "reject", "edit"}:
            raise ValueError(f"Unsupported review action: {action}")
        item = _find_item(manifest, selector)
        old_name = item["new_filename"]
        if action == "edit":
            requested = str(decision.get("new_filename") or "").strip()
            if not requested or Path(requested).name != requested:
                raise ValueError("Reviewed filename must be a filename without directory components")
            sanitized = sanitize_filename(requested)
            if Path(sanitized).suffix.lower() != Path(item["original_path"]).suffix.lower():
                raise ValueError("Reviewed filename must preserve the source extension")
            destination = Path(item["new_path"]).with_name(sanitized)
            item["new_filename"] = sanitized
            item["new_path"] = str(destination.resolve(strict=False))
            item["approval_status"] = "approved"
            item["status"] = "planned"
        elif action == "approve":
            if item.get("status") not in {"planned", "needs-review"}:
                raise ValueError(f"File cannot be approved from status {item.get('status')}")
            item["approval_status"] = "approved"
            item["status"] = "planned"
        else:
            item["approval_status"] = "rejected"
            item["status"] = "rejected"
        history.append(
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "reviewer": reviewer,
                "selector": selector,
                "action": action,
                "old_filename": old_name,
                "new_filename": item["new_filename"],
            }
        )
    _validate_destinations(manifest)
    write_manifest(manifest, manifest_path.parent, manifest_path)
    return manifest
