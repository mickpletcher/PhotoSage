from __future__ import annotations

from typing import Any


def parse_gps_coordinate(value: Any, reference: str | None) -> float | None:
    """Convert EXIF GPS rational values into decimal degrees."""
    if not value:
        return None

    try:
        degrees = float(value[0])
        minutes = float(value[1])
        seconds = float(value[2])
    except (TypeError, ValueError, IndexError):
        return None

    result = degrees + (minutes / 60) + (seconds / 3600)
    if reference in {"S", "W"}:
        result *= -1
    return result


def parse_gps_info(gps_info: dict[str, Any] | None) -> tuple[float | None, float | None]:
    """Parse latitude and longitude from decoded EXIF GPS data."""
    if not gps_info:
        return None, None

    lat = parse_gps_coordinate(gps_info.get("GPSLatitude"), gps_info.get("GPSLatitudeRef"))
    lon = parse_gps_coordinate(gps_info.get("GPSLongitude"), gps_info.get("GPSLongitudeRef"))
    return lat, lon

