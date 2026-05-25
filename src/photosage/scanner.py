from __future__ import annotations

import logging
from pathlib import Path

SUPPORTED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".heic", ".webp", ".tiff"}

logger = logging.getLogger(__name__)


def iter_files(input_directory: Path, recursive: bool = True) -> list[Path]:
    """Return files under a directory with deterministic ordering."""
    pattern = "**/*" if recursive else "*"
    return [path for path in sorted(input_directory.glob(pattern)) if path.is_file()]


def scan_images(input_directory: Path, recursive: bool = True) -> list[Path]:
    """Return supported image files under an input directory."""
    files: list[Path] = []
    for path in iter_files(input_directory, recursive=recursive):
        if path.suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS:
            logger.info("scanned file: %s", path)
            files.append(path)
        else:
            logger.warning("skipped unsupported file: %s", path)
    return files


def count_unsupported_files(input_directory: Path, recursive: bool = True) -> int:
    """Count unsupported files under a directory."""
    return sum(1 for path in iter_files(input_directory, recursive=recursive) if path.suffix.lower() not in SUPPORTED_IMAGE_EXTENSIONS)
