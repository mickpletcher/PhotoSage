from __future__ import annotations

from datetime import datetime, time
from fractions import Fraction
from typing import Any

from dateutil import parser


def _to_float(value: Any) -> float:
    if hasattr(value, "num") and hasattr(value, "den"):
        return float(value.num) / float(value.den)
    if isinstance(value, tuple) and len(value) == 2:
        return float(Fraction(value[0], value[1]))
    return float(value)


def parse_gps_coordinate(value: Any, reference: str | None) -> float | None:
    """Convert EXIF GPS rational values into decimal degrees."""
    if not value:
        return None

    try:
        degrees = _to_float(value[0])
        minutes = _to_float(value[1])
        seconds = _to_float(value[2])
    except (TypeError, ValueError, IndexError):
        return None

    result = degrees + (minutes / 60) + (seconds / 3600)
    if reference in {"S", "W"}:
        result *= -1
    return result


def parse_gps_altitude(value: Any, reference: Any = None) -> float | None:
    """Convert EXIF GPS altitude into meters."""
    if value is None:
        return None

    try:
        altitude = _to_float(value)
    except (TypeError, ValueError, ZeroDivisionError):
        return None

    if str(reference) in {"1", "b'\\x01'"}:
        altitude *= -1
    return altitude


def parse_gps_timestamp(date_stamp: Any, time_stamp: Any) -> datetime | None:
    """Parse GPS date and time tags into a datetime."""
    if not date_stamp or not time_stamp:
        return None

    try:
        parts = [_to_float(part) for part in time_stamp]
        gps_time = time(int(parts[0]), int(parts[1]), int(parts[2]))
        gps_date = parser.parse(str(date_stamp).replace(":", "-")).date()
        return datetime.combine(gps_date, gps_time)
    except (TypeError, ValueError, IndexError, OverflowError):
        return None


def parse_gps_info(gps_info: dict[str, Any] | None) -> dict[str, Any]:
    """Parse GPS fields from decoded EXIF GPS data."""
    if not gps_info:
        return {"latitude": None, "longitude": None, "altitude": None, "gps_timestamp": None}

    lat = parse_gps_coordinate(gps_info.get("GPSLatitude"), gps_info.get("GPSLatitudeRef"))
    lon = parse_gps_coordinate(gps_info.get("GPSLongitude"), gps_info.get("GPSLongitudeRef"))
    altitude = parse_gps_altitude(gps_info.get("GPSAltitude"), gps_info.get("GPSAltitudeRef"))
    gps_timestamp = parse_gps_timestamp(gps_info.get("GPSDateStamp"), gps_info.get("GPSTimeStamp"))
    return {
        "latitude": lat,
        "longitude": lon,
        "altitude": altitude,
        "gps_timestamp": gps_timestamp,
    }
