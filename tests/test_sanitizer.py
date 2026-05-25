from photosage.rename.sanitizer import sanitize_filename, sanitize_part


def test_sanitize_part_lowercases_spaces_and_removes_unsafe_chars():
    assert sanitize_part("Dover TN / Deck Build!") == "dover-tn-deck-build"


def test_sanitize_filename_preserves_extension_and_limits_length():
    filename = sanitize_filename(f"{'A' * 250}.JPG", max_length=180)

    assert filename.endswith(".jpg")
    assert len(filename) <= 180


def test_sanitize_part_normalizes_unicode_and_removes_emoji():
    assert sanitize_part("São Francisco 📷") == "sao-francisco"


def test_sanitize_part_prevents_windows_reserved_names():
    assert sanitize_part("CON") == "con-file"
