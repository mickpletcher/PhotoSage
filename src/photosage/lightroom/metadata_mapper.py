from __future__ import annotations

from copy import deepcopy
from typing import Any


def merge_lightroom_metadata(metadata: dict[str, Any], xmp_metadata: dict[str, Any]) -> dict[str, Any]:
    """Merge Lightroom XMP metadata into PhotoSage metadata without discarding EXIF."""
    merged = deepcopy(metadata)
    merged["lightroom"] = xmp_metadata
    merged["title"] = xmp_metadata.get("title") or merged.get("title")
    merged["description"] = xmp_metadata.get("caption") or merged.get("description")

    keywords = list(merged.get("keywords") or [])
    keywords.extend(xmp_metadata.get("keywords") or [])
    keywords.extend(xmp_metadata.get("lightroom_collections") or [])
    merged["keywords"] = sorted({keyword for keyword in keywords if keyword})
    merged["tags"] = merged["keywords"]

    if xmp_metadata.get("gps_latitude") is not None and merged.get("gps_latitude") is None:
        merged["gps_latitude"] = xmp_metadata["gps_latitude"]
    if xmp_metadata.get("gps_longitude") is not None and merged.get("gps_longitude") is None:
        merged["gps_longitude"] = xmp_metadata["gps_longitude"]

    merged["lightroom_rating"] = xmp_metadata.get("rating")
    merged["lightroom_color_label"] = xmp_metadata.get("color_label")
    merged["creator"] = xmp_metadata.get("creator")
    merged["copyright"] = xmp_metadata.get("copyright")
    return merged


def lightroom_score_bonus(xmp_metadata: dict[str, Any]) -> int:
    """Return additional score from Lightroom metadata."""
    score = 0
    if xmp_metadata.get("keywords"):
        score += 20
    if xmp_metadata.get("title"):
        score += 15
    if xmp_metadata.get("caption"):
        score += 10
    if xmp_metadata.get("rating") is not None:
        score += 5
    return score


def category_from_metadata(metadata: dict[str, Any], ai_response: dict[str, Any] | None = None) -> str:
    """Pick an organization category from metadata and optional AI response."""
    ai_response = ai_response or {}
    candidates = []
    candidates.extend(metadata.get("keywords") or [])
    candidates.extend((metadata.get("lightroom") or {}).get("lightroom_collections") or [])
    candidates.extend(ai_response.get("tags") or [])
    candidates.extend([ai_response.get("activity"), ai_response.get("environment"), ai_response.get("primary_subject")])

    mapping = {
        "astro": "Astrophotography",
        "astronomy": "Astrophotography",
        "moon": "Astrophotography",
        "solar": "Astrophotography",
        "nebula": "Astrophotography",
        "wildlife": "Wildlife",
        "bird": "Wildlife",
        "travel": "Travel",
        "hiking": "Travel",
        "landscape": "Landscape",
        "construction": "Construction",
        "container": "Construction",
        "architecture": "Architecture",
        "family": "Family",
        "portrait": "Portraits",
        "pet": "Pets",
        "vehicle": "Vehicles",
        "screenshot": "Screenshots",
        "document": "Documents",
    }

    for candidate in candidates:
        text = str(candidate or "").lower()
        for token, category in mapping.items():
            if token in text:
                return category
    return "Uncategorized"
