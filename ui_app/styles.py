APP_STYLESHEET = """
QMainWindow {
    background: #0f141a;
}

QWidget {
    color: #edf2f7;
    font-family: "Segoe UI";
    font-size: 10pt;
}

QFrame#sidebar {
    background: #0b1117;
    border-right: 1px solid #202a35;
}

QLabel#sidebarTitle {
    color: #ffffff;
    font-size: 13pt;
    font-weight: 700;
}

QLabel#sidebarSubtitle {
    color: #94a3b8;
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
    color: #dbe7f3;
    padding: 10px 12px;
    text-align: left;
}

QPushButton#navButton:hover {
    background: #152130;
}

QPushButton#navButton[active="true"] {
    background: #1d3347;
    border-color: #2f5f85;
    color: #ffffff;
}

QFrame#topBar {
    background: #121922;
    border-bottom: 1px solid #273241;
}

QLabel#pageTitle {
    font-size: 18pt;
    font-weight: 700;
}

QLabel#pageSubtitle {
    color: #9aa8b7;
}

QFrame#contentPanel {
    background: #151d27;
    border: 1px solid #283545;
    border-radius: 8px;
}

QLabel#panelTitle {
    font-size: 13pt;
    font-weight: 700;
}

QLabel#muted {
    color: #a8b3c1;
}

QLabel#fieldLabel {
    color: #d9e3ee;
    font-weight: 600;
}

QLineEdit,
QTextEdit,
QComboBox,
QSpinBox,
QDoubleSpinBox {
    background: #0f1620;
    border: 1px solid #334155;
    border-radius: 6px;
    color: #edf2f7;
    padding: 9px 10px;
    selection-background-color: #2f6f9f;
    selection-color: #ffffff;
}

QTextEdit {
    padding: 10px;
}

QLineEdit:focus,
QTextEdit:focus,
QComboBox:focus,
QSpinBox:focus,
QDoubleSpinBox:focus {
    border-color: #3b82c4;
}

QComboBox::drop-down {
    border: none;
    width: 28px;
}

QComboBox QAbstractItemView {
    background: #111923;
    border: 1px solid #334155;
    color: #edf2f7;
    selection-background-color: #244968;
}

QCheckBox {
    color: #edf2f7;
    spacing: 8px;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 1px solid #4b5f75;
    border-radius: 3px;
    background: #0f1620;
}

QCheckBox::indicator:checked {
    background: #2f80c7;
    border-color: #57a6e8;
}

QListWidget#projectList {
    background: #0f1620;
    border: 1px solid #334155;
    border-radius: 6px;
    color: #edf2f7;
    outline: none;
}

QListWidget#projectList::item {
    border-bottom: 1px solid #1f2a37;
    padding: 10px;
}

QListWidget#projectList::item:hover {
    background: #182535;
}

QListWidget#projectList::item:selected {
    background: #244968;
    color: #ffffff;
}

QPushButton#primaryButton {
    background: #2f80c7;
    border: none;
    border-radius: 6px;
    color: #ffffff;
    font-weight: 600;
    padding: 9px 14px;
}

QPushButton#primaryButton:hover {
    background: #276da9;
}

QPushButton#primaryButton:disabled,
QPushButton#secondaryButton:disabled {
    background: #202a35;
    border: 1px solid #303d4d;
    color: #718096;
}

QPushButton#secondaryButton {
    background: #192331;
    border: 1px solid #405166;
    border-radius: 6px;
    color: #edf2f7;
    padding: 9px 14px;
}

QPushButton#secondaryButton:hover {
    background: #223247;
}

QStatusBar {
    background: #121922;
    border-top: 1px solid #273241;
    color: #a8b3c1;
}

QMessageBox {
    background: #151d27;
}

QMessageBox QLabel {
    color: #edf2f7;
}
"""
