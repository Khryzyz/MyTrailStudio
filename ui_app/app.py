from __future__ import annotations

import sys

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from ui_app import APP_NAME
from ui_app.main_window import MainWindow
from ui_app.paths import ISOTYPE_PATH
from ui_app.styles import APP_STYLESHEET


def run(argv: list[str] | None = None) -> int:
    app = QApplication(argv or sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName("MyTrailStudio")
    app.setStyleSheet(APP_STYLESHEET)

    if ISOTYPE_PATH.is_file():
        app.setWindowIcon(QIcon(str(ISOTYPE_PATH)))

    window = MainWindow()
    window.show()
    return app.exec()
