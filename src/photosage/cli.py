from __future__ import annotations

import json
import time
from dataclasses import asdict
from pathlib import Path
from typing import Annotated, Any, Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, TextColumn
from rich.table import Table

from photosage.config import AppConfig, load_config
from photosage.lightroom.catalog_safety import CatalogSafetyError
from photosage.lightroom.exporter import process_lightroom_export
from photosage.logging_config import configure_logging
from photosage.manifest.manifest_reader import ManifestValidationError
from photosage.manifest.undo import rollback_all
from photosage.metadata.exif_reader import extract_metadata
from photosage.metadata.metadata_score import score_metadata
from photosage.providers.healthcheck import check_providers, list_ollama_models, ollama_info
from photosage.rename.renamer import preview_renames, rename_files
from photosage.scanner import count_unsupported_files, scan_images

SUPPORTED_PROVIDERS = {"anthropic", "openai", "gemini", "ollama"}

app = typer.Typer(
    help="Metadata-first AI photo organization and safe renaming CLI.",
    epilog="Examples: photosage scan --input ./photos | photosage preview --input ./photos | photosage rename --input ./photos --apply | photosage undo --manifest ./manifests/file.json",
)
ollama_app = typer.Typer(help="Inspect local Ollama vision model support.")
app.add_typer(ollama_app, name="ollama")
console = Console()


def _config(
    config_path: Path,
    provider: Optional[str] = None,
    local_only: bool = False,
    verbose: bool = False,
) -> AppConfig:
    config = load_config(config_path)
    if provider:
        provider_name = provider.lower()
        if provider_name not in SUPPORTED_PROVIDERS:
            raise typer.BadParameter(f"Unsupported provider: {provider}")
        config.vision_provider = provider_name
    if local_only:
        config.local_only = True
        config.vision_provider = "ollama" if config.vision_provider not in {"ollama"} else config.vision_provider
    configure_logging(config.log_file, verbose=verbose)
    return config


def _write_json(path: Optional[Path], payload: dict[str, Any]) -> None:
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, default=str)
    console.print(f"[cyan]JSON output:[/cyan] {path}")


