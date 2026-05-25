from __future__ import annotations

from pathlib import Path
from typing import Any


def has_useful_original_filename(filename: str | None) -> bool:
    """Return true when the original filename contains human useful context."""
    if not filename:
        return False

    stem = Path(filename).stem.lower()
    generic_prefixes = ("img_", "dsc_", "dscf", "image", "photo", "pxl_", "screenshot")
    if stem.isdigit() or any(stem.startswith(prefix) for prefix in generic_prefixes):
        return False
    return any(char.isalpha() for char in stem)


def score_metadata(metadata: dict[str, Any]) -> int:
    """Score metadata quality for deciding whether AI fallback is needed."""
    score = 0

    if metadata.get("exif_date_taken"):
        score += 30
    if metadata.get("gps_latitude") is not None and metadata.get("gps_longitude") is not None:
        score += 30
    if metadata.get("title") or metadata.get("description") or metadata.get("keywords"):
        score += 20
    if has_useful_original_filename(metadata.get("original_filename")):
        score += 10
    if metadata.get("camera_make") or metadata.get("camera_model"):
        score += 5
    if metadata.get("image_width") and metadata.get("image_height"):
        score += 5

    return score


def metadata_is_sufficient(metadata: dict[str, Any], threshold: int) -> bool:
    """Return true when metadata score meets the configured threshold."""
    return score_metadata(metadata) >= threshold

