from pathlib import Path

from PIL import Image

from photosage.duplicates.detector import find_duplicate_groups, hamming_distance, write_duplicate_report


def _image(path: Path, color: tuple[int, int, int]) -> None:
    Image.new("RGB", (24, 24), color).save(path)


def _gradient(path: Path) -> None:
    image = Image.new("RGB", (24, 24))
    for x in range(24):
        for y in range(24):
            image.putpixel((x, y), (x * 10, y * 10, 120))
    image.save(path)


def test_find_duplicate_groups(tmp_path):
    first = tmp_path / "first.jpg"
    second = tmp_path / "second.jpg"
    different = tmp_path / "different.jpg"
    _image(first, (20, 20, 20))
    _image(second, (20, 20, 20))
    _gradient(different)

    groups = find_duplicate_groups([first, second, different], max_distance=0)

    assert len(groups) == 1
    assert set(groups[0].files) == {str(first.resolve()), str(second.resolve())}


def test_hamming_distance():
    assert hamming_distance("0f", "0e") == 1


def test_write_duplicate_report(tmp_path):
    first = tmp_path / "first.jpg"
    second = tmp_path / "second.jpg"
    _image(first, (20, 20, 20))
    _image(second, (20, 20, 20))

    groups = find_duplicate_groups([first, second], max_distance=0)
    report = write_duplicate_report(groups, tmp_path / "duplicates.json")

    assert report.exists()
    assert "dup-0001" in report.read_text(encoding="utf-8")
