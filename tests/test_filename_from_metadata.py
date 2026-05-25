from datetime import datetime

from photosage.metadata.exif_reader import PhotoMetadata
from photosage.metadata.filename_from_metadata import date_from_metadata, filename_from_metadata


def test_metadata_only_filename_uses_dataclass_fields(tmp_path):
    metadata = PhotoMetadata(
        path=tmp_path / "IMG_0001.jpg",
        original_filename="IMG_0001.jpg",
        extension="jpg",
        file_size=100,
        created_date=None,
        modified_date=datetime(2026, 5, 24, 10, 0, 0),
        date_taken=datetime(2026, 5, 25, 12, 0, 0),
        width=100,
        height=100,
        camera_model="Canon R5",
        latitude=36.5,
        longitude=-87.75,
        keywords=["shipping container"],
    )

    assert filename_from_metadata(metadata) == "2026-05-25_gps-location_shipping-container_canon-r5_001.jpg"


def test_date_from_metadata_handles_iso_and_exif_strings():
    assert date_from_metadata({"modified_date": "2026-05-20T10:00:00"}) == "2026-05-20"
    assert date_from_metadata({"exif_date_taken": "2026:05:25 14:22:00"}) == "2026-05-25"
