from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from photosage.config import AppConfig
from photosage.lightroom.catalog_safety import validate_lightroom_export_directory
from photosage.lightroom.folder_organizer import category_for_photo, organized_destination
from photosage.lightroom.metadata_mapper import lightroom_score_bonus, merge_lightroom_metadata
from photosage.lightroom.presets import LightroomPreset, get_preset
from photosage.lightroom.xmp_reader import read_xmp_sidecar, sidecar_path_for_image
from photosage.manifest.manifest_writer import create_manifest, write_manifest
from photosage.metadata.exif_reader import extract_metadata
from photosage.metadata.metadata_score import score_metadata
from photosage.rename.duplicate_handler import existing_names, unique_destination
from photosage.rename.filename_builder import build_filename
from photosage.scanner import scan_images

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class LightroomProcessResult:
    manifest: dict[str, Any]
    manifest_path: Path
    warnings: list[str]


def _effective_config(config: AppConfig, preset: LightroomPreset | None) -> AppConfig:
    if preset is None:
        return config
    return AppConfig(
        vision_provider=config.vision_provider,
        metadata_threshold=preset.metadata_threshold,
        dry_run_default=config.dry_run_default,
        local_only=config.local_only,
        fallback_order=config.fallback_order,
        filename_format=preset.filename_format,
        manifest_directory=config.manifest_directory,
        log_file=config.log_file,
        provider_settings=config.provider_settings,
        provider_retry_count=config.provider_retry_count,
        provider_retry_initial_delay=config.provider_retry_initial_delay,
        recursive_scanning=config.recursive_scanning,
        thumbnail_size=config.thumbnail_size,
        log_level=config.log_level,
        max_concurrent_ai_requests=config.max_concurrent_ai_requests,
    )


def _ai_for_path(image_path: Path, ai_responses: dict[str, dict[str, Any]] | None) -> dict[str, Any] | None:
    if not ai_responses:
        return None
    return ai_responses.get(str(image_path)) or ai_responses.get(str(image_path.resolve())) or ai_responses.get(image_path.name)


def build_lightroom_manifest(
    input_directory: Path,
    config: AppConfig,
    dry_run: bool = True,
    organize: bool = False,
    preset_name: str | None = None,
    force_ai: bool = False,
    ai_responses: dict[str, dict[str, Any]] | None = None,
    recursive: bool = True,
    force_catalog_modify: bool = False,
) -> tuple[dict[str, Any], list[str]]:
    warnings = validate_lightroom_export_directory(input_directory, force_catalog_modify=force_catalog_modify)
    preset = get_preset(preset_name) if preset_name else None
    effective = _effective_config(config, preset)
    organize = organize or bool(preset and preset.organize)
    force_ai = force_ai or bool(preset and preset.force_ai)

    files: list[dict[str, Any]] = []
    seen: set[Path] = set()
    existing_by_directory: dict[Path, set[str]] = {}
    provider_used: str | None = None

    for image_path in scan_images(input_directory, recursive=recursive):
        metadata = extract_metadata(image_path)
        xmp_metadata = read_xmp_sidecar(image_path)
        merged_metadata = merge_lightroom_metadata(metadata, xmp_metadata)
        metadata_score = min(100, score_metadata(merged_metadata) + lightroom_score_bonus(xmp_metadata))
        ai_response = _ai_for_path(image_path, ai_responses)
        ai_required = force_ai or metadata_score < effective.metadata_threshold
        ai_used = ai_response is not None
        if ai_response and not provider_used:
            provider_used = ai_response.get("provider")

        target_directory = image_path.parent
        if organize:
            preliminary_name = build_filename(merged_metadata, ai_response, 1, effective.filename_format)
            target_directory = organized_destination(
                input_directory,
                merged_metadata,
                preliminary_name,
                ai_response,
                preset.category if preset else None,
            ).parent

        directory_key = target_directory.resolve()
        existing = existing_by_directory.setdefault(directory_key, existing_names(target_directory))
        new_path = unique_destination(
            target_directory,
            lambda counter, metadata=merged_metadata, ai_response=ai_response: build_filename(
                metadata,
                ai_response,
                counter,
                effective.filename_format,
            ),
            seen,
            existing,
            image_path,
        )

        sidecar_path = sidecar_path_for_image(image_path)
        new_sidecar_path = new_path.with_suffix(".xmp") if sidecar_path.exists() else None
        category = category_for_photo(merged_metadata, ai_response, preset.category if preset else None)
        status = "planned" if dry_run else "pending"

        files.append(
            {
                "original_path": str(image_path.resolve()),
                "new_path": str(new_path.resolve()),
                "original_filename": image_path.name,
                "new_filename": new_path.name,
                "metadata_score": metadata_score,
                "ai_required": ai_required,
                "ai_used": ai_used,
                "status": status,
                "metadata": merged_metadata,
                "ai_response": ai_response or {},
                "lightroom_mode": True,
                "xmp_detected": bool(xmp_metadata.get("xmp_detected")),
                "xmp_path": str(sidecar_path.resolve()) if sidecar_path.exists() else None,
                "new_xmp_path": str(new_sidecar_path.resolve()) if new_sidecar_path else None,
                "organization_applied": organize,
                "category": category,
                "sidecar_status": "planned" if new_sidecar_path else "none",
            }
        )
        logger.info(
            "lightroom preview original=%s new=%s score=%s ai_required=%s xmp=%s",
            image_path,
            new_path,
            metadata_score,
            ai_required,
            bool(xmp_metadata.get("xmp_detected")),
        )

    manifest = create_manifest(
        input_directory=input_directory,
        dry_run=dry_run,
        provider_used=provider_used,
        metadata_threshold=effective.metadata_threshold,
        files=files,
    )
    manifest["lightroom_mode"] = True
    manifest["preset"] = preset.name if preset else None
    manifest["organization_applied"] = organize
    manifest["catalog_warnings"] = warnings
    return manifest, warnings


