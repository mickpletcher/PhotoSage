from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from photosage.config import load_config
from photosage.gui.main_window import MainWindow
from photosage.logging_config import configure_logging


def main() -> int:
    """Start the PhotoSage desktop application."""
    config_path = Path("config/settings.yaml")
    config = load_config(config_path)
    configure_logging(config.log_file)
    app = QApplication(sys.argv)
    stylesheet = Path(__file__).parent / "resources" / "styles" / "dark.qss"
    if stylesheet.exists():
        app.setStyleSheet(stylesheet.read_text(encoding="utf-8"))
    window = MainWindow(config=config, config_path=config_path)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())

