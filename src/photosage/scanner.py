from __future__ import annotations

import logging
from pathlib import Path

SUPPORTED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".heic", ".webp", ".tiff"}

logger = logging.getLogger(__name__)


def scan_images(input_directory: Path) -> list[Path]:
    """Return supported image files under an input directory."""
    files: list[Path] = []
    for path in input_directory.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS:
            logger.info("scanned file: %s", path)
            files.append(path)
        else:
            logger.info("skipped unsupported file: %s", path)
    return files

