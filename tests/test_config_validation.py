from pathlib import Path

import pytest

from photosage.config import AppConfig, ConfigValidationError, load_config, save_config


def test_config_rejects_string_boolean(tmp_path):
    path = tmp_path / "settings.yaml"
    path.write_text("local_only: 'false'\n", encoding="utf-8")
    with pytest.raises(ConfigValidationError, match="true or false"):
        load_config(path)


def test_config_rejects_unknown_setting(tmp_path):
    path = tmp_path / "settings.yaml"
    path.write_text("mystery_setting: true\n", encoding="utf-8")
    with pytest.raises(ConfigValidationError, match="Unknown"):
        load_config(path)


def test_config_rejects_unsafe_filename_format(tmp_path):
    path = tmp_path / "settings.yaml"
    path.write_text("filename_format: '{date}_{subject}'\n", encoding="utf-8")
    with pytest.raises(ConfigValidationError, match="counter"):
        load_config(path)


def test_save_config_is_atomic_and_round_trips(tmp_path):
    path = tmp_path / "settings.yaml"
    config = AppConfig(search_database=Path("cache/search.sqlite3"))
    save_config(config, path)
    assert load_config(path).search_database == Path("cache/search.sqlite3")
    assert not list(tmp_path.glob("*.tmp"))


def test_config_accepts_kimi_settings(tmp_path):
    path = tmp_path / "settings.yaml"
    path.write_text(
        "vision_provider: kimi\nlocal_only: false\nkimi:\n  model: kimi-k3\n  reasoning_effort: low\n",
        encoding="utf-8",
    )
    config = load_config(path)
    assert config.vision_provider == "kimi"
    assert config.provider_settings["kimi"]["model"] == "kimi-k3"


def test_config_rejects_invalid_kimi_reasoning_effort(tmp_path):
    path = tmp_path / "settings.yaml"
    path.write_text("kimi:\n  reasoning_effort: extreme\n", encoding="utf-8")
    with pytest.raises(ConfigValidationError, match="reasoning_effort"):
        load_config(path)
