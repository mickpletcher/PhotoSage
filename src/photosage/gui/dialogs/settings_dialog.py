from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QCheckBox, QComboBox, QDialog, QFormLayout, QLineEdit, QPushButton, QSpinBox, QVBoxLayout

from photosage.config import AppConfig, save_config


class SettingsDialog(QDialog):
    """Editable GUI settings dialog."""

    def __init__(self, config: AppConfig, config_path: Path, parent=None) -> None:
        super().__init__(parent)
        self.config = config
        self.config_path = config_path
        self.setWindowTitle("PhotoSage Settings")
        self.setMinimumWidth(520)

        self.provider = QComboBox()
        self.provider.addItems(["anthropic", "openai", "gemini", "ollama", "lmstudio"])
        self.provider.setCurrentText(config.vision_provider)
        self.threshold = QSpinBox()
        self.threshold.setRange(0, 100)
        self.threshold.setValue(config.metadata_threshold)
        self.filename_format = QLineEdit(config.filename_format)
        self.dry_run_default = QCheckBox()
        self.dry_run_default.setChecked(config.dry_run_default)
        self.local_only = QCheckBox()
        self.local_only.setChecked(config.local_only)
        self.recursive = QCheckBox()
        self.recursive.setChecked(config.recursive_scanning)
        self.thumbnail_size = QSpinBox()
        self.thumbnail_size.setRange(64, 512)
        self.thumbnail_size.setValue(config.thumbnail_size)
        self.log_level = QComboBox()
        self.log_level.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        self.log_level.setCurrentText(config.log_level)
        self.max_ai = QSpinBox()
        self.max_ai.setRange(1, 16)
        self.max_ai.setValue(config.max_concurrent_ai_requests)

        form = QFormLayout()
        form.addRow("Default provider", self.provider)
        form.addRow("Metadata threshold", self.threshold)
        form.addRow("Filename format", self.filename_format)
        form.addRow("Dry run default", self.dry_run_default)
        form.addRow("Local only mode", self.local_only)
        form.addRow("Recursive scanning", self.recursive)
        form.addRow("Thumbnail size", self.thumbnail_size)
        form.addRow("Log level", self.log_level)
        form.addRow("Max concurrent AI requests", self.max_ai)

        save_button = QPushButton("Save")
        save_button.clicked.connect(self.save)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(save_button, alignment=Qt.AlignRight)
        layout.addWidget(cancel_button, alignment=Qt.AlignRight)

    def save(self) -> None:
        self.config.vision_provider = self.provider.currentText()
        self.config.metadata_threshold = self.threshold.value()
        self.config.filename_format = self.filename_format.text()
        self.config.dry_run_default = self.dry_run_default.isChecked()
        self.config.local_only = self.local_only.isChecked()
        self.config.recursive_scanning = self.recursive.isChecked()
        self.config.thumbnail_size = self.thumbnail_size.value()
        self.config.log_level = self.log_level.currentText()
        self.config.max_concurrent_ai_requests = self.max_ai.value()
        save_config(self.config, self.config_path)
        self.accept()
