from __future__ import annotations

from pathlib import Path
from typing import Any

from photosage.organization.policies import destination_for_policy


def folder_policy_preview(manifest: dict[str, Any], root: Path, policies: list[str]) -> dict[str, Any]:
    previews: dict[str, Any] = {}
    for policy in policies:
        destinations: list[dict[str, str]] = []
        folders: set[str] = set()
        names: set[str] = set()
        collisions: list[str] = []
        for item in manifest["files"]:
            destination = destination_for_policy(
                root,
                item.get("metadata") or {},
                item.get("ai_response") or {},
                item["new_filename"],
                policy,
            ).resolve(strict=False)
            key = str(destination).casefold()
            if key in names or (destination.exists() and destination != Path(item["original_path"])):
                collisions.append(str(destination))
            names.add(key)
            folders.add(str(destination.parent))
            destinations.append({"source": item["original_path"], "destination": str(destination)})
        previews[policy] = {
            "folder_count": len(folders),
            "folders": sorted(folders),
            "collisions": collisions,
            "operations": destinations,
        }
    return {"root": str(root.resolve()), "policies": previews}
