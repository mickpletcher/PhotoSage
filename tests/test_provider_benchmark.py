from pathlib import Path

from PIL import Image

from photosage.config import AppConfig
from photosage.providers.base import VisionProvider
from photosage.providers.benchmark import benchmark_providers, write_benchmark_reports
from photosage.providers.provider_factory import ProviderFactory


class BenchmarkProvider(VisionProvider):
    provider_name = "ollama"
    default_model = "test"
    is_local = True

    def analyze_image(self, image_path: Path, metadata: dict) -> dict:
        return self.normalize({"primary_subject": "test", "confidence": 0.8})


def test_provider_benchmark_exports_json_and_markdown(monkeypatch, tmp_path):
    image = tmp_path / "sample.jpg"
    Image.new("RGB", (10, 10)).save(image)
    monkeypatch.setattr(ProviderFactory, "PROVIDERS", {"ollama": BenchmarkProvider})

    report = benchmark_providers([image], AppConfig(provider_retry_initial_delay=0), ["ollama"])
    json_path = tmp_path / "benchmark.json"
    markdown_path = tmp_path / "benchmark.md"
    write_benchmark_reports(report, json_path, markdown_path)

    assert report["summary"]["ollama"]["successful"] == 1
    assert report["results"][0]["json_valid"] is True
    assert json_path.exists()
    assert "| ollama |" in markdown_path.read_text(encoding="utf-8")
