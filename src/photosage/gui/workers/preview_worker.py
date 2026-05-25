from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, Signal, Slot

from photosage.config import AppConfig
from photosage.gui.services import preview_folder


class PreviewWorker(QObject):
    """Background worker for rename previews."""

    finished = Signal(dict)
    failed = Signal(str)
    progress = Signal(int, str)

    def __init__(self, input_directory: Path, config: AppConfig, recursive: bool, force_ai: bool) -> None:
        super().__init__()
        self.input_directory = input_directory
        self.config = config
        self.recursive = recursive
        self.force_ai = force_ai
        self.cancelled = False

    @Slot()
    def run(self) -> None:
        try:
            if self.cancelled:
                return
            self.progress.emit(0, "Building preview")
            result = preview_folder(self.input_directory, self.config, self.recursive, self.force_ai)
            self.progress.emit(100, "Preview complete")
            self.finished.emit(result)
        except Exception as error:
            self.failed.emit(str(error))

    def cancel(self) -> None:
        self.cancelled = True

