from PIL import Image

from photosage.metadata.exif_reader import PhotoMetadata, extract_metadata, extract_photo_metadata


def test_extract_photo_metadata_normalizes_filesystem_and_image_data(tmp_path):
    image_path = tmp_path / "container-build.jpg"
    Image.new("RGB", (120, 80), color="red").save(image_path)

    metadata = extract_photo_metadata(image_path)

    assert isinstance(metadata, PhotoMetadata)
    assert metadata.original_filename == "container-build.jpg"
    assert metadata.extension == "jpg"
    assert metadata.width == 120
    assert metadata.height == 80
    assert metadata.color_mode == "RGB"
    assert metadata.file_size > 0
    assert metadata.path.is_absolute()


def test_extract_metadata_returns_compatibility_aliases(tmp_path):
    image_path = tmp_path / "photo.png"
    Image.new("RGB", (10, 20), color="blue").save(image_path)

    metadata = extract_metadata(image_path)

    assert metadata["file_extension"] == "png"
    assert metadata["image_width"] == 10
    assert metadata["image_height"] == 20
    assert metadata["absolute_path"].endswith("photo.png")


def test_extract_photo_metadata_skips_unsupported_file(tmp_path):
    text_path = tmp_path / "notes.txt"
    text_path.write_text("not an image", encoding="utf-8")

    assert extract_photo_metadata(text_path) is None

