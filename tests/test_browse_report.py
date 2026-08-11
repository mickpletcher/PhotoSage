from PIL import Image

from photosage.browsing.report import build_browse_data, write_browse_report


def test_browse_report_builds_offline_timeline(monkeypatch, tmp_path):
    image = tmp_path / "trip.jpg"
    Image.new("RGB", (8, 8)).save(image)
    monkeypatch.setattr(
        "photosage.browsing.report.extract_metadata",
        lambda path: {"date_taken": "2026-05-01T12:00:00", "latitude": 36.5, "longitude": -87.8},
    )
    data = build_browse_data(tmp_path)
    html_path = tmp_path / "browser.html"
    json_path = tmp_path / "browser.json"
    write_browse_report(data, html_path, json_path)

    assert "2026-05" in data["timeline"]
    assert len(data["map_points"]) == 1
    assert "Offline GPS Map" in html_path.read_text(encoding="utf-8")
    assert json_path.exists()
