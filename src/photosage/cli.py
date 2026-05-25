from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from photosage.config import load_config
from photosage.logging_config import configure_logging
from photosage.manifest.undo import undo_from_manifest
from photosage.rename.renamer import preview_renames, rename_files
from photosage.scanner import scan_images

app = typer.Typer(help="Metadata-first AI photo organization and safe renaming CLI.")
console = Console()


def _config():
    config = load_config()
    configure_logging(config.log_file)
    return config


@app.command()
def scan(input: Annotated[Path, typer.Option("--input", exists=True, file_okay=False, dir_okay=True)]) -> None:
    """Scan an input directory for supported images."""
    config = _config()
    files = scan_images(input)
    console.print(f"[green]Found {len(files)} supported images.[/green]")
    console.print(f"Log: {config.log_file}")


@app.command()
def preview(
    input: Annotated[Path, typer.Option("--input", exists=True, file_okay=False, dir_okay=True)],
    force_ai: Annotated[bool, typer.Option("--force-ai")] = False,
) -> None:
    """Preview proposed renames without modifying files."""
    config = _config()
    result = preview_renames(input, config)
    table = Table(title="PhotoSage Rename Preview")
    table.add_column("Original", overflow="fold")
    table.add_column("New", overflow="fold")
    table.add_column("Score", justify="right")
    table.add_column("AI", justify="center")
    for item in result.manifest["files"]:
        table.add_row(item["original_filename"], item["new_filename"], str(item["metadata_score"]), "yes" if item["ai_used"] else "no")
    console.print(table)
    if force_ai:
        console.print("[yellow]--force-ai was requested, but the rename engine only consumes precomputed normalized AI JSON in this phase.[/yellow]")
    console.print(f"[cyan]Manifest:[/cyan] {result.manifest_path}")


@app.command()
def rename(
    input: Annotated[Path, typer.Option("--input", exists=True, file_okay=False, dir_okay=True)],
    apply: Annotated[bool, typer.Option("--apply", help="Actually rename files. Without this flag, PhotoSage only previews.")] = False,
    force_ai: Annotated[bool, typer.Option("--force-ai")] = False,
) -> None:
    """Preview or apply file renames."""
    config = _config()
    result = rename_files(input, config, apply=apply, force_ai=force_ai)
    statuses: dict[str, int] = {}
    for item in result.manifest["files"]:
        statuses[item["status"]] = statuses.get(item["status"], 0) + 1

    action = "Renamed" if apply else "Previewed"
    console.print(f"[green]{action} {len(result.manifest['files'])} files.[/green]")
    for status, count in sorted(statuses.items()):
        style = "red" if status in {"error", "missing", "overwrite-prevented"} else "cyan"
        console.print(f"[{style}]{status}: {count}[/{style}]")
    if force_ai and not any(item["ai_used"] for item in result.manifest["files"]):
        console.print("[yellow]--force-ai was requested, but no normalized AI responses were supplied to the rename engine.[/yellow]")
    console.print(f"[cyan]Manifest:[/cyan] {result.manifest_path}")


@app.command()
def undo(manifest: Annotated[Path, typer.Option("--manifest", exists=True, file_okay=True, dir_okay=False)]) -> None:
    """Undo renames from a manifest."""
    config = _config()
    results = undo_from_manifest(manifest)
    statuses: dict[str, int] = {}
    for result in results:
        statuses[result["status"]] = statuses.get(result["status"], 0) + 1
    console.print(f"[green]Undo processed {len(results)} files.[/green]")
    for status, count in sorted(statuses.items()):
        style = "red" if status in {"error", "missing", "overwrite-prevented"} else "cyan"
        console.print(f"[{style}]{status}: {count}[/{style}]")


if __name__ == "__main__":
    app()
