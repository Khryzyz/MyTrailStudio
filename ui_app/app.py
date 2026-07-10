from __future__ import annotations

import sys

from PySide6.QtGui import QColor, QIcon, QPalette
from PySide6.QtWidgets import QApplication

from ui_app import APP_NAME
from ui_app.main_window import MainWindow
from ui_app.paths import ISOTYPE_PATH
from ui_app.styles import APP_STYLESHEET


def run(argv: list[str] | None = None) -> int:
    app = QApplication(argv or sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName("MyTrailStudio")
    app.setStyle("Fusion")
    app.setPalette(_dark_palette())
    app.setStyleSheet(APP_STYLESHEET)

    if ISOTYPE_PATH.is_file():
        app.setWindowIcon(QIcon(str(ISOTYPE_PATH)))

    window = MainWindow()
    window.show()
    return app.exec()


def _dark_palette() -> QPalette:
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor("#0f141a"))
    palette.setColor(QPalette.WindowText, QColor("#edf2f7"))
    palette.setColor(QPalette.Base, QColor("#151b23"))
    palette.setColor(QPalette.AlternateBase, QColor("#1b2430"))
    palette.setColor(QPalette.ToolTipBase, QColor("#202a35"))
    palette.setColor(QPalette.ToolTipText, QColor("#edf2f7"))
    palette.setColor(QPalette.Text, QColor("#edf2f7"))
    palette.setColor(QPalette.Button, QColor("#1b2430"))
    palette.setColor(QPalette.ButtonText, QColor("#edf2f7"))
    palette.setColor(QPalette.BrightText, QColor("#ffffff"))
    palette.setColor(QPalette.Highlight, QColor("#3b82c4"))
    palette.setColor(QPalette.HighlightedText, QColor("#ffffff"))
    palette.setColor(QPalette.Disabled, QPalette.Text, QColor("#7d8a99"))
    palette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor("#7d8a99"))
    return palette
