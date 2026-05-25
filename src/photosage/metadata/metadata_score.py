from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class MetadataScore:
    """Metadata quality score with reason details."""

    total: int
    has_date_taken: bool
    has_gps: bool
    has_user_metadata: bool
    has_useful_filename: bool
    has_camera: bool
    has_dimensions: bool


def _get(metadata: Any, key: str) -> Any:
    if isinstance(metadata, dict):
        return metadata.get(key)
    return getattr(metadata, key, None)


def has_useful_original_filename(filename: str | None) -> bool:
    """Return true when the original filename contains human useful context."""
    if not filename:
        return False

    stem = Path(filename).stem.lower()
    generic_prefixes = ("img_", "dsc_", "dscf", "image", "photo", "pxl_", "screenshot", "mvimg_", "vid_")
    if stem.isdigit() or any(stem.startswith(prefix) for prefix in generic_prefixes):
        return False
    if len(stem) < 4:
        return False
    return any(char.isalpha() for char in stem)


def score_metadata_details(metadata: Any) -> MetadataScore:
    """Score metadata quality and return the reason breakdown."""
    has_date_taken = bool(_get(metadata, "date_taken") or _get(metadata, "exif_date_taken"))
    has_gps = (
        (_get(metadata, "latitude") is not None and _get(metadata, "longitude") is not None)
        or (_get(metadata, "gps_latitude") is not None and _get(metadata, "gps_longitude") is not None)
    )
    has_user_metadata = bool(_get(metadata, "title") or _get(metadata, "description") or _get(metadata, "keywords") or _get(metadata, "tags"))
    has_filename = has_useful_original_filename(_get(metadata, "original_filename"))
    has_camera = bool(_get(metadata, "camera_make") or _get(metadata, "camera_model"))
    has_dimensions = bool(
        (_get(metadata, "width") and _get(metadata, "height"))
        or (_get(metadata, "image_width") and _get(metadata, "image_height"))
    )

    score = 0
    score += 30 if has_date_taken else 0
    score += 30 if has_gps else 0
    score += 20 if has_user_metadata else 0
    score += 10 if has_filename else 0
    score += 5 if has_camera else 0
    score += 5 if has_dimensions else 0

    return MetadataScore(
        total=score,
        has_date_taken=has_date_taken,
        has_gps=has_gps,
        has_user_metadata=has_user_metadata,
        has_useful_filename=has_filename,
        has_camera=has_camera,
        has_dimensions=has_dimensions,
    )


def score_metadata(metadata: Any) -> int:
    """Score metadata quality for deciding whether AI fallback is needed."""
    return score_metadata_details(metadata).total



def metadata_is_sufficient(metadata: Any, threshold: int) -> bool:
    """Return true when metadata score meets the configured threshold."""
    return score_metadata(metadata) >= threshold
