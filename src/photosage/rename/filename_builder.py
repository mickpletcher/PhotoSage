from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from photosage.metadata.filename_from_metadata import location_from_metadata, subject_from_metadata
from photosage.rename.sanitizer import sanitize_filename, sanitize_part


def _parse_date(value: str | None) -> str | None:
    if not value:
        return None

    try:
        return datetime.fromisoformat(value[:19]).date().isoformat()
    except ValueError:
        pass

    for fmt in ("%Y:%m:%d %H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(value[:19], fmt).date().isoformat()
        except ValueError:
            continue
    return None


def date_for_filename(metadata: dict[str, Any]) -> str:
    """Return the best available photo date for the filename."""
    return (
        _parse_date(metadata.get("exif_date_taken"))
        or _parse_date(metadata.get("modified_date"))
        or datetime.now().date().isoformat()
    )


def build_filename(
    metadata: dict[str, Any],
    ai_response: dict[str, Any] | None,
    counter: int,
    filename_format: str = "{date}_{location}_{subject}_{context}_{counter}",
) -> str:
    """Build a deterministic safe filename."""
    ai_response = ai_response or {}
    extension = metadata.get("file_extension") or Path(str(metadata.get("original_filename", "photo.jpg"))).suffix.lstrip(".")
    location = location_from_metadata(metadata) or ai_response.get("location_guess") or "unknown-location"
    subject = subject_from_metadata(metadata) if not ai_response.get("primary_subject") else ai_response["primary_subject"]
    context = ai_response.get("activity") or ai_response.get("environment") or metadata.get("camera_model") or "photo"

    values = {
        "date": date_for_filename(metadata),
        "location": sanitize_part(location, "unknown-location"),
        "subject": sanitize_part(subject, "photo"),
        "context": sanitize_part(context, "photo"),
        "counter": f"{counter:03d}",
    }
    stem = filename_format.format(**values)
    return sanitize_filename(f"{stem}.{extension}")
