from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, Signal, Slot

from photosage.config import AppConfig
from photosage.gui.services import apply_folder


class RenameWorker(QObject):
    """Background worker for safe rename apply operations."""

    finished = Signal(dict)
    failed = Signal(str)
    progress = Signal(int, str)

    def __init__(self, input_directory: Path, config: AppConfig, recursive: bool) -> None:
        super().__init__()
        self.input_directory = input_directory
        self.config = config
        self.recursive = recursive
        self.cancelled = False

    @Slot()
    def run(self) -> None:
        try:
            if self.cancelled:
                return
            self.progress.emit(0, "Applying renames")
            result = apply_folder(self.input_directory, self.config, self.recursive)
            self.progress.emit(100, "Rename complete")
            self.finished.emit(result)
        except Exception as error:
            self.failed.emit(str(error))

    def cancel(self) -> None:
        self.cancelled = True

