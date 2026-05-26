from pathlib import Path

from PIL import Image

from photosage.gui.performance import ThumbnailCache, add_recent_manifest, recent_manifests


def test_thumbnail_cache_creates_thumbnail(tmp_path):
    image_path = tmp_path / "photo.jpg"
    Image.new("RGB", (256, 256), (10, 20, 30)).save(image_path)

    thumbnail = ThumbnailCache(tmp_path / "thumbs", size=64).thumbnail_for(image_path)

    assert thumbnail is not None
    assert thumbnail.exists()


def test_recent_manifests_tracks_latest_first(tmp_path):
    recent_file = tmp_path / "recent.json"
    first = tmp_path / "first.json"
    second = tmp_path / "second.json"

    add_recent_manifest(recent_file, first)
    add_recent_manifest(recent_file, second)

    assert recent_manifests(recent_file) == [second.resolve(), first.resolve()]
