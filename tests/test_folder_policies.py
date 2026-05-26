from pathlib import Path

from photosage.organization.policies import destination_for_policy


def test_date_first_policy():
    path = destination_for_policy(
        Path("out"),
        {"date_taken": "2026-05-25", "keywords": ["construction"]},
        {},
        "photo.jpg",
        "date-first",
        {"construction": "build-project"},
    )

    assert path == Path("out") / "2026" / "2026-05" / "build-project" / "photo.jpg"


def test_location_first_policy():
    path = destination_for_policy(
        Path("out"),
        {"date_taken": "2026-05-25", "location": "Dover TN"},
        {},
        "photo.jpg",
        "location-first",
    )

    assert path == Path("out") / "dover-tn" / "2026" / "2026-05" / "photo.jpg"
