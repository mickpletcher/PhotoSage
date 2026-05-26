from __future__ import annotations

from pathlib import Path
from typing import Any

from photosage.rename.filename_builder import date_for_filename
from photosage.rename.sanitizer import sanitize_part


def destination_for_policy(
    root: Path,
    metadata: dict[str, Any],
    ai_response: dict[str, Any] | None,
    filename: str,
    policy: str = "date-first",
    keyword_map: dict[str, str] | None = None,
) -> Path:
    ai_response = ai_response or {}
    keyword_map = keyword_map or {}
    date = date_for_filename(metadata)
    year = date[:4]
    month = date[:7]
    location = sanitize_part(metadata.get("location") or ai_response.get("location_guess") or "unknown-location")
    project = _project(metadata, ai_response, keyword_map)

    match policy:
        case "location-first":
            return root / location / year / month / filename
        case "project-first":
            return root / project / year / month / filename
        case "custom":
            return root / project / filename
        case _:
            return root / year / month / project / filename


def _project(metadata: dict[str, Any], ai_response: dict[str, Any], keyword_map: dict[str, str]) -> str:
    keywords = [str(value).lower() for value in (metadata.get("keywords") or metadata.get("tags") or [])]
    for keyword in keywords:
        if keyword in keyword_map:
            return sanitize_part(keyword_map[keyword])
    return sanitize_part(
        ai_response.get("activity")
        or ai_response.get("primary_subject")
        or metadata.get("content_label")
        or metadata.get("document_type")
        or "uncategorized"
    )
