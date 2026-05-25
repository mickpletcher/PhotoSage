from photosage.lightroom.metadata_mapper import category_from_metadata, lightroom_score_bonus, merge_lightroom_metadata


def test_merge_lightroom_metadata_preserves_exif_and_adds_xmp():
    metadata = {
        "original_filename": "IMG_0001.jpg",
        "camera_model": "Canon R5",
        "keywords": ["existing"],
        "gps_latitude": None,
        "gps_longitude": None,
    }
    xmp = {
        "title": "Orion Nebula",
        "caption": "Stacked telescope image",
        "keywords": ["astronomy", "deep sky"],
        "rating": 5,
        "gps_latitude": 36.0,
        "gps_longitude": -87.0,
    }

    merged = merge_lightroom_metadata(metadata, xmp)

    assert merged["camera_model"] == "Canon R5"
    assert merged["title"] == "Orion Nebula"
    assert merged["description"] == "Stacked telescope image"
    assert merged["gps_latitude"] == 36.0
    assert merged["gps_longitude"] == -87.0
    assert merged["keywords"] == ["astronomy", "deep sky", "existing"]


def test_lightroom_score_bonus_uses_xmp_confidence_fields():
    xmp = {"keywords": ["travel"], "title": "Paris", "caption": "Street scene", "rating": 4}

    assert lightroom_score_bonus(xmp) == 50


def test_category_from_metadata_prefers_lightroom_keywords():
    metadata = {"keywords": ["night sky", "astronomy"], "lightroom": {"lightroom_collections": ["Favorites"]}}

    assert category_from_metadata(metadata) == "Astrophotography"
