from __future__ import annotations

from pathlib import Path
from typing import Any
from xml.etree import ElementTree

from PIL import Image


def sidecar_path_for_image(image_path: Path) -> Path:
    """Return the expected XMP sidecar path for an image."""
    return image_path.with_suffix(".xmp")


def read_xmp_sidecar(image_path: Path) -> dict[str, Any]:
    """Read the XMP sidecar associated with an image when present."""
    sidecar = sidecar_path_for_image(image_path)
    if not sidecar.exists():
        return read_embedded_xmp(image_path)
    return read_xmp(sidecar)


def read_xmp(xmp_path: Path) -> dict[str, Any]:
    """Parse useful Lightroom and XMP fields from a sidecar file."""
    return _parse_xmp_text(xmp_path.read_text(encoding="utf-8"), str(xmp_path))


def read_embedded_xmp(image_path: Path) -> dict[str, Any]:
    """Read embedded XMP metadata from image info when available."""
    try:
        with Image.open(image_path) as image:
            raw_xmp = image.info.get("XML:com.adobe.xmp") or image.info.get("xmp")
    except Exception:
        raw_xmp = None

    if not raw_xmp:
        return {"xmp_path": None, "xmp_detected": False}
    if isinstance(raw_xmp, bytes):
        raw_xmp = raw_xmp.decode("utf-8", errors="ignore")
    return _parse_xmp_text(str(raw_xmp), str(image_path))


def _parse_xmp_text(xmp_text: str, source: str) -> dict[str, Any]:
    start = xmp_text.find("<x:xmpmeta")
    if start == -1:
        start = xmp_text.find("<rdf:RDF")
    if start > 0:
        xmp_text = xmp_text[start:]
    try:
        root = ElementTree.fromstring(xmp_text)
    except ElementTree.ParseError as error:
        raise ValueError(f"Invalid XMP data: {source}") from error

    result: dict[str, Any] = {
        "xmp_path": source,
        "xmp_detected": True,
        "title": None,
        "caption": None,
        "keywords": [],
        "rating": None,
        "color_label": None,
        "creator": None,
        "copyright": None,
        "gps_latitude": None,
        "gps_longitude": None,
        "lightroom_collections": [],
    }

    descriptions = [element for element in root.iter() if _local_name(element.tag) == "Description"]
    for description in descriptions:
        attrs = {_local_name(key): value for key, value in description.attrib.items()}
        result["rating"] = result["rating"] or _to_int(attrs.get("Rating"))
        result["color_label"] = result["color_label"] or attrs.get("Label")
        result["creator"] = result["creator"] or attrs.get("Creator")
        result["copyright"] = result["copyright"] or attrs.get("Rights") or attrs.get("Copyright")
        result["gps_latitude"] = result["gps_latitude"] if result["gps_latitude"] is not None else _to_float(attrs.get("GPSLatitude"))
        result["gps_longitude"] = result["gps_longitude"] if result["gps_longitude"] is not None else _to_float(attrs.get("GPSLongitude"))
        collection = attrs.get("Collection") or attrs.get("HierarchicalSubject")
        if collection:
            result["lightroom_collections"].extend(_split_values(collection))

    result["title"] = _find_text(root, "title") or result["title"]
    result["caption"] = _find_text(root, "description") or result["caption"]
    creator = _find_text(root, "creator")
    if creator:
        result["creator"] = creator
    copyright_text = _find_text(root, "rights")
    if copyright_text:
        result["copyright"] = copyright_text
    result["keywords"] = sorted(set(_find_bag_values(root, "subject") + result["keywords"]))
    result["lightroom_collections"] = sorted(set(result["lightroom_collections"]))
    return result


def _local_name(tag: str) -> str:
    return tag.split("}", 1)[-1].split(":", 1)[-1]


def _find_text(root: ElementTree.Element, name: str) -> str | None:
    for element in root.iter():
        if _local_name(element.tag).lower() != name.lower():
            continue
        if name.lower() == "description" and "1999/02/22-rdf-syntax-ns" in element.tag:
            continue
        values = [child.text.strip() for child in element.iter() if _local_name(child.tag) == "li" and child.text and child.text.strip()]
        if values:
            return values[0]
        if element.text and element.text.strip():
            return element.text.strip()
    return None


def _find_bag_values(root: ElementTree.Element, name: str) -> list[str]:
    values: list[str] = []
    for element in root.iter():
        if _local_name(element.tag).lower() == name.lower():
            values.extend(child.text.strip() for child in element.iter() if _local_name(child.tag) == "li" and child.text and child.text.strip())
    return values


def _split_values(value: str) -> list[str]:
    return [part.strip() for part in value.replace("|", ",").replace(";", ",").split(",") if part.strip()]


def _to_int(value: str | None) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except ValueError:
        return None


def _to_float(value: str | None) -> float | None:
    if value in (None, ""):
        return None
    text = str(value).strip()
    try:
        return float(text)
    except ValueError:
        return None
