from __future__ import annotations

import json
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from dateutil import parser

VIDEO_EXTENSIONS = {".mp4", ".mov", ".m4v", ".avi", ".mkv", ".webm"}


def _creation_time(payload: dict[str, Any], modified: datetime) -> str:
    tags = payload.get("format", {}).get("tags", {})
    value = tags.get("creation_time") or tags.get("com.apple.quicktime.creationdate")
    if value:
        try:
            return parser.parse(str(value)).isoformat(timespec="seconds")
        except (ValueError, TypeError, OverflowError):
            pass
    return modified.isoformat(timespec="seconds")


def extract_video_metadata(video_path: Path) -> dict[str, Any]:
    video_path = video_path.resolve()
    stat = video_path.stat()
    modified = datetime.fromtimestamp(stat.st_mtime)
    payload: dict[str, Any] = {}
    ffprobe = shutil.which("ffprobe")
    if ffprobe:
        result = subprocess.run(
            [ffprobe, "-v", "error", "-show_format", "-show_streams", "-of", "json", str(video_path)],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        if result.returncode == 0:
            try:
                payload = json.loads(result.stdout)
            except json.JSONDecodeError:
                payload = {}
    video_stream = next((stream for stream in payload.get("streams", []) if stream.get("codec_type") == "video"), {})
    duration_value = payload.get("format", {}).get("duration") or video_stream.get("duration")
    try:
        duration = round(float(duration_value), 3) if duration_value is not None else None
    except (TypeError, ValueError):
        duration = None
    return {
        "path": str(video_path),
        "absolute_path": str(video_path),
        "original_filename": video_path.name,
        "extension": video_path.suffix.lower().lstrip("."),
        "file_extension": video_path.suffix.lower().lstrip("."),
        "file_size": stat.st_size,
        "created_date": datetime.fromtimestamp(stat.st_ctime).isoformat(timespec="seconds"),
        "modified_date": modified.isoformat(timespec="seconds"),
        "date_taken": _creation_time(payload, modified),
        "width": video_stream.get("width"),
        "height": video_stream.get("height"),
        "image_width": video_stream.get("width"),
        "image_height": video_stream.get("height"),
        "duration_seconds": duration,
        "codec": video_stream.get("codec_name"),
        "frame_rate": video_stream.get("avg_frame_rate"),
        "media_type": "video",
        "content_label": "video",
        "raw_metadata": payload,
    }


def extract_video_keyframe(video_path: Path, output_path: Path, second: float = 0) -> Path:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("ffmpeg is required for video keyframe extraction")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        [ffmpeg, "-v", "error", "-ss", str(max(0, second)), "-i", str(video_path), "-frames:v", "1", "-y", str(output_path)],
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    if result.returncode != 0 or not output_path.exists():
        raise RuntimeError(f"Video keyframe extraction failed: {result.stderr.strip()}")
    return output_path
