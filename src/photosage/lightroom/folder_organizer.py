from __future__ import annotations

from pathlib import Path

from photosage.lightroom.metadata_mapper import category_from_metadata
from photosage.organization.policies import destination_for_policy
from photosage.rename.filename_builder import date_for_filename
from photosage.rename.sanitizer import sanitize_part


def category_for_photo(metadata: dict, ai_response: dict | None = None, preset_category: str | None = None) -> str:
    """Return the folder category for a photo."""
    return preset_category or category_from_metadata(metadata, ai_response)


def destination_directory(root: Path, metadata: dict, category: str) -> Path:
    """Build a Lightroom export organization destination folder."""
    date = date_for_filename(metadata)
    year = date[:4] if date and date != "unknown-date" else "Unknown-Year"
    month = date[:7] if len(date) >= 7 else "Unknown-Month"
    safe_category = sanitize_part(category, "uncategorized").title().replace("-", " ")
    return root / year / month / safe_category


def organized_destination(root: Path, metadata: dict, filename: str, ai_response: dict | None = None, preset_category: str | None = None) -> Path:
    """Return the organized destination path for a renamed photo."""
    category = category_for_photo(metadata, ai_response, preset_category)
    return destination_directory(root, metadata, category) / filename


def policy_destination(
    root: Path,
    metadata: dict,
    filename: str,
    ai_response: dict | None = None,
    policy: str = "date-first",
    keyword_map: dict[str, str] | None = None,
) -> Path:
    return destination_for_policy(root, metadata, ai_response, filename, policy, keyword_map)
