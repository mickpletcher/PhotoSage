from __future__ import annotations

import html
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

from dateutil import parser

from photosage.metadata.exif_reader import extract_metadata
from photosage.scanner import scan_images


def build_browse_data(input_directory: Path, recursive: bool = True) -> dict[str, Any]:
    timeline: dict[str, list[dict[str, str]]] = defaultdict(list)
    map_points: list[dict[str, Any]] = []
    for path in scan_images(input_directory, recursive=recursive):
        metadata = extract_metadata(path)
        raw_date = metadata.get("date_taken") or metadata.get("modified_date")
        try:
            date = parser.parse(str(raw_date)) if raw_date else datetime.fromtimestamp(path.stat().st_mtime)
        except (ValueError, TypeError, OverflowError):
            date = datetime.fromtimestamp(path.stat().st_mtime)
        item = {"path": str(path.resolve()), "filename": path.name, "date": date.isoformat(timespec="seconds")}
        timeline[date.strftime("%Y-%m")].append(item)
        latitude = metadata.get("latitude") or metadata.get("gps_latitude")
        longitude = metadata.get("longitude") or metadata.get("gps_longitude")
        if latitude is not None and longitude is not None:
            map_points.append({**item, "latitude": float(latitude), "longitude": float(longitude)})
    return {
        "input_directory": str(input_directory.resolve()),
        "timeline": {key: value for key, value in sorted(timeline.items())},
        "map_points": map_points,
    }


def _svg_points(points: list[dict[str, Any]]) -> str:
    circles: list[str] = []
    for point in points:
        x = (point["longitude"] + 180) / 360 * 1000
        y = (90 - point["latitude"]) / 180 * 500
        title = html.escape(f"{point['filename']} ({point['latitude']:.5f}, {point['longitude']:.5f})")
        circles.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="5"><title>{title}</title></circle>')
    return "".join(circles)


def write_browse_report(data: dict[str, Any], output_html: Path, output_json: Path | None = None) -> None:
    output_html.parent.mkdir(parents=True, exist_ok=True)
    timeline_sections = []
    for month, items in data["timeline"].items():
        rows = "".join(f"<li><time>{html.escape(item['date'])}</time> {html.escape(item['filename'])}</li>" for item in items)
        timeline_sections.append(f"<details open><summary>{month} ({len(items)})</summary><ul>{rows}</ul></details>")
    document = f"""<!doctype html>
<html lang="en"><meta charset="utf-8"><title>PhotoSage Browser</title>
<style>body{{font:15px system-ui;background:#111;color:#eee;margin:2rem}}svg{{background:#1c2733;width:100%;height:auto}}circle{{fill:#68b5ff;opacity:.8}}summary{{font-size:1.1rem;margin-top:.7rem}}time{{color:#aaa}}</style>
<h1>PhotoSage Timeline</h1>{"".join(timeline_sections)}
<h1>Offline GPS Map</h1><p>{len(data["map_points"])} geotagged files. Hover a point for details.</p>
<svg viewBox="0 0 1000 500" role="img" aria-label="Offline coordinate plot">{_svg_points(data["map_points"])}</svg>
</html>"""
    output_html.write_text(document, encoding="utf-8")
    if output_json:
        output_json.parent.mkdir(parents=True, exist_ok=True)
        output_json.write_text(json.dumps(data, indent=2), encoding="utf-8")
