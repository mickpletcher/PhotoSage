from __future__ import annotations

from pathlib import Path
from typing import Any


def subject_from_metadata(metadata: dict[str, Any]) -> str:
    """Pick the best subject candidate from metadata."""
    keywords = metadata.get("keywords") or []
    if keywords:
        return str(keywords[0])
    for key in ("title", "description"):
        if metadata.get(key):
            return str(metadata[key])
    return Path(str(metadata.get("original_filename", "photo"))).stem


def location_from_metadata(metadata: dict[str, Any]) -> str | None:
    """Return a deterministic location token when metadata already has one."""
    if metadata.get("location"):
        return str(metadata["location"])
    if metadata.get("gps_latitude") is not None and metadata.get("gps_longitude") is not None:
        return "gps-location"
    return None

