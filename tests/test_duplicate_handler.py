from photosage.rename.duplicate_handler import existing_names, unique_destination


def test_unique_destination_skips_existing_files(tmp_path):
    (tmp_path / "photo_001.jpg").write_text("existing", encoding="utf-8")

    destination = unique_destination(tmp_path, lambda counter: f"photo_{counter:03d}.jpg")

    assert destination.name == "photo_002.jpg"


def test_unique_destination_tracks_seen_paths(tmp_path):
    seen = set()

    first = unique_destination(tmp_path, lambda counter: f"photo_{counter:03d}.jpg", seen)
    second = unique_destination(tmp_path, lambda counter: f"photo_{counter:03d}.jpg", seen)

    assert first.name == "photo_001.jpg"
    assert second.name == "photo_002.jpg"


def test_existing_names_returns_lowercase_names(tmp_path):
    (tmp_path / "Photo.JPG").write_text("existing", encoding="utf-8")

    assert existing_names(tmp_path) == {"photo.jpg"}


def test_unique_destination_allows_current_file_name(tmp_path):
    original = tmp_path / "photo_001.jpg"
    original.write_text("existing", encoding="utf-8")

    destination = unique_destination(tmp_path, lambda counter: f"photo_{counter:03d}.jpg", original_path=original)

    assert destination == original
