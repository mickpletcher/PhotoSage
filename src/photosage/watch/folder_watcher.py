from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any

from photosage.config import AppConfig
from photosage.manifest.manifest_writer import write_manifest
from photosage.rename.renamer import build_rename_manifest
from photosage.scanner import scan_images

logger = logging.getLogger(__name__)


def stable_files(input_directory: Path, recursive: bool = True, stable_seconds: float = 5.0) -> list[Path]:
    now = time.time()
    files: list[Path] = []
    for path in scan_images(input_directory, recursive=recursive):
        stat = path.stat()
        if now - stat.st_mtime >= stable_seconds and stat.st_size > 0:
            files.append(path)
        else:
            logger.info("watch skipped unstable file path=%s", path)
    return files


def build_approval_queue(input_directory: Path, config: AppConfig, recursive: bool = True, force_ai: bool = False) -> dict[str, Any]:
    manifest = build_rename_manifest(input_directory, config, force_ai=force_ai, dry_run=True, recursive=recursive, analyze_ai=False)
    stable = {str(path.resolve()) for path in stable_files(input_directory, recursive=recursive, stable_seconds=config.watch_stable_seconds)}
    manifest["watch_mode"] = True
    manifest["approval_required"] = True
    manifest["files"] = [item for item in manifest["files"] if item["original_path"] in stable]
    for item in manifest["files"]:
        item["approval_status"] = "queued"
    return manifest


def process_watch_once(
    input_directory: Path,
    config: AppConfig,
    apply: bool = False,
    recursive: bool = True,
    force_ai: bool = False,
) -> dict[str, Any]:
    stable = {str(path.resolve()) for path in stable_files(input_directory, recursive=recursive, stable_seconds=config.watch_stable_seconds)}
    if apply:
        manifest = build_rename_manifest(input_directory, config, force_ai=force_ai, dry_run=False, recursive=recursive, analyze_ai=False)
        manifest["watch_mode"] = True
        manifest["approval_required"] = False
        manifest["files"] = [item for item in manifest["files"] if item["original_path"] in stable]
        manifest_path = write_manifest(manifest, config.manifest_directory)
        for item in manifest["files"]:
            original_path = Path(item["original_path"])
            new_path = Path(item["new_path"])
            if item["status"] != "pending":
                continue
            if original_path == new_path:
                item["status"] = "unchanged"
            elif not original_path.exists():
                item["status"] = "missing"
            elif new_path.exists():
                item["status"] = "overwrite-prevented"
            else:
                try:
                    new_path.parent.mkdir(parents=True, exist_ok=True)
                    original_path.rename(new_path)
                    item["status"] = "renamed"
                except OSError as error:
                    item["status"] = "error"
                    item["error"] = str(error)
        write_manifest(manifest, config.manifest_directory, manifest_path)
        manifest["manifest_path"] = str(manifest_path)
        return manifest

    manifest = build_approval_queue(input_directory, config, recursive=recursive, force_ai=force_ai)
    manifest_path = write_manifest(manifest, config.manifest_directory)
    manifest["manifest_path"] = str(manifest_path)
    return manifest
