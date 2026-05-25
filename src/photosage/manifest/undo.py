from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from photosage.manifest.manifest_reader import ManifestValidationError, load_manifest, resolved_input_directory, safe_restore_path
from photosage.manifest.rollback_report import RollbackOperation, generate_rollback_report

logger = logging.getLogger(__name__)

ROLLBACKABLE_STATUSES = {"renamed"}


@dataclass(slots=True)
class RollbackResult:
    """Result of a rollback run."""

    operations: list[RollbackOperation]
    report_path: Path

    @property
    def summary(self) -> dict[str, int]:
        """Return operation counts by status."""
        summary = {"restored": 0, "skipped_missing": 0, "skipped_collision": 0, "failed": 0}
        for operation in self.operations:
            if operation.status in summary:
                summary[operation.status] += 1
        return summary


def _base_directory(manifest: dict[str, Any], manifest_path: Path | None = None) -> Path:
    return resolved_input_directory(manifest, manifest_path)


def validate_rollback_operation(item: dict[str, Any], base_directory: Path) -> tuple[Path, Path, str | None]:
    """Validate one manifest file entry for rollback."""
    source = safe_restore_path(Path(str(item["new_path"])), base_directory)
    destination = safe_restore_path(Path(str(item["original_path"])), base_directory)

    if item.get("status") not in ROLLBACKABLE_STATUSES:
        return source, destination, f"Entry status is not rollbackable: {item.get('status')}"
    if not source.exists():
        return source, destination, "Renamed file is missing"
    if destination.exists():
        return source, destination, "Original path already exists"
    return source, destination, None


def rollback_file(source: Path, destination: Path, dry_run: bool = False) -> RollbackOperation:
    """Restore one renamed file without overwriting."""
    if not source.exists():
        logger.warning("rollback skipped missing source=%s destination=%s", source, destination)
        return RollbackOperation(str(source), str(destination), "skipped_missing", "Renamed file is missing")
    if destination.exists():
        logger.warning("rollback skipped collision source=%s destination=%s", source, destination)
        return RollbackOperation(str(source), str(destination), "skipped_collision", "Original path already exists")
    if dry_run:
        logger.info("rollback dry-run restore source=%s destination=%s", source, destination)
        return RollbackOperation(str(source), str(destination), "restored", "Dry run would restore file")

    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
        source.rename(destination)
    except OSError as error:
        logger.error("rollback failed source=%s destination=%s error=%s", source, destination, error)
        return RollbackOperation(str(source), str(destination), "failed", str(error))

    logger.info("rollback restored source=%s destination=%s", source, destination)
    return RollbackOperation(str(source), str(destination), "restored", "File restored successfully")


def perform_rollback(
    manifest: dict[str, Any],
    dry_run: bool = False,
    continue_on_error: bool = True,
    manifest_path: Path | None = None,
) -> list[RollbackOperation]:
    """Perform rollback operations from a validated manifest."""
    operations: list[RollbackOperation] = []
    base_directory = _base_directory(manifest, manifest_path)

    for item in manifest["files"]:
        try:
            source, destination, validation_message = validate_rollback_operation(item, base_directory)
            if validation_message == "Renamed file is missing":
                operation = RollbackOperation(str(source), str(destination), "skipped_missing", validation_message)
            elif validation_message == "Original path already exists":
                operation = RollbackOperation(str(source), str(destination), "skipped_collision", validation_message)
            elif validation_message:
                operation = RollbackOperation(str(source), str(destination), "failed", validation_message)
            else:
                operation = rollback_file(source, destination, dry_run=dry_run)
            operations.append(operation)

            if operation.status == "failed" and not continue_on_error:
                break
        except (ManifestValidationError, OSError, ValueError) as error:
            source = str(item.get("new_path", ""))
            destination = str(item.get("original_path", ""))
            logger.error("rollback validation failed source=%s destination=%s error=%s", source, destination, error)
            operations.append(RollbackOperation(source, destination, "failed", str(error)))
            if not continue_on_error:
                break

    logger.info("rollback summary=%s", {status: sum(1 for op in operations if op.status == status) for status in {op.status for op in operations}})
    return operations


def rollback_all(
    manifest_path: Path,
    dry_run: bool = False,
    continue_on_error: bool = True,
    report_directory: Path = Path("rollback_reports"),
) -> RollbackResult:
    """Load a manifest, rollback all entries, and write a rollback report."""
    manifest = load_manifest(manifest_path)
    operations = perform_rollback(manifest, dry_run=dry_run, continue_on_error=continue_on_error, manifest_path=manifest_path)
    report_path = generate_rollback_report(manifest_path, operations, dry_run=dry_run, output_directory=report_directory)
    return RollbackResult(operations=operations, report_path=report_path)


def undo_from_manifest(
    manifest_path: Path,
    dry_run: bool = False,
    continue_on_error: bool = True,
    report_directory: Path = Path("rollback_reports"),
) -> list[dict[str, str]]:
    """Compatibility wrapper returning legacy dict operation results."""
    result = rollback_all(
        manifest_path=manifest_path,
        dry_run=dry_run,
        continue_on_error=continue_on_error,
        report_directory=report_directory,
    )
    return [
        {
            "path": operation.destination,
            "source": operation.source,
            "destination": operation.destination,
            "status": operation.status,
            "message": operation.message,
        }
        for operation in result.operations
    ]