def apply_lightroom_manifest(
    manifest: dict[str, Any],
    progress_callback: Callable[[dict[str, Any]], None] | None = None,
) -> dict[str, Any]:
    for item in manifest["files"]:
        original_path = Path(item["original_path"])
        new_path = Path(item["new_path"])
        sidecar_path = Path(item["xmp_path"]) if item.get("xmp_path") else None
        new_sidecar_path = Path(item["new_xmp_path"]) if item.get("new_xmp_path") else None

        if original_path == new_path:
            item["status"] = "unchanged"
            item["sidecar_status"] = "unchanged" if sidecar_path else "none"
            if progress_callback:
                progress_callback(item)
            continue
        if not original_path.exists():
            item["status"] = "missing"
            logger.warning("lightroom rename skipped missing file: %s", original_path)
            if progress_callback:
                progress_callback(item)
            continue
        if new_path.exists():
            item["status"] = "overwrite-prevented"
            logger.warning("lightroom rename skipped overwrite risk: %s", new_path)
            if progress_callback:
                progress_callback(item)
            continue
        if new_sidecar_path and new_sidecar_path.exists():
            item["status"] = "overwrite-prevented"
            item["sidecar_status"] = "overwrite-prevented"
            logger.warning("lightroom sidecar skipped overwrite risk: %s", new_sidecar_path)
            if progress_callback:
                progress_callback(item)
            continue

        try:
            new_path.parent.mkdir(parents=True, exist_ok=True)
            original_path.rename(new_path)
            item["status"] = "renamed"
            if sidecar_path and sidecar_path.exists() and new_sidecar_path:
                new_sidecar_path.parent.mkdir(parents=True, exist_ok=True)
                sidecar_path.rename(new_sidecar_path)
                item["sidecar_status"] = "renamed"
            elif sidecar_path:
                item["sidecar_status"] = "missing"
            else:
                item["sidecar_status"] = "none"
        except OSError as error:
            item["status"] = "error"
            item["error"] = str(error)
            logger.error("lightroom rename failed: %s -> %s error=%s", original_path, new_path, error)
        if progress_callback:
            progress_callback(item)
    return manifest


def process_lightroom_export(
    input_directory: Path,
    config: AppConfig,
    preview: bool = True,
    apply: bool = False,
    organize: bool = False,
    preset_name: str | None = None,
    force_ai: bool = False,
    ai_responses: dict[str, dict[str, Any]] | None = None,
    recursive: bool = True,
    force_catalog_modify: bool = False,
    progress_callback: Callable[[dict[str, Any]], None] | None = None,
) -> LightroomProcessResult:
    if apply and preview:
        raise ValueError("Choose preview or apply, not both.")

    manifest, warnings = build_lightroom_manifest(
        input_directory=input_directory,
        config=config,
        dry_run=not apply,
        organize=organize,
        preset_name=preset_name,
        force_ai=force_ai,
        ai_responses=ai_responses,
        recursive=recursive,
        force_catalog_modify=force_catalog_modify,
    )
    manifest_path = write_manifest(manifest, config.manifest_directory)
    logger.info("lightroom manifest generated: %s", manifest_path)

    if apply:
        manifest = apply_lightroom_manifest(manifest, progress_callback=progress_callback)
        write_manifest(manifest, config.manifest_directory, manifest_path)

    return LightroomProcessResult(manifest=manifest, manifest_path=manifest_path, warnings=warnings)
