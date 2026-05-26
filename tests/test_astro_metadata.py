from pathlib import Path

from PIL import Image

from photosage.astro.metadata import capture_night, enrich_astro_metadata, group_by_capture_night, read_fits_header
from photosage.metadata.exif_reader import extract_metadata
from photosage.rename.filename_builder import build_filename


def _fits(path: Path) -> None:
    cards = [
        "SIMPLE  =                    T",
        "BITPIX  =                   16",
        "NAXIS   =                    0",
        "OBJECT  = 'Orion Nebula'",
        "DATE-OBS= '2026-05-26T03:15:00'",
        "TELESCOP= 'Seestar S50'",
        "FILTER  = 'H-alpha'",
        "EXPTIME = '10'",
        "END",
    ]
    content = "".join(card.ljust(80) for card in cards)
    content = content.ljust(2880)
    path.write_bytes(content.encode("ascii"))


def test_read_fits_header(tmp_path):
    path = tmp_path / "m42.fits"
    _fits(path)

    header = read_fits_header(path)

    assert header["OBJECT"] == "Orion Nebula"
    assert header["TELESCOP"] == "Seestar S50"


def test_extract_metadata_uses_fits_sidecar(tmp_path):
    image = tmp_path / "m42.jpg"
    Image.new("RGB", (16, 16), (1, 2, 3)).save(image)
    _fits(tmp_path / "m42.fits")

    metadata = extract_metadata(image)

    assert metadata["astro_mode"] is True
    assert metadata["astro_target"] == "Orion Nebula"
    assert metadata["astro_capture_night"] == "2026-05-25"
    assert metadata["fits_detected"] is True


def test_astro_filename_tokens_from_metadata(tmp_path):
    image = tmp_path / "m42.jpg"
    Image.new("RGB", (16, 16), (1, 2, 3)).save(image)
    _fits(tmp_path / "m42.fits")
    metadata = extract_metadata(image)

    filename = build_filename(metadata, None, 1, "{capture_night}_{astro_target}_{telescope}_{filter}_{exposure}_{counter}")

    assert filename == "2026-05-25_orion-nebula_seestar-s50_h-alpha_10_001.jpg"


def test_capture_night_groups_after_midnight_to_previous_date():
    assert capture_night("2026-05-26T03:15:00") == "2026-05-25"


def test_group_by_capture_night():
    groups = group_by_capture_night(
        [
            {"metadata": {"astro_capture_night": "2026-05-25"}},
            {"metadata": {"astro_capture_night": "2026-05-25"}},
            {"metadata": {"astro_capture_night": "2026-05-26"}},
        ]
    )

    assert len(groups["2026-05-25"]) == 2
    assert len(groups["2026-05-26"]) == 1


def test_enrich_from_filename_without_fits(tmp_path):
    image = tmp_path / "moon_seestar-s50.jpg"
    metadata = {"original_filename": image.name, "tags": [], "keywords": []}

    enriched = enrich_astro_metadata(metadata, image)

    assert enriched["astro_profile"] == "lunar"
    assert enriched["astro_telescope"] == "seestar-s50"
