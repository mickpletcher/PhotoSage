from __future__ import annotations

import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from dateutil import parser
from PIL import ExifTags, Image

try:
    from pillow_heif import register_heif_opener
except ImportError:
    register_heif_opener = None

try:
    import exifread
except ImportError:
    exifread = None

from photosage.metadata.gps_parser import parse_gps_info
from photosage.scanner import SUPPORTED_IMAGE_EXTENSIONS

logger = logging.getLogger(__name__)

if register_heif_opener:
    register_heif_opener()


@dataclass(slots=True)
class PhotoMetadata:
    """Normalized metadata extracted from a photo file."""

    path: Path
    original_filename: str
    extension: str
    file_size: int
    created_date: datetime | None
    modified_date: datetime | None
    date_taken: datetime | None
    width: int | None = None
    height: int | None = None
    orientation: str | None = None
    color_mode: str | None = None
    exif_datetime_original: datetime | None = None
    exif_datetime_digitized: datetime | None = None
    camera_make: str | None = None
    camera_model: str | None = None
    lens_model: str | None = None
    focal_length: str | None = None
    iso: int | None = None
    shutter_speed: str | None = None
    aperture: str | None = None
    exposure_program: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    altitude: float | None = None
    gps_timestamp: datetime | None = None
    title: str | None = None
    description: str | None = None
    keywords: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    raw_metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Return metadata as a JSON friendly dictionary with compatibility aliases."""
        data = asdict(self)
        data["path"] = str(self.path)
        for key in ("created_date", "modified_date", "date_taken", "exif_datetime_original", "exif_datetime_digitized", "gps_timestamp"):
            data[key] = data[key].isoformat(timespec="seconds") if data[key] else None

        data["absolute_path"] = str(self.path)
        data["file_extension"] = self.extension
        data["exif_date_taken"] = data["date_taken"]
        data["gps_latitude"] = self.latitude
        data["gps_longitude"] = self.longitude
        data["image_width"] = self.width
        data["image_height"] = self.height
        return data


def _parse_datetime(value: Any) -> datetime | None:
    if not value:
        return None

    text = str(value).strip().strip("\x00")
    if not text:
        return None

    try:
        return parser.parse(text.replace(":", "-", 2))
    except (ValueError, OverflowError, TypeError):
        return None


def _clean_text(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, bytes):
        value = value.decode("utf-16", errors="ignore") if b"\x00" in value else value.decode("utf-8", errors="ignore")
    if isinstance(value, tuple):
        chars = [chr(part) for part in value if isinstance(part, int) and part != 0]
        value = "".join(chars)
    text = str(value).replace("\x00", "").strip()
    return text or None


def _split_keywords(value: Any) -> list[str]:
    text = _clean_text(value)
    if not text:
        return []
    return [part.strip() for part in text.replace(";", ",").split(",") if part.strip()]


def _to_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


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


def _read_exifread_tags(image_path: Path) -> dict[str, str]:
    if exifread is None:
        return {}

    try:
        with image_path.open("rb") as handle:
            tags = exifread.process_file(handle, details=False)
    except Exception as error:
        logger.warning("exifread failed for %s: %s", image_path, error)
        return {}

    return {key: str(value) for key, value in tags.items()}


def _first(raw: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        value = raw.get(key)
        if value not in (None, "", []):
            return value
    return None


def extract_photo_metadata(image_path: Path) -> PhotoMetadata | None:
    """Extract normalized metadata from a supported image file."""
    image_path = image_path.resolve()
    extension = image_path.suffix.lower().lstrip(".")

    if image_path.suffix.lower() not in SUPPORTED_IMAGE_EXTENSIONS:
        logger.warning("skipped unsupported file: %s", image_path)
        return None

    stat = image_path.stat()
    created_date = datetime.fromtimestamp(stat.st_ctime)
    modified_date = datetime.fromtimestamp(stat.st_mtime)
    raw_metadata: dict[str, Any] = {}
    width = height = None
    color_mode = orientation = None

    try:
        with Image.open(image_path) as image:
            width, height = image.size
            color_mode = image.mode
            raw_metadata.update(_decode_exif(image.getexif()))
            raw_metadata.update(dict(image.info))
    except Exception as error:
        logger.warning("image metadata read failed for %s: %s", image_path, error)

    raw_metadata.update(_read_exifread_tags(image_path))
    gps = parse_gps_info(raw_metadata.get("GPSInfo") if isinstance(raw_metadata.get("GPSInfo"), dict) else None)

    exif_datetime_original = _parse_datetime(_first(raw_metadata, "DateTimeOriginal", "EXIF DateTimeOriginal"))
    exif_datetime_digitized = _parse_datetime(_first(raw_metadata, "DateTimeDigitized", "EXIF DateTimeDigitized"))
    date_taken = exif_datetime_original or exif_datetime_digitized

    metadata = PhotoMetadata(
        path=image_path,
        original_filename=image_path.name,
        extension=extension,
        file_size=stat.st_size,
        created_date=created_date,
        modified_date=modified_date,
        date_taken=date_taken,
        width=width,
        height=height,
        orientation=_clean_text(_first(raw_metadata, "Orientation", "Image Orientation")),
        color_mode=color_mode,
        exif_datetime_original=exif_datetime_original,
        exif_datetime_digitized=exif_datetime_digitized,
        camera_make=_clean_text(_first(raw_metadata, "Make", "Image Make")),
        camera_model=_clean_text(_first(raw_metadata, "Model", "Image Model")),
        lens_model=_clean_text(_first(raw_metadata, "LensModel", "EXIF LensModel")),
        focal_length=_clean_text(_first(raw_metadata, "FocalLength", "EXIF FocalLength")),
        iso=_to_int(_first(raw_metadata, "ISOSpeedRatings", "PhotographicSensitivity", "EXIF ISOSpeedRatings")),
        shutter_speed=_clean_text(_first(raw_metadata, "ExposureTime", "EXIF ExposureTime", "ShutterSpeedValue")),
        aperture=_clean_text(_first(raw_metadata, "FNumber", "EXIF FNumber", "ApertureValue")),
        exposure_program=_clean_text(_first(raw_metadata, "ExposureProgram", "EXIF ExposureProgram")),
        latitude=gps["latitude"],
        longitude=gps["longitude"],
        altitude=gps["altitude"],
        gps_timestamp=gps["gps_timestamp"],
        title=_clean_text(_first(raw_metadata, "XPTitle", "Title", "ImageDescription")),
        description=_clean_text(_first(raw_metadata, "XPComment", "UserComment", "Description")),
        keywords=_split_keywords(_first(raw_metadata, "XPKeywords", "Keywords")),
        tags=_split_keywords(_first(raw_metadata, "XPKeywords", "Keywords")),
        raw_metadata=raw_metadata,
    )

    logger.info("extracted metadata for %s", image_path)
    return metadata


def extract_metadata(image_path: Path) -> dict[str, Any]:
    """Extract metadata as a dictionary for the rename pipeline."""
    metadata = extract_photo_metadata(image_path)
    if metadata is None:
        return {}
    return metadata.to_dict()
