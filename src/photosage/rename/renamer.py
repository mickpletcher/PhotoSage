from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from photosage.config import AppConfig
from photosage.manifest.manifest_writer import create_manifest, write_manifest
from photosage.metadata.exif_reader import extract_metadata
from photosage.metadata.metadata_score import score_metadata
from photosage.providers.exceptions import ProviderError
from photosage.providers.provider_manager import ProviderManager
from photosage.rename.duplicate_handler import unique_destination
from photosage.rename.filename_builder import build_filename
from photosage.scanner import scan_images

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class RenameResult:
    manifest: dict[str, Any]
    manifest_path: Path | None


def build_rename_manifest(input_directory: Path, config: AppConfig, force_ai: bool = False, dry_run: bool = True) -> dict[str, Any]:
    """Build proposed rename operations without modifying files."""
    provider_manager = ProviderManager(config)
    provider_used = None
    files: list[dict[str, Any]] = []
    seen: set[Path] = set()

    for image_path in scan_images(input_directory):
        metadata = extract_metadata(image_path)
        metadata_score = score_metadata(metadata)
        ai_used = False
        ai_response = None

        if force_ai or metadata_score < config.metadata_threshold:
            try:
                ai_response = provider_manager.analyze_image(image_path, metadata)
                ai_used = True
                provider_used = ai_response.get("provider")
            except ProviderError as error:
                logger.warning("AI fallback failed for %s: %s", image_path, type(error).__name__)

        new_path = unique_destination(
            image_path.parent,
            lambda counter, metadata=metadata, ai_response=ai_response: build_filename(
                metadata,
                ai_response,
                counter,
                config.filename_format,
            ),
            seen,
        )

        logger.info("metadata score for %s: %s", image_path, metadata_score)
        logger.info("ai used for %s: %s", image_path, ai_used)
        logger.info("suggested filename for %s: %s", image_path, new_path.name)

        files.append(
            {
                "original_path": str(image_path),
                "new_path": str(new_path),
                "original_filename": image_path.name,
                "new_filename": new_path.name,
                "metadata_score": metadata_score,
                "ai_used": ai_used,
                "metadata": metadata,
                "ai_response": ai_response,
                "status": "planned" if dry_run else "pending",
            }
        )

    return create_manifest(
        input_directory=input_directory,
        dry_run=dry_run,
        provider_used=provider_used,
        metadata_threshold=config.metadata_threshold,
        files=files,
    )


def rename_files(input_directory: Path, config: AppConfig, apply: bool = False, force_ai: bool = False) -> RenameResult:
    """Preview or apply safe photo renames."""
    manifest = build_rename_manifest(input_directory, config, force_ai=force_ai, dry_run=not apply)
    manifest_path = write_manifest(manifest, config.manifest_directory)

    if not apply:
        return RenameResult(manifest=manifest, manifest_path=manifest_path)

    for item in manifest["files"]:
        original_path = Path(item["original_path"])
        new_path = Path(item["new_path"])

        if not original_path.exists():
            item["status"] = "missing"
            logger.warning("rename skipped missing file: %s", original_path)
            continue
        if new_path.exists():
            item["status"] = "overwrite-prevented"
            logger.warning("rename skipped overwrite risk: %s", new_path)
            continue

        new_path.parent.mkdir(parents=True, exist_ok=True)
        original_path.rename(new_path)
        item["status"] = "renamed"
        logger.info("applied rename: %s -> %s", original_path, new_path)

    write_manifest(manifest, config.manifest_directory)
    return RenameResult(manifest=manifest, manifest_path=manifest_path)
