from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any

from photosage.config import AppConfig
from photosage.metadata.exif_reader import extract_metadata
from photosage.providers.base import CLOUD_PROVIDERS
from photosage.providers.provider_factory import ProviderFactory
from photosage.providers.retry_handler import RetryConfig, run_with_retries


@dataclass(slots=True)
class BenchmarkResult:
    provider: str
    model: str
    file: str
    success: bool
    latency_ms: int
    attempts: int
    json_valid: bool
    confidence: float
    routing: str
    error: str = ""


def benchmark_providers(
    image_paths: list[Path],
    config: AppConfig,
    provider_names: list[str],
    allow_cloud: bool = False,
) -> dict[str, Any]:
    results: list[BenchmarkResult] = []
    retry_config = RetryConfig(config.provider_retry_count, config.provider_retry_initial_delay)
    for provider_name in provider_names:
        if provider_name in CLOUD_PROVIDERS and not allow_cloud:
            raise ValueError(f"Cloud benchmark blocked without --allow-cloud: {provider_name}")
        provider = ProviderFactory.create(provider_name, config)
        for image_path in image_paths:
            attempts = 0
            started = time.perf_counter()
            response: dict[str, Any] = {}
            error_text = ""

            def operation(provider=provider, image_path=image_path) -> dict[str, Any]:
                nonlocal attempts
                attempts += 1
                return provider.analyze_image(image_path, extract_metadata(image_path))

            try:
                response = run_with_retries(operation, retry_config)
                success = True
            except Exception as error:
                success = False
                error_text = f"{type(error).__name__}: {error}"
            latency_ms = int((time.perf_counter() - started) * 1000)
            results.append(
                BenchmarkResult(
                    provider=provider_name,
                    model=provider.model,
                    file=image_path.name,
                    success=success,
                    latency_ms=latency_ms,
                    attempts=attempts,
                    json_valid=isinstance(response, dict) and bool(response),
                    confidence=float(response.get("confidence") or 0),
                    routing=getattr(provider, "endpoint_trust", "cloud"),
                    error=error_text,
                )
            )
    summaries: dict[str, dict[str, Any]] = {}
    for provider_name in provider_names:
        selected = [result for result in results if result.provider == provider_name]
        successful = [result for result in selected if result.success]
        summaries[provider_name] = {
            "runs": len(selected),
            "successful": len(successful),
            "success_rate": round(len(successful) / len(selected), 3) if selected else 0,
            "average_latency_ms": round(mean(result.latency_ms for result in selected), 2) if selected else 0,
            "average_confidence": round(mean(result.confidence for result in successful), 3) if successful else 0,
            "total_attempts": sum(result.attempts for result in selected),
        }
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "files": len(image_paths),
        "providers": provider_names,
        "summary": summaries,
        "results": [asdict(result) for result in results],
    }


def write_benchmark_reports(report: dict[str, Any], json_path: Path | None = None, markdown_path: Path | None = None) -> None:
    if json_path:
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    if markdown_path:
        markdown_path.parent.mkdir(parents=True, exist_ok=True)
        lines = [
            "# PhotoSage Provider Benchmark",
            "",
            "| Provider | Success | Latency ms | Confidence | Attempts |",
            "|---|---:|---:|---:|---:|",
        ]
        for provider, summary in report["summary"].items():
            lines.append(
                f"| {provider} | {summary['successful']}/{summary['runs']} | {summary['average_latency_ms']} | "
                f"{summary['average_confidence']} | {summary['total_attempts']} |"
            )
        markdown_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
