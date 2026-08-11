from pathlib import Path

from photosage.organization.preview import folder_policy_preview


def test_folder_policy_preview_compares_destination_trees(tmp_path):
    manifest = {
        "files": [
            {
                "original_path": str(tmp_path / "photo.jpg"),
                "new_filename": "2026-01-01_trip_001.jpg",
                "metadata": {"date_taken": "2026-01-01", "location": "Dover"},
                "ai_response": {"primary_subject": "trip"},
            }
        ]
    }
    report = folder_policy_preview(manifest, tmp_path, ["date-first", "location-first"])

    assert set(report["policies"]) == {"date-first", "location-first"}
    assert Path(report["policies"]["date-first"]["operations"][0]["destination"]).name.endswith(".jpg")
