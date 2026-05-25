from __future__ import annotations

from pathlib import Path
from typing import Any

from photosage.config import AppConfig
from photosage.manifest.manifest_writer import write_manifest
from photosage.manifest.undo import rollback_all
from photosage.metadata.exif_reader import extract_metadata
from photosage.metadata.metadata_score import score_metadata
from photosage.rename.renamer import apply_renames, build_rename_manifest
from photosage.scanner import count_unsupported_files, scan_images


def scan_folder(input_directory: Path, config: AppConfig, recursive: bool = True, force_ai: bool = False) -> dict[str, Any]:
    """Scan a folder and return metadata score rows for the GUI."""
    images = scan_images(input_directory, recursive=recursive)
    rows: list[dict[str, Any]] = []
    scores: list[int] = []

    for image_path in images:
        metadata = extract_metadata(image_path)
        score = score_metadata(metadata)
        ai_required = force_ai or score < config.metadata_threshold
        scores.append(score)
        rows.append(
            {
                "path": str(image_path.resolve()),
                "original_filename": image_path.name,
                "metadata_score": score,
                "ai_required": ai_required,
                "ai_used": False,
                "provider": config.vision_provider if ai_required else "",
                "confidence": "",
                "file_type": image_path.suffix.lower().lstrip("."),
                "date_taken": metadata.get("date_taken") or metadata.get("exif_date_taken") or "",
                "location": _location_text(metadata),
                "status": "ai-required" if ai_required else "metadata-only",
                "metadata": metadata,
                "ai_response": {},
            }
        )

    return {
        "summary": {
            "total_files": len(images) + count_unsupported_files(input_directory, recursive=recursive),
            "supported_files": len(images),
            "unsupported_files": count_unsupported_files(input_directory, recursive=recursive),
            "files_requiring_ai": sum(1 for row in rows if row["ai_required"]),
            "files_with_sufficient_metadata": sum(1 for row in rows if not row["ai_required"]),
            "average_metadata_score": round(sum(scores) / len(scores), 2) if scores else 0,
        },
        "files": rows,
    }


def preview_folder(input_directory: Path, config: AppConfig, recursive: bool = True, force_ai: bool = False) -> dict[str, Any]:
    """Build a preview manifest using backend rename logic."""
    manifest = build_rename_manifest(input_directory, config, force_ai=force_ai, dry_run=True, recursive=recursive)
    manifest_path = write_manifest(manifest, config.manifest_directory)
    manifest["manifest_path"] = str(manifest_path)
    return manifest


def apply_folder(input_directory: Path, config: AppConfig, recursive: bool = True) -> dict[str, Any]:
    """Apply safe renames using backend rename logic."""
    result = apply_renames(input_directory, config, recursive=recursive)
    result.manifest["manifest_path"] = str(result.manifest_path)
    return result.manifest


def undo_manifest(manifest_path: Path, dry_run: bool = False) -> dict[str, Any]:
    """Run or preview rollback using backend undo logic."""
    result = rollback_all(manifest_path, dry_run=dry_run)
    return {
        "summary": result.summary,
        "report_path": str(result.report_path),
        "operations": [
            {
                "source": operation.source,
                "destination": operation.destination,
                "status": operation.status,
                "message": operation.message,
            }
            for operation in result.operations
        ],
    }


def _location_text(metadata: dict[str, Any]) -> str:
    latitude = metadata.get("latitude") or metadata.get("gps_latitude")
    longitude = metadata.get("longitude") or metadata.get("gps_longitude")
    if latitude is None or longitude is None:
        return ""
    return f"{latitude}, {longitude}"
