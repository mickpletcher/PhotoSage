from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from photosage.config import load_config
from photosage.logging_config import configure_logging
from photosage.manifest.undo import undo_from_manifest
from photosage.rename.renamer import build_rename_manifest, rename_files
from photosage.scanner import scan_images

app = typer.Typer(help="Metadata-first AI photo organization and safe renaming CLI.")


def _config():
    config = load_config()
    configure_logging(config.log_file)
    return config


@app.command()
def scan(input: Annotated[Path, typer.Option("--input", exists=True, file_okay=False, dir_okay=True)]) -> None:
    """Scan an input directory for supported images."""
    config = _config()
    files = scan_images(input)
    typer.echo(f"Found {len(files)} supported images.")
    typer.echo(f"Log: {config.log_file}")


@app.command()
def preview(
    input: Annotated[Path, typer.Option("--input", exists=True, file_okay=False, dir_okay=True)],
    force_ai: Annotated[bool, typer.Option("--force-ai")] = False,
) -> None:
    """Preview proposed renames without modifying files."""
    config = _config()
    manifest = build_rename_manifest(input, config, force_ai=force_ai, dry_run=True)
    for item in manifest["files"]:
        typer.echo(f"{item['original_filename']} -> {item['new_filename']} score={item['metadata_score']} ai={item['ai_used']}")


@app.command()
def rename(
    input: Annotated[Path, typer.Option("--input", exists=True, file_okay=False, dir_okay=True)],
    apply: Annotated[bool, typer.Option("--apply", help="Actually rename files. Without this flag, PhotoSage only previews.")] = False,
    force_ai: Annotated[bool, typer.Option("--force-ai")] = False,
) -> None:
    """Preview or apply file renames."""
    config = _config()
    result = rename_files(input, config, apply=apply, force_ai=force_ai)
    action = "Renamed" if apply else "Previewed"
    typer.echo(f"{action} {len(result.manifest['files'])} files.")
    typer.echo(f"Manifest: {result.manifest_path}")


@app.command()
def undo(manifest: Annotated[Path, typer.Option("--manifest", exists=True, file_okay=True, dir_okay=False)]) -> None:
    """Undo renames from a manifest."""
    config = _config()
    results = undo_from_manifest(manifest)
    typer.echo(f"Undo processed {len(results)} files.")


if __name__ == "__main__":
    app()

