from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from PIL import Image

from photosage.duplicates.detector import DuplicateGroup
from photosage.manifest.manifest_writer import create_manifest, write_manifest
from photosage.rename.duplicate_handler import unique_destination
from photosage.rename.renamer import source_fingerprint


def _quality(path: Path) -> tuple[int, int, str]:
    try:
        with Image.open(path) as image:
            pixels = image.width * image.height
    except Exception:
        pixels = 0
    return pixels, path.stat().st_size, path.name.casefold()


def duplicate_review_rows(groups: list[DuplicateGroup]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for group in groups:
        paths = [Path(value) for value in group.files]
        keep = max(paths, key=_quality)
        confidence = "high" if group.distance == 0 else ("medium" if group.distance <= 3 else "low")
        for path in paths:
            rows.append(
                {
                    "group_id": group.group_id,
                    "path": str(path),
                    "distance": group.distance,
                    "confidence": confidence,
                    "recommendation": "keep" if path == keep else "review",
                    "recommended_keep": str(keep),
                }
            )
    return rows


def write_duplicate_csv(rows: list[dict[str, Any]], output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]) if rows else ["group_id", "path"])
        writer.writeheader()
        writer.writerows(rows)
    return output_path


def build_duplicate_review_manifest(
    input_directory: Path,
    review_directory: Path,
    groups: list[DuplicateGroup],
    manifest_directory: Path,
) -> Path:
    root = input_directory.resolve()
    review_root = review_directory.resolve(strict=False)
    try:
        review_root.relative_to(root)
    except ValueError as error:
        raise ValueError("Duplicate review folder must be inside the scanned input directory") from error

    rows = duplicate_review_rows(groups)
    seen: set[Path] = set()
    files: list[dict[str, Any]] = []
    for row in rows:
        if row["recommendation"] == "keep":
            continue
        source = Path(row["path"])
        destination = unique_destination(review_root, lambda counter, name=source.name: f"{counter:03d}_{name}", seen)
        files.append(
            {
                "original_path": str(source.resolve()),
                "new_path": str(destination.resolve(strict=False)),
                "original_filename": source.name,
                "new_filename": destination.name,
                "metadata_score": 0,
                "ai_required": False,
                "ai_used": False,
                "status": "needs-review",
                "approval_status": "required",
                "duplicate_group_id": row["group_id"],
                "duplicate_confidence": row["confidence"],
                "recommended_keep": row["recommended_keep"],
                **source_fingerprint(source),
            }
        )
    manifest = create_manifest(root, True, None, 0, files)
    manifest["workflow"] = "duplicate-review"
    manifest["review_directory"] = str(review_root)
    return write_manifest(manifest, manifest_directory)
