from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QCheckBox, QComboBox, QHBoxLayout, QLabel, QSlider, QWidget
from PySide6.QtCore import Qt


class ProviderSelector(QWidget):
    """Provider controls for the main toolbar."""

    changed = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.provider_combo = QComboBox()
        self.provider_combo.addItems(["anthropic", "openai", "gemini", "ollama"])
        self.local_only = QCheckBox("Local only")
        self.force_ai = QCheckBox("Force AI")
        self.threshold = QSlider(Qt.Horizontal)
        self.threshold.setRange(0, 100)
        self.threshold.setValue(70)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(QLabel("Provider"))
        layout.addWidget(self.provider_combo)
        layout.addWidget(self.local_only)
        layout.addWidget(self.force_ai)
        layout.addWidget(QLabel("Threshold"))
        layout.addWidget(self.threshold)

        self.provider_combo.currentTextChanged.connect(self.changed.emit)
        self.local_only.toggled.connect(self.changed.emit)
        self.force_ai.toggled.connect(self.changed.emit)
        self.threshold.valueChanged.connect(self.changed.emit)

    def apply_to_config(self, config) -> None:
        config.vision_provider = self.provider_combo.currentText()
        config.local_only = self.local_only.isChecked()
        config.metadata_threshold = self.threshold.value()

    def load_from_config(self, config) -> None:
        self.provider_combo.setCurrentText(config.vision_provider)
        self.local_only.setChecked(config.local_only)
        self.threshold.setValue(config.metadata_threshold)