def _status_counts(items: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in items:
        counts[item["status"]] = counts.get(item["status"], 0) + 1
    return counts


def _preview_table(files: list[dict[str, Any]], title: str = "PhotoSage Rename Preview") -> Table:
    table = Table(title=title)
    table.add_column("Original", overflow="fold")
    table.add_column("Proposed", overflow="fold")
    table.add_column("Score", justify="right")
    table.add_column("AI", justify="center")
    table.add_column("Provider")
    table.add_column("Confidence", justify="right")
    for item in files:
        ai_response = item.get("ai_response") or {}
        ai_flag = "yes" if item.get("ai_used") or item.get("ai_required") else "no"
        style = "yellow" if ai_flag == "yes" else "green"
        if item.get("status") in {"error", "missing", "overwrite-prevented"}:
            style = "red"
        table.add_row(
            item["original_filename"],
            item["new_filename"],
            str(item["metadata_score"]),
            ai_flag,
            ai_response.get("provider") or "",
            str(ai_response.get("confidence", "")),
            style=style,
        )
    return table


def _summary_table(summary: dict[str, Any]) -> Table:
    table = Table(title="Summary")
    table.add_column("Metric")
    table.add_column("Value", justify="right")
    for key, value in summary.items():
        table.add_row(str(key).replace("_", " "), str(value))
    return table


def _scan_summary(input_path: Path, config: AppConfig, recursive: bool, force_ai: bool) -> dict[str, Any]:
    supported = scan_images(input_path, recursive=recursive)
    unsupported_count = count_unsupported_files(input_path, recursive=recursive)
    rows: list[dict[str, Any]] = []
    scores: list[int] = []

    for image_path in supported:
        try:
            metadata = extract_metadata(image_path)
            score = score_metadata(metadata)
            ai_required = force_ai or score < config.metadata_threshold
            scores.append(score)
            rows.append(
                {
                    "path": str(image_path),
                    "filename": image_path.name,
                    "metadata_score": score,
                    "ai_required": ai_required,
                    "status": "ok",
                }
            )
        except Exception as error:
            rows.append({"path": str(image_path), "filename": image_path.name, "metadata_score": 0, "ai_required": False, "status": f"error: {error}"})

    ai_required_count = sum(1 for row in rows if row["ai_required"])
    sufficient_count = sum(1 for row in rows if row["status"] == "ok" and not row["ai_required"])
    return {
        "summary": {
            "total_files": len(supported) + unsupported_count,
            "supported_files": len(supported),
            "unsupported_files": unsupported_count,
            "files_requiring_ai": ai_required_count,
            "files_with_sufficient_metadata": sufficient_count,
            "provider_selected": config.vision_provider,
            "local_only": config.local_only,
            "average_metadata_score": round(sum(scores) / len(scores), 2) if scores else 0,
        },
        "files": rows,
    }


@app.command(help="Show configured provider availability and local/cloud status.")
def providers(
    verbose: Annotated[bool, typer.Option("--verbose", help="Enable detailed console logging.")] = False,
    config: Annotated[Path, typer.Option("--config", exists=True, file_okay=True, dir_okay=False, help="Alternate config file.")] = Path("config/settings.yaml"),
) -> None:
    cli_config = _config(config, verbose=verbose)
    table = Table(title="Available Providers")
    table.add_column("Status")
    table.add_column("Provider")
    table.add_column("Model")
    table.add_column("Endpoint")
    table.add_column("Message", overflow="fold")
    for health in check_providers(cli_config):
        style = "green" if health.status == "OK" else ("yellow" if health.status == "DISABLED" else "red")
        table.add_row(f"[{style}]{health.status}[/{style}]", health.name, health.model, health.endpoint, health.message)
    console.print(table)


@ollama_app.command("models", help="List locally installed Ollama models.")
def ollama_models(
    endpoint: Annotated[Optional[str], typer.Option("--endpoint", help="Ollama endpoint override.")] = None,
    config: Annotated[Path, typer.Option("--config", exists=True, file_okay=True, dir_okay=False, help="Alternate config file.")] = Path("config/settings.yaml"),
) -> None:
    cli_config = _config(config)
    settings = cli_config.provider_settings.get("ollama", {})
    ollama_endpoint = endpoint or str(settings.get("endpoint") or "http://localhost:11434")
    timeout_seconds = float(settings.get("healthcheck_timeout_seconds") or 5)
    try:
        models = list_ollama_models(ollama_endpoint, timeout_seconds)
    except Exception as error:
        console.print(f"[red]ERROR: Ollama server not reachable at {ollama_endpoint}[/red]")
        console.print(str(error))
        raise typer.Exit(code=1) from error

    table = Table(title="Installed Ollama Models")
    table.add_column("Model")
    for model in models:
        table.add_row(model)
    console.print(table)


@ollama_app.command("info", help="Show best-effort Ollama diagnostics.")
def ollama_info_command(
    endpoint: Annotated[Optional[str], typer.Option("--endpoint", help="Ollama endpoint override.")] = None,
    config: Annotated[Path, typer.Option("--config", exists=True, file_okay=True, dir_okay=False, help="Alternate config file.")] = Path("config/settings.yaml"),
) -> None:
    cli_config = _config(config)
    settings = cli_config.provider_settings.get("ollama", {})
    ollama_endpoint = endpoint or str(settings.get("endpoint") or "http://localhost:11434")
    timeout_seconds = float(settings.get("healthcheck_timeout_seconds") or 5)
    info = ollama_info(ollama_endpoint, timeout_seconds)

    table = Table(title="Ollama Info")
    table.add_column("Field")
    table.add_column("Value", overflow="fold")
    table.add_row("Endpoint", str(info["endpoint"]))
    table.add_row("Version", str(info["version"]))
    table.add_row("Models", ", ".join(info["models"]) if info["models"] else "none detected")
    table.add_row("GPU usage", str(info["gpu_usage"]))
    table.add_row("VRAM estimate", str(info["vram_estimate"]))
    table.add_row("Inference mode", str(info["inference_mode"]))
    console.print(table)


@app.command(help="Scan supported image files, score metadata, and show whether AI would be required.")
def scan(
    input: Annotated[Path, typer.Option("--input", exists=True, file_okay=False, dir_okay=True, help="Photo directory to scan.")],
    recursive: Annotated[bool, typer.Option("--recursive/--no-recursive", help="Scan nested folders.")] = True,
    provider: Annotated[Optional[str], typer.Option("--provider", help="Override configured provider.")] = None,
    force_ai: Annotated[bool, typer.Option("--force-ai", help="Treat every supported image as requiring AI.")] = False,
    local_only: Annotated[bool, typer.Option("--local-only", help="Prevent cloud provider usage.")] = False,
    verbose: Annotated[bool, typer.Option("--verbose", help="Enable detailed console logging.")] = False,
    output_json: Annotated[Optional[Path], typer.Option("--output-json", help="Write scan results to a JSON file.")] = None,
    config: Annotated[Path, typer.Option("--config", exists=True, file_okay=True, dir_okay=False, help="Alternate config file.")] = Path("config/settings.yaml"),
) -> None:
    cli_config = _config(config, provider=provider, local_only=local_only, verbose=verbose)
    result = _scan_summary(input, cli_config, recursive=recursive, force_ai=force_ai)

    console.print(_summary_table(result["summary"]))
    table = Table(title="Metadata Scores")
    table.add_column("File", overflow="fold")
    table.add_column("Score", justify="right")
    table.add_column("AI Required", justify="center")
    table.add_column("Status")
    for row in result["files"]:
        style = "red" if str(row["status"]).startswith("error") else ("yellow" if row["ai_required"] else "green")
        table.add_row(row["filename"], str(row["metadata_score"]), "yes" if row["ai_required"] else "no", row["status"], style=style)
    console.print(table)
    _write_json(output_json, result)


@app.command(help="Preview proposed filename changes without renaming files.")
def preview(
    input: Annotated[Path, typer.Option("--input", exists=True, file_okay=False, dir_okay=True, help="Photo directory to preview.")],
    recursive: Annotated[bool, typer.Option("--recursive/--no-recursive", help="Scan nested folders.")] = True,
    provider: Annotated[Optional[str], typer.Option("--provider", help="Override configured provider.")] = None,
    force_ai: Annotated[bool, typer.Option("--force-ai", help="Show every file as AI-required when no precomputed AI JSON is available.")] = False,
    local_only: Annotated[bool, typer.Option("--local-only", help="Prevent cloud provider usage.")] = False,
    verbose: Annotated[bool, typer.Option("--verbose", help="Enable detailed console logging.")] = False,
    output_json: Annotated[Optional[Path], typer.Option("--output-json", help="Write preview manifest to a JSON file.")] = None,
    config: Annotated[Path, typer.Option("--config", exists=True, file_okay=True, dir_okay=False, help="Alternate config file.")] = Path("config/settings.yaml"),
) -> None:
    cli_config = _config(config, provider=provider, local_only=local_only, verbose=verbose)
    result = preview_renames(input, cli_config, recursive=recursive)
    if force_ai:
        for item in result.manifest["files"]:
            item["ai_required"] = True

    console.print(_preview_table(result.manifest["files"]))
    summary = {
        "total_renames": len(result.manifest["files"]),
        "skipped": sum(1 for item in result.manifest["files"] if item["status"] != "planned"),
        "ai_usage_count": sum(1 for item in result.manifest["files"] if item.get("ai_used") or item.get("ai_required")),
        "provider_selected": cli_config.vision_provider,
        "manifest": str(result.manifest_path),
    }
    console.print(_summary_table(summary))
    if force_ai:
        console.print("[yellow]--force-ai marks files as AI-required, but this CLI phase does not perform live AI calls.[/yellow]")
    _write_json(output_json, result.manifest)


@app.command(help="Apply safe renames only when --apply is explicitly provided.")
def rename(
    input: Annotated[Path, typer.Option("--input", exists=True, file_okay=False, dir_okay=True, help="Photo directory to rename.")],
    apply: Annotated[bool, typer.Option("--apply", help="Actually rename files. Required for any file changes.")] = False,
    recursive: Annotated[bool, typer.Option("--recursive/--no-recursive", help="Scan nested folders.")] = True,
    provider: Annotated[Optional[str], typer.Option("--provider", help="Override configured provider.")] = None,
    force_ai: Annotated[bool, typer.Option("--force-ai", help="Mark files as AI-required when no precomputed AI JSON is available.")] = False,
    local_only: Annotated[bool, typer.Option("--local-only", help="Prevent cloud provider usage.")] = False,
    verbose: Annotated[bool, typer.Option("--verbose", help="Enable detailed console logging.")] = False,
    output_json: Annotated[Optional[Path], typer.Option("--output-json", help="Write rename manifest to a JSON file.")] = None,
    config: Annotated[Path, typer.Option("--config", exists=True, file_okay=True, dir_okay=False, help="Alternate config file.")] = Path("config/settings.yaml"),
) -> None:
    cli_config = _config(config, provider=provider, local_only=local_only, verbose=verbose)
    if not apply:
        console.print(Panel("[yellow]No files were renamed. Re-run with --apply or use photosage preview first.[/yellow]", title="Safety Stop"))
        return

    started = time.perf_counter()
    processed = 0

    def on_item(item: dict[str, Any]) -> None:
        nonlocal processed
        processed += 1

    with Progress(TextColumn("[progress.description]{task.description}"), console=console) as progress:
        task = progress.add_task("Renaming files safely...", total=None)
        result = rename_files(input, cli_config, apply=True, force_ai=force_ai, recursive=recursive, progress_callback=on_item)
        progress.update(task, description=f"Processed {processed} files")

    elapsed = round(time.perf_counter() - started, 2)
    for item in result.manifest["files"]:
        style = "green" if item["status"] == "renamed" else ("yellow" if item["status"] in {"unchanged", "overwrite-prevented"} else "red")
        console.print(f"[{style}][RENAME][/{style}] old: {item['original_filename']} new: {item['new_filename']} status: {item['status']}")

    counts = _status_counts(result.manifest["files"])
    summary = {
        "renamed": counts.get("renamed", 0),
        "skipped": counts.get("unchanged", 0) + counts.get("missing", 0) + counts.get("overwrite-prevented", 0),
        "failed": counts.get("error", 0),
        "manifest": str(result.manifest_path),
        "elapsed_seconds": elapsed,
    }
    console.print(_summary_table(summary))
    _write_json(output_json, result.manifest)


@app.command("lightroom-process", help="Process Lightroom export folders with XMP sidecar preservation.")
def lightroom_process(
    input: Annotated[Path, typer.Option("--input", exists=True, file_okay=False, dir_okay=True, help="Lightroom export directory to process.")],
    preview: Annotated[bool, typer.Option("--preview", help="Preview Lightroom rename and organization operations.")] = False,
    apply: Annotated[bool, typer.Option("--apply", help="Actually rename exported files and matching XMP sidecars.")] = False,
    organize: Annotated[bool, typer.Option("--organize", help="Organize output into year/month/category folders.")] = False,
    preset: Annotated[Optional[str], typer.Option("--preset", help="Lightroom preset such as travel, astronomy, construction, metadata-only, or ai-heavy.")] = None,
    recursive: Annotated[bool, typer.Option("--recursive/--no-recursive", help="Scan nested folders.")] = True,
    provider: Annotated[Optional[str], typer.Option("--provider", help="Override configured provider.")] = None,
    force_ai: Annotated[bool, typer.Option("--force-ai", help="Mark files as AI-required even when metadata is sufficient.")] = False,
    local_only: Annotated[bool, typer.Option("--local-only", help="Prevent cloud provider usage.")] = False,
    force_catalog_modify: Annotated[bool, typer.Option("--force-catalog-modify", help="Allow processing inside probable Lightroom catalog paths. Not recommended.")] = False,
    verbose: Annotated[bool, typer.Option("--verbose", help="Enable detailed console logging.")] = False,
    output_json: Annotated[Optional[Path], typer.Option("--output-json", help="Write Lightroom manifest to a JSON file.")] = None,
    config: Annotated[Path, typer.Option("--config", exists=True, file_okay=True, dir_okay=False, help="Alternate config file.")] = Path("config/settings.yaml"),
) -> None:
    cli_config = _config(config, provider=provider, local_only=local_only, verbose=verbose)
    if apply and preview:
        console.print("[red]Choose either --preview or --apply, not both.[/red]")
        raise typer.Exit(code=1)
    if not apply and not preview:
        preview = True

    processed = 0

    def on_item(item: dict[str, Any]) -> None:
        nonlocal processed
        processed += 1
        style = "green" if item.get("status") == "renamed" else ("yellow" if item.get("status") != "error" else "red")
        console.print(f"[{style}][LIGHTROOM][/{style}] old: {item['original_filename']} new: {item['new_filename']} status: {item['status']}")

    try:
        with Progress(TextColumn("[progress.description]{task.description}"), console=console) as progress:
            task = progress.add_task("Processing Lightroom export...", total=None)
            result = process_lightroom_export(
                input_directory=input,
                config=cli_config,
                preview=preview,
                apply=apply,
                organize=organize,
                preset_name=preset,
                force_ai=force_ai,
                recursive=recursive,
                force_catalog_modify=force_catalog_modify,
                progress_callback=on_item if apply else None,
            )
            progress.update(task, description=f"Processed {processed if apply else len(result.manifest['files'])} files")
    except CatalogSafetyError as error:
        console.print(f"[red]Lightroom catalog safety block:[/red] {error}")
        console.print("[yellow]Export photos to a separate folder or pass --force-catalog-modify only if you understand the catalog reference risk.[/yellow]")
        raise typer.Exit(code=1) from error
    except ValueError as error:
        console.print(f"[red]Lightroom processing failed:[/red] {error}")
        raise typer.Exit(code=1) from error

    if result.warnings:
        console.print(Panel("\n".join(result.warnings), title="Catalog Safety Warnings", style="yellow"))

    console.print(_preview_table(result.manifest["files"], title="Lightroom Export Processing"))
    counts = _status_counts(result.manifest["files"])
    summary = {
        "mode": "apply" if apply else "preview",
        "files": len(result.manifest["files"]),
        "renamed": counts.get("renamed", 0),
        "planned": counts.get("planned", 0),
        "skipped": counts.get("unchanged", 0) + counts.get("missing", 0) + counts.get("overwrite-prevented", 0),
        "xmp_sidecars": sum(1 for item in result.manifest["files"] if item.get("xmp_detected")),
        "organization_applied": result.manifest.get("organization_applied"),
        "preset": result.manifest.get("preset") or "",
        "manifest": str(result.manifest_path),
    }
    console.print(_summary_table(summary))
    if not apply:
        console.print("[yellow]Preview only. Re-run with --apply to rename exported files and synchronized XMP sidecars.[/yellow]")
    _write_json(output_json, result.manifest)


@app.command(help="Restore original filenames from a rename manifest.")
def undo(
    manifest: Annotated[Path, typer.Option("--manifest", exists=True, file_okay=True, dir_okay=False, help="Rename manifest to roll back.")],
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Validate and report rollback operations without moving files.")] = False,
    force: Annotated[bool, typer.Option("--force", help="Skip confirmation for real undo operations.")] = False,
    verbose: Annotated[bool, typer.Option("--verbose", help="Print each rollback operation and enable detailed logging.")] = False,
    continue_on_error: Annotated[bool, typer.Option("--continue-on-error/--stop-on-error", help="Continue processing after failed operations.")] = True,
    recursive: Annotated[bool, typer.Option("--recursive/--no-recursive", help="Accepted for command consistency. Undo uses manifest paths.")] = True,
    provider: Annotated[Optional[str], typer.Option("--provider", help="Accepted for command consistency. Undo does not use providers.")] = None,
    force_ai: Annotated[bool, typer.Option("--force-ai", help="Accepted for command consistency. Undo does not use AI.")] = False,
    local_only: Annotated[bool, typer.Option("--local-only", help="Accepted for command consistency. Undo does not use providers.")] = False,
    output_json: Annotated[Optional[Path], typer.Option("--output-json", help="Write rollback summary to a JSON file.")] = None,
    config: Annotated[Path, typer.Option("--config", exists=True, file_okay=True, dir_okay=False, help="Alternate config file.")] = Path("config/settings.yaml"),
) -> None:
    _ = recursive, provider, force_ai, local_only
    _config(config, verbose=verbose)

    try:
        if not dry_run and not force:
            preview_result = rollback_all(manifest, dry_run=True, continue_on_error=continue_on_error)
            console.print("[yellow]Undo preview. No files moved yet.[/yellow]")
            console.print(_summary_table(preview_result.summary))
            console.print(f"[cyan]Dry-run rollback report:[/cyan] {preview_result.report_path}")
            typer.confirm("Undo will move files back to their original paths. Continue?", abort=True)
        result = rollback_all(manifest, dry_run=dry_run, continue_on_error=continue_on_error)
    except ManifestValidationError as error:
        console.print(f"[red]Invalid manifest:[/red] {error}")
        raise typer.Exit(code=1) from error

    if dry_run:
        console.print("[yellow][DRY RUN] No files were moved.[/yellow]")
    console.print(f"[green]Undo processed {len(result.operations)} files.[/green]")
    console.print(_summary_table(result.summary))
    if verbose:
        table = Table(title="Rollback Operations")
        table.add_column("Status")
        table.add_column("Source", overflow="fold")
        table.add_column("Destination", overflow="fold")
        table.add_column("Message", overflow="fold")
        for operation in result.operations:
            table.add_row(operation.status, operation.source, operation.destination, operation.message)
        console.print(table)
    console.print(f"[cyan]Rollback report:[/cyan] {result.report_path}")
    _write_json(
        output_json,
        {
            "summary": result.summary,
            "report_path": str(result.report_path),
            "operations": [asdict(operation) for operation in result.operations],
        },
    )


if __name__ == "__main__":
    app()
