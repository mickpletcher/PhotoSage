import pytest

from photosage.lightroom.catalog_safety import CatalogSafetyError, detect_lightroom_catalog_risk, validate_lightroom_export_directory


def test_catalog_safety_detects_lrcat_files(tmp_path):
    catalog = tmp_path / "Lightroom Catalog.lrcat"
    catalog.write_text("catalog", encoding="utf-8")

    warnings = detect_lightroom_catalog_risk(tmp_path)

    assert any(".lrcat" in warning for warning in warnings)


def test_catalog_safety_blocks_probable_catalog_by_default(tmp_path):
    (tmp_path / "catalog.lrcat").write_text("catalog", encoding="utf-8")

    with pytest.raises(CatalogSafetyError):
        validate_lightroom_export_directory(tmp_path)


def test_catalog_safety_allows_catalog_with_force(tmp_path):
    (tmp_path / "catalog.lrcat").write_text("catalog", encoding="utf-8")

    warnings = validate_lightroom_export_directory(tmp_path, force_catalog_modify=True)

    assert warnings
