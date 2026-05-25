from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, Signal, Slot

from photosage.gui.services import undo_manifest


class UndoWorker(QObject):
    """Background worker for undo operations."""

    finished = Signal(dict)
    failed = Signal(str)
    progress = Signal(int, str)

    def __init__(self, manifest_path: Path, dry_run: bool) -> None:
        super().__init__()
        self.manifest_path = manifest_path
        self.dry_run = dry_run
        self.cancelled = False

    @Slot()
    def run(self) -> None:
        try:
            if self.cancelled:
                return
            self.progress.emit(0, "Undo started")
            result = undo_manifest(self.manifest_path, self.dry_run)
            self.progress.emit(100, "Undo complete")
            self.finished.emit(result)
        except Exception as error:
            self.failed.emit(str(error))

    def cancel(self) -> None:
        self.cancelled = True

