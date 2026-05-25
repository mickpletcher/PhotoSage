from photosage.lightroom.folder_organizer import category_for_photo, organized_destination


def test_organized_destination_uses_date_and_category(tmp_path):
    metadata = {
        "date_taken": "2026-05-25T20:00:00",
        "keywords": ["construction"],
    }

    destination = organized_destination(tmp_path, metadata, "photo_001.jpg")

    assert destination == tmp_path / "2026" / "2026-05" / "Construction" / "photo_001.jpg"


def test_category_for_photo_uses_preset_override():
    metadata = {"keywords": ["wildlife"]}

    assert category_for_photo(metadata, preset_category="Travel") == "Travel"
