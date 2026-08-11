from __future__ import annotations

import hashlib
import logging
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from photosage.config import AppConfig
from photosage.duplicates.detector import duplicate_index, find_duplicate_groups
from photosage.geocoding.cache import GeocodeCache
from photosage.manifest.manifest_reader import load_manifest
from photosage.manifest.manifest_writer import create_manifest, write_manifest
from photosage.manifest.undo import undo_from_manifest
from photosage.metadata.exif_reader import extract_metadata
from photosage.metadata.metadata_score import score_metadata
from photosage.metadata.video import extract_video_keyframe
from photosage.providers.exceptions import ProviderError
from photosage.providers.provider_manager import ProviderManager
from photosage.rename.duplicate_handler import existing_names, unique_destination
from photosage.rename.filename_builder import build_filename
from photosage.scanner import scan_images

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class RenameResult:
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


def source_fingerprint(path: Path) -> dict[str, Any]:
    before = path.stat()
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    after = path.stat()
    if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
        raise OSError("Source file changed while it was being inspected")
    return {
        "source_sha256": digest.hexdigest(),
        "source_size": after.st_size,
        "source_mtime_ns": after.st_mtime_ns,
    }


def _source_matches(item: dict[str, Any], path: Path) -> bool:
    try:
        fingerprint = source_fingerprint(path)
    except OSError:
        return False
    return all(fingerprint[key] == item.get(key) for key in fingerprint)


def _analyze_pending_records(records: list[dict[str, Any]], config: AppConfig) -> None:
    pending = [record for record in records if record["ai_required"] and record["ai_response"] is None and not record["fingerprint_error"]]
    if not pending:
        return

    manager = ProviderManager(config)

    def analyze(record: dict[str, Any]) -> dict[str, Any]:
        if record["metadata"].get("media_type") != "video":
            return manager.analyze_image(record["image_path"], record["metadata"])
        with tempfile.TemporaryDirectory(prefix="photosage-video-") as temporary_directory:
            keyframe = extract_video_keyframe(record["image_path"], Path(temporary_directory) / "keyframe.jpg")
            return manager.analyze_image(keyframe, record["metadata"])

    with ThreadPoolExecutor(max_workers=max(1, config.max_concurrent_ai_requests)) as executor:
        futures = {executor.submit(analyze, record): record for record in pending}
        for future in as_completed(futures):
            record = futures[future]
            record["ai_attempted"] = True
            try:
                record["ai_response"] = future.result()
            except (ProviderError, RuntimeError, OSError) as error:
                record["ai_error"] = f"{type(error).__name__}: {error}"
                logger.warning("AI analysis unavailable for %s: %s", record["image_path"], record["ai_error"])


def _planned_status(record: dict[str, Any], dry_run: bool) -> str:
    if record["fingerprint_error"]:
        return "source-unstable"
    if record["ai_required"] and record["ai_response"] is None:
        return "ai-unavailable" if record["ai_attempted"] else "ai-required"
    return "planned" if dry_run else "pending"


def build_rename_manifest(
    input_directory: Path,
    config: AppConfig,
    force_ai: bool = False,
    dry_run: bool = True,
    ai_responses: dict[str, dict[str, Any]] | None = None,
    recursive: bool = True,
    analyze_ai: bool = False,
) -> dict[str, Any]:
    files: list[dict[str, Any]] = []
    seen: set[Path] = set()
    existing_by_directory: dict[Path, set[str]] = {}
    provider_used: str | None = None
    scanned_images = scan_images(input_directory, recursive=recursive)
    duplicate_data = (
        duplicate_index(find_duplicate_groups(scanned_images, config.duplicate_hash_distance))
        if config.detect_duplicates_during_rename
        else {}
    )
    records: list[dict[str, Any]] = []

    for image_path in scanned_images:
        metadata = _apply_geocode_cache(extract_metadata(image_path), config)
        try:
            fingerprint = source_fingerprint(image_path)
            fingerprint_error = None
        except OSError as error:
            fingerprint = {}
            fingerprint_error = str(error)
        records.append(
            {
                "image_path": image_path,
                "metadata": metadata,
                "metadata_score": score_metadata(metadata),
                "ai_response": _ai_for_path(image_path, ai_responses),
                "ai_required": force_ai or score_metadata(metadata) < config.metadata_threshold,
                "ai_error": None,
                "ai_attempted": False,
                "fingerprint": fingerprint,
                "fingerprint_error": fingerprint_error,
            }
        )

    if analyze_ai:
        _analyze_pending_records(records, config)

    for record in records:
        image_path = record["image_path"]
        metadata = record["metadata"]
        ai_response = record["ai_response"]
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
        duplicate_info = duplicate_data.get(str(image_path.resolve()), {})
        item = {
            "original_path": str(image_path.resolve()),
            "new_path": str(new_path.resolve()),
            "original_filename": image_path.name,
            "new_filename": new_path.name,
            "metadata_score": record["metadata_score"],
            "ai_required": record["ai_required"],
            "ai_used": ai_used,
            "ai_error": record["ai_error"],
            "status": _planned_status(record, dry_run),
            "metadata": metadata,
            "ai_response": ai_response or {},
            "duplicate_group_id": duplicate_info.get("duplicate_group_id"),
            "duplicate_hash": duplicate_info.get("duplicate_hash"),
            "duplicate_distance": duplicate_info.get("duplicate_distance"),
            "astro_mode": bool(metadata.get("astro_mode")),
            "astro_profile": metadata.get("astro_profile"),
            "astro_target": metadata.get("astro_target"),
            "astro_capture_night": metadata.get("astro_capture_night"),
            "astro_session_id": metadata.get("astro_session_id"),
            "fits_detected": bool(metadata.get("fits_detected")),
            **record["fingerprint"],
        }
        confidence = float((ai_response or {}).get("confidence") or 0)
        needs_review = item["status"] == "planned" and (
            (config.require_manual_review_for_ai and ai_used and confidence < config.review_confidence_threshold)
            or bool(item.get("duplicate_group_id"))
        )
        if needs_review:
            item["status"] = "needs-review"
            item["approval_status"] = "required"
        else:
            item["approval_status"] = "not-required"
        if record["fingerprint_error"]:
            item["error"] = record["fingerprint_error"]
        files.append(item)
        logger.info(
            "preview rename original=%s new=%s metadata_score=%s ai_used=%s",
            image_path,
            new_path,
            record["metadata_score"],
            ai_used,
        )

    manifest = create_manifest(
        input_directory=input_directory,
        dry_run=dry_run,
        provider_used=provider_used,
        metadata_threshold=config.metadata_threshold,
        files=files,
    )
    astro_files = [item for item in files if item.get("astro_mode")]
    if astro_files:
        manifest["astro_mode"] = True
        manifest["astro_groups"] = _astro_group_summary(astro_files)
    return manifest


