from PIL import Image

from photosage.config import AppConfig
from photosage.search.index import build_search_index, hash_embedding, search_index


def test_hash_embedding_is_normalized_and_deterministic():
    first = hash_embedding("red container home")
    second = hash_embedding("red container home")
    assert first == second
    assert round(sum(value * value for value in first), 6) == 1


def test_local_search_index_returns_matching_filename(tmp_path):
    Image.new("RGB", (8, 8), "red").save(tmp_path / "container-home.jpg")
    Image.new("RGB", (8, 8), "blue").save(tmp_path / "ocean-trip.jpg")
    config = AppConfig(search_database=tmp_path / "search.sqlite3", metadata_threshold=0)

    summary = build_search_index(tmp_path, config)
    results = search_index("container home", config, limit=1)

    assert summary == {"indexed": 2, "failed": 0, "removed": 0}
    assert results[0]["path"].endswith("container-home.jpg")
