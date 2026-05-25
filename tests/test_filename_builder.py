from photosage.rename.filename_builder import build_filename


def test_build_filename_uses_exif_date_and_ai_context():
    metadata = {
        "original_filename": "IMG_0001.jpg",
        "file_extension": "jpg",
        "exif_date_taken": "2026:05:25 14:22:00",
        "modified_date": "2026-05-24T10:00:00",
        "gps_latitude": None,
        "gps_longitude": None,
    }
    ai_response = {
        "primary_subject": "Shipping Container",
        "activity": "Deck Construction",
        "environment": "Outdoor",
        "location_guess": "Dover TN",
    }

    assert build_filename(metadata, ai_response, 1) == "2026-05-25_dover-tn_shipping-container_deck-construction_001.jpg"


def test_build_filename_falls_back_to_modified_date():
    metadata = {
        "original_filename": "camera photo.png",
        "file_extension": "png",
        "exif_date_taken": None,
        "modified_date": "2026-05-20T10:00:00",
        "camera_model": "Pixel",
    }

    assert build_filename(metadata, None, 2).startswith("2026-05-20_unknown-location_camera-photo_pixel_002")


def test_build_filename_skips_empty_ai_fields_without_double_underscores():
    metadata = {
        "original_filename": "IMG_0001.jpg",
        "file_extension": "jpg",
        "modified_date": "2026-05-20T10:00:00",
    }
    ai_response = {"primary_subject": "", "secondary_subject": "Deck", "activity": ""}

    filename = build_filename(metadata, ai_response, 1)

    assert "__" not in filename
    assert filename == "2026-05-20_unknown-location_deck_photo_001.jpg"


def test_build_filename_uses_screenshot_labels_and_app_context():
    metadata = {
        "original_filename": "Screenshot 2026-05-25 Chrome.png",
        "file_extension": "png",
        "modified_date": "2026-05-25T10:00:00",
        "media_type": "screenshot",
        "content_label": "screenshot",
        "source_app": "chrome",
    }

    assert build_filename(metadata, None, 1) == "2026-05-25_digital_screenshot_chrome_001.png"


def test_build_filename_supports_document_tokens():
    metadata = {
        "original_filename": "receipt.jpg",
        "file_extension": "jpg",
        "modified_date": "2026-05-25T10:00:00",
        "media_type": "document",
        "content_label": "receipt",
        "document_type": "receipt",
        "ocr_summary": "Target receipt total",
    }

    filename = build_filename(metadata, None, 2, "{date}_{media_type}_{document_type}_{ocr_summary}_{counter}")

    assert filename == "2026-05-25_document_receipt_target-receipt-total_002.jpg"