def _astro_group_summary(files: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    groups: dict[str, dict[str, Any]] = {}
    for item in files:
        capture_night = str(item.get("astro_capture_night") or "unknown-night")
        group = groups.setdefault(capture_night, {"count": 0, "targets": [], "profiles": []})
        group["count"] += 1
        target = item.get("astro_target")
        profile = item.get("astro_profile")
        if target and target not in group["targets"]:
            group["targets"].append(target)
        if profile and profile not in group["profiles"]:
            group["profiles"].append(profile)
    return groups


def preview_renames(
    input_directory: Path,
    config: AppConfig,
    force_ai: bool = False,
    ai_responses: dict[str, dict[str, Any]] | None = None,
    recursive: bool = True,
    analyze_ai: bool = False,
) -> RenameResult:
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


def _write_operation(manifest: dict[str, Any], manifest_path: Path) -> None:
    write_manifest(manifest, manifest_path.parent, manifest_path)


def apply_rename_manifest(
    manifest: dict[str, Any],
    manifest_path: Path,
    progress_callback: Callable[[dict[str, Any]], None] | None = None,
) -> RenameResult:
    manifest["dry_run"] = False
    manifest["apply_started_at"] = datetime.now(timezone.utc).isoformat()
    if manifest.get("watch_mode"):
        manifest["approval_required"] = False
    for item in manifest["files"]:
        if item.get("status") == "planned":
            item["status"] = "pending"
        if item.get("approval_status") == "queued":
            item["approval_status"] = "approved"
    _write_operation(manifest, manifest_path)

    for item in manifest["files"]:
        original_path = Path(item["original_path"])
        new_path = Path(item["new_path"])
        if item["status"] != "pending":
            logger.warning("rename skipped status=%s path=%s", item["status"], original_path)
        elif original_path == new_path:
            item["status"] = "unchanged"
        elif not original_path.exists():
            item["status"] = "missing"
        elif new_path.exists():
            item["status"] = "overwrite-prevented"
        elif not _source_matches(item, original_path):
            item["status"] = "source-changed"
            item["error"] = "Source file no longer matches the reviewed manifest"
        else:
            item["status"] = "rename-started"
            _write_operation(manifest, manifest_path)
            try:
                new_path.parent.mkdir(parents=True, exist_ok=True)
                original_path.rename(new_path)
                if not _source_matches(item, new_path):
                    try:
                        new_path.rename(original_path)
                        item["status"] = "integrity-rollback"
                        item["error"] = "Destination fingerprint changed during rename; source was restored"
                    except OSError as rollback_error:
                        item["status"] = "integrity-error"
                        item["error"] = f"Destination fingerprint mismatch and rollback failed: {rollback_error}"
                else:
                    item["status"] = "renamed"
                    item["renamed_at"] = datetime.now(timezone.utc).isoformat()
                    logger.info("renamed file original=%s new=%s", original_path, new_path)
            except OSError as error:
                item["status"] = "error"
                item["error"] = str(error)
                logger.error("rename failed: %s -> %s error=%s", original_path, new_path, error)
        _write_operation(manifest, manifest_path)
        if progress_callback:
            progress_callback(item)

    manifest["apply_completed_at"] = datetime.now(timezone.utc).isoformat()
    _write_operation(manifest, manifest_path)
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
    return apply_rename_manifest(manifest, manifest_path, progress_callback=progress_callback)


def apply_reviewed_manifest(
    manifest_path: Path,
    progress_callback: Callable[[dict[str, Any]], None] | None = None,
) -> RenameResult:
    manifest = load_manifest(manifest_path)
    if not manifest.get("dry_run"):
        raise ValueError("Only an unapplied preview manifest can be approved")
    return apply_rename_manifest(manifest, manifest_path.resolve(), progress_callback=progress_callback)


def rollback_renames(manifest_path: Path) -> list[dict[str, str]]:
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
    return preview_renames(
        input_directory,
        config,
        force_ai=force_ai,
        ai_responses=ai_responses,
        recursive=recursive,
        analyze_ai=analyze_ai,
    )
