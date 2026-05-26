from datetime import datetime, timedelta, timezone
import json

from photosage.geocoding.cache import GeocodeCache


def test_geocode_cache_set_and_resolve(tmp_path):
    cache = GeocodeCache(tmp_path / "cache.json", ttl_days=365)

    cache.set(36.50, -87.84, "dover-tn")

    assert cache.resolve(36.50, -87.84) == "dover-tn"


def test_geocode_cache_expires_old_entries(tmp_path):
    cache_file = tmp_path / "cache.json"
    cache_file.write_text(
        json.dumps(
            {
                "36.50000,-87.84000": {
                    "location": "dover-tn",
                    "timestamp": (datetime.now(timezone.utc) - timedelta(days=10)).isoformat(),
                }
            }
        ),
        encoding="utf-8",
    )

    cache = GeocodeCache(cache_file, ttl_days=1)

    assert cache.resolve(36.50, -87.84) is None
