from photosage.metadata.mixed_media import classify_mixed_media


def test_classify_screenshot_with_source_app():
    metadata = {
        "original_filename": "Screenshot 2026-05-25 at 10.00.00 Chrome.png",
        "raw_metadata": {"Software": "Chrome"},
    }

    result = classify_mixed_media(metadata)

    assert result["media_type"] == "screenshot"
    assert result["content_label"] == "screenshot"
    assert result["source_app"] == "chrome"
    assert "screenshot" in result["mixed_media_tags"]


def test_classify_receipt_document_with_ocr_summary():
    metadata = {
        "original_filename": "receipt-target-order.jpg",
        "raw_metadata": {"OCRText": "Target receipt total 42 dollars paid by card"},
    }

    result = classify_mixed_media(metadata)

    assert result["media_type"] == "document"
    assert result["content_label"] == "receipt"
    assert result["document_type"] == "receipt"
    assert result["ocr_summary"] == "Target receipt total 42 dollars paid by card"


def test_classify_regular_photo_defaults_to_photo():
    metadata = {"original_filename": "IMG_0001.jpg", "camera_model": "Canon R5"}

    result = classify_mixed_media(metadata)

    assert result["media_type"] == "photo"
    assert result["content_label"] is None
    assert result["mixed_media_tags"] == []
