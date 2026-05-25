from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class RollbackOperation:
    """One rollback operation result."""

    source: str
    destination: str
    status: str
    message: str


@dataclass(slots=True)
class RollbackReport:
    """Rollback report written after an undo attempt."""

    rollback_id: str
    manifest_used: str
    timestamp: str
    dry_run: bool
    summary: dict[str, int]
    operations: list[RollbackOperation]

    def to_dict(self) -> dict:
        """Return JSON serializable report data."""
        data = asdict(self)
        data["operations"] = [asdict(operation) for operation in self.operations]
        return data


def build_rollback_report(manifest_path: Path, operations: list[RollbackOperation], dry_run: bool) -> RollbackReport:
    """Build a rollback report object."""
    now = datetime.now(timezone.utc)
    summary = {"restored": 0, "skipped_missing": 0, "skipped_collision": 0, "failed": 0}
    for operation in operations:
        if operation.status in summary:
            summary[operation.status] += 1
    return RollbackReport(
        rollback_id=f"rollback_{now.strftime('%Y%m%d_%H%M%S')}",
        manifest_used=str(manifest_path),
        timestamp=now.isoformat(),
        dry_run=dry_run,
        summary=summary,
        operations=operations,
    )


def generate_rollback_report(
    manifest_path: Path,
    operations: list[RollbackOperation],
    dry_run: bool,
    output_directory: Path = Path("rollback_reports"),
) -> Path:
    """Write a rollback report JSON file."""
    report = build_rollback_report(manifest_path, operations, dry_run)
    output_directory.mkdir(parents=True, exist_ok=True)
    report_path = output_directory / f"{report.rollback_id}.json"
    if report_path.exists():
        report_path = output_directory / f"{report.rollback_id}_{len(operations)}.json"
    with report_path.open("w", encoding="utf-8") as handle:
        json.dump(report.to_dict(), handle, indent=2)
    logger.info("rollback report generated path=%s", report_path)
    return report_path

