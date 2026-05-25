from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from photosage.config import AppConfig
from photosage.manifest.manifest_writer import create_manifest, write_manifest
from photosage.manifest.undo import undo_from_manifest
from photosage.metadata.exif_reader import extract_metadata
from photosage.metadata.metadata_score import score_metadata
from photosage.rename.duplicate_handler import existing_names, unique_destination
from photosage.rename.filename_builder import build_filename
from photosage.scanner import scan_images

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class RenameResult:
    """Result from a preview or apply rename operation."""

    manifest: dict[str, Any]
    manifest_path: Path | None


def _ai_for_path(image_path: Path, ai_responses: dict[str, dict[str, Any]] | None) -> dict[str, Any] | None:
    if not ai_responses:
        return None
    return ai_responses.get(str(image_path)) or ai_responses.get(str(image_path.resolve())) or ai_responses.get(image_path.name)


def build_rename_manifest(
    input_directory: Path,
    config: AppConfig,
    force_ai: bool = False,
    dry_run: bool = True,
    ai_responses: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build proposed rename operations without modifying files or calling providers."""
    files: list[dict[str, Any]] = []
    seen: set[Path] = set()
    existing_by_directory: dict[Path, set[str]] = {}
    provider_used: str | None = None

    if force_ai and not ai_responses:
        logger.info("force_ai requested, but renamer received no normalized AI responses")

    for image_path in scan_images(input_directory):
        metadata = extract_metadata(image_path)
        metadata_score = score_metadata(metadata)
        ai_response = _ai_for_path(image_path, ai_responses)
        ai_used = ai_response is not None
        if ai_response and not provider_used:
            provider_used = ai_response.get("provider")

        directory = image_path.parent
        existing = existing_by_directory.setdefault(directory.resolve(), existing_names(directory))
        new_path = unique_destination(
            directory,
            lambda counter, metadata=metadata, ai_response=ai_response: build_filename(
                metadata,
                ai_response,
                counter,
                config.filename_format,
            ),
            seen,
            existing,
            image_path,
        )

        logger.info("preview rename original=%s new=%s metadata_score=%s ai_used=%s", image_path, new_path, metadata_score, ai_used)

        files.append(
            {
                "original_path": str(image_path.resolve()),
                "new_path": str(new_path.resolve()),
                "original_filename": image_path.name,
                "new_filename": new_path.name,
                "metadata_score": metadata_score,
                "ai_used": ai_used,
                "status": "planned" if dry_run else "pending",
                "metadata": metadata,
                "ai_response": ai_response or {},
            }
        )

    return create_manifest(
        input_directory=input_directory,
        dry_run=dry_run,
        provider_used=provider_used,
        metadata_threshold=config.metadata_threshold,
        files=files,
    )


def preview_renames(
    input_directory: Path,
    config: AppConfig,
    ai_responses: dict[str, dict[str, Any]] | None = None,
) -> RenameResult:
    """Preview proposed rename operations and write a dry-run manifest."""
    manifest = build_rename_manifest(input_directory, config, dry_run=True, ai_responses=ai_responses)
    manifest_path = write_manifest(manifest, config.manifest_directory)
    logger.info("preview manifest generated: %s", manifest_path)
    return RenameResult(manifest=manifest, manifest_path=manifest_path)


def apply_renames(
    input_directory: Path,
    config: AppConfig,
    ai_responses: dict[str, dict[str, Any]] | None = None,
) -> RenameResult:
    """Apply safe rename operations after writing a manifest."""
    manifest = build_rename_manifest(input_directory, config, dry_run=False, ai_responses=ai_responses)
    manifest_path = write_manifest(manifest, config.manifest_directory)

    for item in manifest["files"]:
        original_path = Path(item["original_path"])
        new_path = Path(item["new_path"])

        if original_path == new_path:
            item["status"] = "unchanged"
            logger.info("rename skipped unchanged path: %s", original_path)
            continue
        if not original_path.exists():
            item["status"] = "missing"
            logger.warning("rename skipped missing file: %s", original_path)
            continue
        if new_path.exists():
            item["status"] = "overwrite-prevented"
            logger.warning("rename skipped overwrite risk: %s", new_path)
            continue

        try:
            new_path.parent.mkdir(parents=True, exist_ok=True)
            original_path.rename(new_path)
        except OSError as error:
            item["status"] = "error"
            item["error"] = str(error)
            logger.error("rename failed: %s -> %s error=%s", original_path, new_path, error)
            continue

        item["status"] = "renamed"
        logger.info("renamed file original=%s new=%s", original_path, new_path)

    write_manifest(manifest, config.manifest_directory, manifest_path)
    return RenameResult(manifest=manifest, manifest_path=manifest_path)


def rollback_renames(manifest_path: Path) -> list[dict[str, str]]:
    """Rollback rename operations from a manifest."""
    logger.info("rollback started manifest=%s", manifest_path)
    return undo_from_manifest(manifest_path)


def rename_files(
    input_directory: Path,
    config: AppConfig,
    apply: bool = False,
    force_ai: bool = False,
    ai_responses: dict[str, dict[str, Any]] | None = None,
) -> RenameResult:
    """Preview or apply safe photo renames."""
    if apply:
        return apply_renames(input_directory, config, ai_responses=ai_responses)
    if force_ai and not ai_responses:
        logger.info("force_ai requested, but no normalized AI responses were supplied")
    return preview_renames(input_directory, config, ai_responses=ai_responses)
