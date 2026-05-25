from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from dateutil import parser

from photosage.metadata.filename_from_metadata import location_from_metadata, subject_from_metadata
from photosage.rename.sanitizer import sanitize_filename, sanitize_part

DEFAULT_FILENAME_FORMAT = "{date}_{location}_{subject}_{context}_{counter}"


def _get(metadata: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        value = metadata.get(key)
        if value not in (None, "", [], {}):
            return value
    return None


def _parse_date(value: Any) -> str | None:
    if not value:
        return None
    if hasattr(value, "date"):
        return value.date().isoformat()

    text = str(value).strip()
    try:
        return parser.parse(text).date().isoformat()
    except (ValueError, OverflowError, TypeError):
        try:
            return parser.parse(text.replace(":", "-", 2)).date().isoformat()
        except (ValueError, OverflowError, TypeError):
            return None


def date_for_filename(metadata: dict[str, Any]) -> str:
    """Return EXIF date first, then file modified date, then today's date."""
    return (
        _parse_date(_get(metadata, "date_taken", "exif_date_taken", "exif_datetime_original"))
        or _parse_date(_get(metadata, "modified_date"))
        or datetime.now().date().isoformat()
    )


def extension_for_filename(metadata: dict[str, Any]) -> str:
    """Return the original extension without a leading dot."""
    extension = _get(metadata, "extension", "file_extension")
    if not extension:
        extension = Path(str(metadata.get("original_filename") or "photo.jpg")).suffix.lstrip(".")
    return sanitize_part(str(extension).lstrip("."), "jpg")


def build_filename_components(metadata: dict[str, Any], ai_response: dict[str, Any] | None) -> dict[str, str]:
    """Build sanitized filename components from metadata and optional AI data."""
    ai_response = ai_response or {}
    location = location_from_metadata(metadata) or ai_response.get("location_guess") or "unknown-location"
    subject = (
        ai_response.get("primary_subject")
        or ai_response.get("secondary_subject")
        or subject_from_metadata(metadata)
        or "photo"
    )
    context = ai_response.get("activity") or ai_response.get("environment") or metadata.get("camera_model") or "photo"

    return {
        "date": sanitize_part(date_for_filename(metadata), "unknown-date"),
        "location": sanitize_part(location, "unknown-location"),
        "subject": sanitize_part(subject, "photo"),
        "context": sanitize_part(context, "photo"),
    }


def build_filename(
    metadata: dict[str, Any],
    ai_response: dict[str, Any] | None,
    counter: int,
    filename_format: str = DEFAULT_FILENAME_FORMAT,
    max_length: int = 180,
) -> str:
    """Build a deterministic safe filename."""
    components = build_filename_components(metadata, ai_response)
    components["counter"] = f"{counter:03d}"
    stem = filename_format.format(**components)
    stem = "_".join(part for part in stem.split("_") if part)
    return sanitize_filename(f"{stem}.{extension_for_filename(metadata)}", max_length=max_length)
