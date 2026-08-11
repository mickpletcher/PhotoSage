import json
from types import SimpleNamespace

from photosage.metadata.video import extract_video_keyframe, extract_video_metadata


def test_extract_video_metadata_uses_ffprobe(monkeypatch, tmp_path):
    video = tmp_path / "clip.mp4"
    video.write_bytes(b"video")
    payload = {
        "format": {"duration": "12.5", "tags": {"creation_time": "2026-01-02T03:04:05Z"}},
        "streams": [{"codec_type": "video", "codec_name": "h264", "width": 1920, "height": 1080}],
    }
    monkeypatch.setattr("photosage.metadata.video.shutil.which", lambda name: name)
    monkeypatch.setattr(
        "photosage.metadata.video.subprocess.run",
        lambda *args, **kwargs: SimpleNamespace(returncode=0, stdout=json.dumps(payload), stderr=""),
    )

    metadata = extract_video_metadata(video)

    assert metadata["media_type"] == "video"
    assert metadata["duration_seconds"] == 12.5
    assert metadata["codec"] == "h264"


def test_extract_video_keyframe_requires_output(monkeypatch, tmp_path):
    video = tmp_path / "clip.mp4"
    video.write_bytes(b"video")
    output = tmp_path / "frame.jpg"
    monkeypatch.setattr("photosage.metadata.video.shutil.which", lambda name: name)

    def run(*args, **kwargs):
        output.write_bytes(b"frame")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr("photosage.metadata.video.subprocess.run", run)
    assert extract_video_keyframe(video, output) == output
