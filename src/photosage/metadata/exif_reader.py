from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from PIL import ExifTags, Image

from photosage.metadata.gps_parser import parse_gps_info


def _safe_iso(timestamp: float) -> str:
    return datetime.fromtimestamp(timestamp).isoformat(timespec="seconds")


def _decode_exif(raw_exif: Any) -> dict[str, Any]:
    decoded: dict[str, Any] = {}
    if not raw_exif:
        return decoded

    for key, value in raw_exif.items():
        name = ExifTags.TAGS.get(key, str(key))
        if name == "GPSInfo" and isinstance(value, dict):
            decoded[name] = {
                ExifTags.GPSTAGS.get(gps_key, str(gps_key)): gps_value
                for gps_key, gps_value in value.items()
            }
        else:
            decoded[name] = value
    return decoded


def extract_metadata(image_path: Path) -> dict[str, Any]:
    """Extract filesystem and available image metadata."""
    stat = image_path.stat()
    metadata: dict[str, Any] = {
        "original_filename": image_path.name,
        "file_extension": image_path.suffix.lower().lstrip("."),
        "file_size": stat.st_size,
        "created_date": _safe_iso(stat.st_ctime),
        "modified_date": _safe_iso(stat.st_mtime),
        "exif_date_taken": None,
        "gps_latitude": None,
        "gps_longitude": None,
        "camera_make": None,
        "camera_model": None,
        "lens_model": None,
        "image_width": None,
        "image_height": None,
        "title": None,
        "description": None,
        "keywords": [],
    }

    try:
        with Image.open(image_path) as image:
            metadata["image_width"], metadata["image_height"] = image.size
            exif = _decode_exif(image.getexif())
    except Exception:
        return metadata

    metadata["exif_date_taken"] = exif.get("DateTimeOriginal") or exif.get("DateTimeDigitized")
    metadata["camera_make"] = exif.get("Make")
    metadata["camera_model"] = exif.get("Model")
    metadata["lens_model"] = exif.get("LensModel")
    metadata["title"] = exif.get("ImageDescription")
    metadata["description"] = exif.get("XPComment") or exif.get("UserComment")

    latitude, longitude = parse_gps_info(exif.get("GPSInfo"))
    metadata["gps_latitude"] = latitude
    metadata["gps_longitude"] = longitude
    return metadata

