from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from photosage.config import load_config
from photosage.logging_config import configure_logging
from photosage.manifest.undo import rollback_all
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
def undo(
    manifest: Annotated[Path, typer.Option("--manifest", exists=True, file_okay=True, dir_okay=False)],
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Validate and report rollback operations without moving files.")] = False,
    verbose: Annotated[bool, typer.Option("--verbose", help="Print each rollback operation.")] = False,
    continue_on_error: Annotated[bool, typer.Option("--continue-on-error/--stop-on-error", help="Continue processing after failed operations.")] = True,
) -> None:
    """Undo renames from a manifest."""
    config = _config()
    result = rollback_all(manifest, dry_run=dry_run, continue_on_error=continue_on_error)
    if dry_run:
        console.print("[yellow][DRY RUN] No files were moved.[/yellow]")
    console.print(f"[green]Undo processed {len(result.operations)} files.[/green]")
    for status, count in sorted(result.summary.items()):
        style = "red" if status in {"failed", "skipped_missing", "skipped_collision"} else "cyan"
        console.print(f"[{style}]{status}: {count}[/{style}]")
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


if __name__ == "__main__":
    app()
