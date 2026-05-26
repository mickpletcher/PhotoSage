from __future__ import annotations

from pathlib import Path
from typing import Any

from dateutil import parser

from photosage.rename.sanitizer import sanitize_filename, sanitize_part


def _get(metadata: Any, key: str) -> Any:
    if isinstance(metadata, dict):
        return metadata.get(key)
    return getattr(metadata, key, None)


def subject_from_metadata(metadata: Any) -> str:
    """Pick the best subject candidate from metadata."""
    for key in ("astro_target", "content_label", "document_type", "media_type"):
        value = _get(metadata, key)
        if value and value != "photo":
            return str(value)
    keywords = _get(metadata, "keywords") or _get(metadata, "tags") or []
    if keywords:
        return str(keywords[0])
    for key in ("title", "description"):
        if _get(metadata, key):
            return str(_get(metadata, key))
    return Path(str(_get(metadata, "original_filename") or "photo")).stem


def location_from_metadata(metadata: Any) -> str | None:
    """Return a deterministic location token when metadata already has one."""
    if _get(metadata, "location"):
        return str(_get(metadata, "location"))
    if (
        (_get(metadata, "latitude") is not None and _get(metadata, "longitude") is not None)
        or (_get(metadata, "gps_latitude") is not None and _get(metadata, "gps_longitude") is not None)
    ):
        return "gps-location"
    if _get(metadata, "media_type") == "screenshot":
        return "digital"
    if _get(metadata, "media_type") == "document":
        return "document"
    return None


def date_from_metadata(metadata: Any) -> str:
    """Return YYYY-MM-DD from date taken first, then modified date."""
    value = _get(metadata, "date_taken") or _get(metadata, "exif_date_taken") or _get(metadata, "modified_date")
    if hasattr(value, "date"):
        return value.date().isoformat()
    if value:
        try:
            return parser.parse(str(value)).date().isoformat()
        except (ValueError, OverflowError, TypeError):
            try:
                return parser.parse(str(value).replace(":", "-", 2)).date().isoformat()
            except (ValueError, OverflowError, TypeError):
                pass
    return "unknown-date"


def filename_from_metadata(metadata: Any, counter: int = 1, max_length: int = 180) -> str:
    """Build a safe filename using metadata only."""
    extension = _get(metadata, "extension") or _get(metadata, "file_extension") or Path(str(_get(metadata, "original_filename") or "photo.jpg")).suffix.lstrip(".")
    context = (
        _get(metadata, "astro_telescope")
        or _get(metadata, "astro_filter")
        or _get(metadata, "source_app")
        or _get(metadata, "document_type")
        or _get(metadata, "camera_model")
        or _get(metadata, "camera_make")
        or "photo"
    )
    parts = [
        date_from_metadata(metadata),
        sanitize_part(location_from_metadata(metadata) or "unknown-location"),
        sanitize_part(subject_from_metadata(metadata)),
        sanitize_part(context),
        f"{counter:03d}",
    ]
    return sanitize_filename(f"{'_'.join(parts)}.{extension}", max_length=max_length)
