from PIL import Image

from photosage.duplicates.detector import find_duplicate_groups
from photosage.duplicates.review import build_duplicate_review_manifest, duplicate_review_rows, write_duplicate_csv
from photosage.manifest.manifest_reader import load_manifest


def test_duplicate_review_recommends_keeper_and_builds_manifest(tmp_path):
    first = tmp_path / "first.jpg"
    second = tmp_path / "second.jpg"
    Image.new("RGB", (20, 20), "red").save(first)
    Image.new("RGB", (20, 20), "red").save(second)
    groups = find_duplicate_groups([first, second], max_distance=0)
    rows = duplicate_review_rows(groups)
    csv_path = write_duplicate_csv(rows, tmp_path / "duplicates.csv")
    manifest_path = build_duplicate_review_manifest(tmp_path, tmp_path / "Review", groups, tmp_path / "manifests")
    manifest = load_manifest(manifest_path)

    assert {row["recommendation"] for row in rows} == {"keep", "review"}
    assert csv_path.exists()
    assert manifest["workflow"] == "duplicate-review"
    assert manifest["files"][0]["status"] == "needs-review"
