APP_STYLESHEET = """
QMainWindow {
    background: #f6f7f9;
}

QWidget {
    color: #17202a;
    font-family: "Segoe UI";
    font-size: 10pt;
}

QFrame#sidebar {
    background: #101820;
    border: none;
}

QLabel#sidebarTitle {
    color: #ffffff;
    font-size: 13pt;
    font-weight: 700;
}

QLabel#sidebarSubtitle {
    color: #aab7c4;
    font-size: 9pt;
}

QFrame#logoPanel {
    background: #ffffff;
    border-radius: 8px;
    border: 1px solid #e5ebf0;
}

QPushButton#navButton {
    background: transparent;
    border: 1px solid transparent;
    border-radius: 6px;
    color: #dce5ee;
    padding: 10px 12px;
    text-align: left;
}

QPushButton#navButton:hover {
    background: #1a2a36;
}

QPushButton#navButton[active="true"] {
    background: #243746;
    border-color: #35556a;
    color: #ffffff;
}

QFrame#topBar {
    background: #ffffff;
    border-bottom: 1px solid #dfe5eb;
}

QLabel#pageTitle {
    font-size: 18pt;
    font-weight: 700;
}

QLabel#pageSubtitle {
    color: #536171;
}

QFrame#contentPanel {
    background: #ffffff;
    border: 1px solid #dfe5eb;
    border-radius: 8px;
}

QLabel#panelTitle {
    font-size: 13pt;
    font-weight: 700;
}

QLabel#muted {
    color: #536171;
}

QLabel#fieldLabel {
    color: #2b3845;
    font-weight: 600;
}

QLineEdit {
    background: #ffffff;
    border: 1px solid #c9d3dc;
    border-radius: 6px;
    padding: 9px 10px;
}

QLineEdit:focus {
    border-color: #1769aa;
}

QListWidget#projectList {
    background: #ffffff;
    border: 1px solid #d8e0e7;
    border-radius: 6px;
    outline: none;
}

QListWidget#projectList::item {
    border-bottom: 1px solid #edf1f4;
    padding: 10px;
}

QListWidget#projectList::item:selected {
    background: #e7f1fa;
    color: #102033;
}

QPushButton#primaryButton {
    background: #1769aa;
    border: none;
    border-radius: 6px;
    color: #ffffff;
    font-weight: 600;
    padding: 9px 14px;
}

QPushButton#primaryButton:hover {
    background: #12598f;
}

QPushButton#secondaryButton {
    background: #ffffff;
    border: 1px solid #c9d3dc;
    border-radius: 6px;
    color: #17202a;
    padding: 9px 14px;
}

QStatusBar {
    background: #ffffff;
    border-top: 1px solid #dfe5eb;
    color: #536171;
}
"""
