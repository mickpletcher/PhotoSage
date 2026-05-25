from photosage.metadata.metadata_score import has_useful_original_filename, metadata_is_sufficient, score_metadata


def test_score_metadata_full_signal_reaches_threshold():
    metadata = {
        "exif_date_taken": "2026:05:25 12:00:00",
        "gps_latitude": 36.4,
        "gps_longitude": -87.8,
        "keywords": ["container"],
        "original_filename": "container-build.jpg",
        "camera_make": "Canon",
        "camera_model": "R5",
        "image_width": 4000,
        "image_height": 3000,
    }

    assert score_metadata(metadata) == 100
    assert metadata_is_sufficient(metadata, 70) is True


def test_score_metadata_low_signal_requires_ai():
    metadata = {"original_filename": "IMG_0001.jpg"}

    assert score_metadata(metadata) == 0
    assert metadata_is_sufficient(metadata, 70) is False


def test_useful_filename_detection():
    assert has_useful_original_filename("shipping-container-build.jpg") is True
    assert has_useful_original_filename("IMG_0001.jpg") is False

