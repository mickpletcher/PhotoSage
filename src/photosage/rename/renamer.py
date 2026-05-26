from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from photosage.config import AppConfig
from photosage.duplicates.detector import duplicate_index, find_duplicate_groups
from photosage.geocoding.cache import GeocodeCache
from photosage.manifest.manifest_writer import create_manifest, write_manifest
from photosage.manifest.undo import undo_from_manifest
from photosage.metadata.exif_reader import extract_metadata
from photosage.metadata.metadata_score import score_metadata
from photosage.providers.exceptions import ProviderError
from photosage.providers.provider_manager import ProviderManager
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


def _apply_geocode_cache(metadata: dict[str, Any], config: AppConfig) -> dict[str, Any]:
    latitude = metadata.get("latitude") or metadata.get("gps_latitude")
    longitude = metadata.get("longitude") or metadata.get("gps_longitude")
    try:
        latitude_value = float(latitude) if latitude is not None else None
        longitude_value = float(longitude) if longitude is not None else None
    except (TypeError, ValueError):
        return metadata
    cached = GeocodeCache(config.geocode_cache_file, config.geocode_cache_ttl_days).resolve(latitude_value, longitude_value)
    if cached:
        metadata = dict(metadata)
        metadata["location"] = cached
        metadata["location_source"] = "geocode-cache"
    return metadata


def build_rename_manifest(
    input_directory: Path,
    config: AppConfig,
    force_ai: bool = False,
    dry_run: bool = True,
    ai_responses: dict[str, dict[str, Any]] | None = None,
    recursive: bool = True,
    analyze_ai: bool = False,
) -> dict[str, Any]:
    """Build proposed rename operations without modifying files."""
    files: list[dict[str, Any]] = []
    seen: set[Path] = set()
    existing_by_directory: dict[Path, set[str]] = {}
    provider_used: str | None = None
    provider_manager = ProviderManager(config) if analyze_ai else None

    scanned_images = scan_images(input_directory, recursive=recursive)
    duplicate_data = duplicate_index(find_duplicate_groups(scanned_images, config.duplicate_hash_distance))

    for image_path in scanned_images:
        metadata = _apply_geocode_cache(extract_metadata(image_path), config)
        metadata_score = score_metadata(metadata)
        ai_response = _ai_for_path(image_path, ai_responses)
        ai_required = force_ai or metadata_score < config.metadata_threshold
        ai_error: str | None = None
        ai_attempted = False

        if ai_required and ai_response is None and provider_manager is not None:
            ai_attempted = True
            try:
                ai_response = provider_manager.analyze_image(image_path, metadata)
            except ProviderError as error:
                ai_error = f"{type(error).__name__}: {error}"
                logger.warning("AI analysis unavailable for %s: %s", image_path, ai_error)

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

        duplicate_info = duplicate_data.get(str(image_path.resolve()), {})
        files.append(
            {
                "original_path": str(image_path.resolve()),
                "new_path": str(new_path.resolve()),
                "original_filename": image_path.name,
                "new_filename": new_path.name,
                "metadata_score": metadata_score,
                "ai_required": ai_required,
                "ai_used": ai_used,
                "ai_error": ai_error,
                "status": "ai-unavailable" if ai_attempted and not ai_used else ("planned" if dry_run else "pending"),
                "metadata": metadata,
                "ai_response": ai_response or {},
                "duplicate_group_id": duplicate_info.get("duplicate_group_id"),
                "duplicate_hash": duplicate_info.get("duplicate_hash"),
                "duplicate_distance": duplicate_info.get("duplicate_distance"),
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
    force_ai: bool = False,
    ai_responses: dict[str, dict[str, Any]] | None = None,
    recursive: bool = True,
    analyze_ai: bool = False,
) -> RenameResult:
    """Preview proposed rename operations and write a dry-run manifest."""
    manifest = build_rename_manifest(
        input_directory,
        config,
        force_ai=force_ai,
        dry_run=True,
        ai_responses=ai_responses,
        recursive=recursive,
        analyze_ai=analyze_ai,
    )
    manifest_path = write_manifest(manifest, config.manifest_directory)
    logger.info("preview manifest generated: %s", manifest_path)
    return RenameResult(manifest=manifest, manifest_path=manifest_path)


def apply_renames(
    input_directory: Path,
    config: AppConfig,
    force_ai: bool = False,
    ai_responses: dict[str, dict[str, Any]] | None = None,
    recursive: bool = True,
    analyze_ai: bool = False,
    progress_callback: Callable[[dict[str, Any]], None] | None = None,
) -> RenameResult:
    """Apply safe rename operations after writing a manifest."""
    manifest = build_rename_manifest(
        input_directory,
        config,
        force_ai=force_ai,
        dry_run=False,
        ai_responses=ai_responses,
        recursive=recursive,
        analyze_ai=analyze_ai,
    )
    manifest_path = write_manifest(manifest, config.manifest_directory)

    for item in manifest["files"]:
        original_path = Path(item["original_path"])
        new_path = Path(item["new_path"])

        if item["status"] != "pending":
            logger.warning("rename skipped status=%s path=%s", item["status"], original_path)
            if progress_callback:
                progress_callback(item)
            continue
        if original_path == new_path:
            item["status"] = "unchanged"
            logger.info("rename skipped unchanged path: %s", original_path)
            if progress_callback:
                progress_callback(item)
            continue
        if not original_path.exists():
            item["status"] = "missing"
            logger.warning("rename skipped missing file: %s", original_path)
            if progress_callback:
                progress_callback(item)
            continue
        if new_path.exists():
            item["status"] = "overwrite-prevented"
            logger.warning("rename skipped overwrite risk: %s", new_path)
            if progress_callback:
                progress_callback(item)
            continue

        try:
            new_path.parent.mkdir(parents=True, exist_ok=True)
            original_path.rename(new_path)
        except OSError as error:
            item["status"] = "error"
            item["error"] = str(error)
            logger.error("rename failed: %s -> %s error=%s", original_path, new_path, error)
            if progress_callback:
                progress_callback(item)
            continue

        item["status"] = "renamed"
        logger.info("renamed file original=%s new=%s", original_path, new_path)
        if progress_callback:
            progress_callback(item)

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
    recursive: bool = True,
    analyze_ai: bool = False,
    progress_callback: Callable[[dict[str, Any]], None] | None = None,
) -> RenameResult:
    """Preview or apply safe photo renames."""
    if apply:
        return apply_renames(
            input_directory,
            config,
            force_ai=force_ai,
            ai_responses=ai_responses,
            recursive=recursive,
            analyze_ai=analyze_ai,
            progress_callback=progress_callback,
        )
    return preview_renames(input_directory, config, force_ai=force_ai, ai_responses=ai_responses, recursive=recursive, analyze_ai=analyze_ai)
