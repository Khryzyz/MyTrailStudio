from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QStackedWidget,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from ui_app import APP_NAME, APP_VERSION
from ui_app.paths import ENGINE_ROOT, LOGO_PATH
from ui_core.services.project_store import create_project, list_projects, load_project
from ui_core.services.project_summary import build_project_summary


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.resize(1180, 760)
        self.setMinimumSize(980, 640)

        self._nav_buttons: list[QPushButton] = []
        self._stack = QStackedWidget()
        self._projects: list[dict] = []
        self._active_project: dict | None = None

        root = QWidget()
        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)
        root_layout.addWidget(self._build_sidebar())
        root_layout.addWidget(self._build_workspace(), 1)
        self.setCentralWidget(root)

        status = QStatusBar()
        status.showMessage(f"{APP_NAME} UI {APP_VERSION} ready")
        self.setStatusBar(status)

        self._activate_page(0)

    def _build_sidebar(self) -> QWidget:
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(248)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(20, 22, 20, 20)
        layout.setSpacing(14)

        logo_panel = QFrame()
        logo_panel.setObjectName("logoPanel")
        logo_panel.setFixedHeight(82)
        logo_layout = QHBoxLayout(logo_panel)
        logo_layout.setContentsMargins(14, 12, 14, 12)

        logo = QLabel()
        logo.setAlignment(Qt.AlignCenter)
        if LOGO_PATH.is_file():
            pixmap = QPixmap(str(LOGO_PATH))
            logo.setPixmap(pixmap.scaledToWidth(176, Qt.SmoothTransformation))
        logo_layout.addWidget(logo)
        layout.addWidget(logo_panel)

        title = QLabel(APP_NAME)
        title.setObjectName("sidebarTitle")
        layout.addWidget(title)

        subtitle = QLabel("Route overlay studio")
        subtitle.setObjectName("sidebarSubtitle")
        layout.addWidget(subtitle)

        layout.addSpacing(12)
        for index, label in enumerate(["Projects", "Setup", "Videos", "Validation", "Export"]):
            button = QPushButton(label)
            button.setObjectName("navButton")
            button.setCursor(Qt.PointingHandCursor)
            button.clicked.connect(lambda checked=False, page=index: self._activate_page(page))
            self._nav_buttons.append(button)
            layout.addWidget(button)

        layout.addStretch(1)

        version = QLabel(f"UI {APP_VERSION}")
        version.setObjectName("sidebarSubtitle")
        layout.addWidget(version)

        return sidebar

    def _build_workspace(self) -> QWidget:
        workspace = QWidget()
        layout = QVBoxLayout(workspace)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(self._build_top_bar())

        content_wrap = QWidget()
        content_layout = QVBoxLayout(content_wrap)
        content_layout.setContentsMargins(28, 28, 28, 28)
        content_layout.setSpacing(18)

        self._stack.addWidget(self._build_projects_page())
        self._stack.addWidget(self._build_setup_page())
        self._stack.addWidget(self._placeholder_page(
            "Videos",
            "Import videos and review timestamps before rendering.",
            "Video status, manual dates, and hyperlapse settings will live here.",
            ["Add video", "Add folder"],
        ))
        self._stack.addWidget(self._placeholder_page(
            "Validation",
            "Review GPX coverage, gaps, warnings, and technical readiness.",
            "The validation view will reuse ui_core project reports.",
            ["Validate project"],
        ))
        self._stack.addWidget(self._placeholder_page(
            "Export",
            "Apply presets, generate previews, and run final renders.",
            "Render actions will stay behind explicit confirmation.",
            ["Apply preset", "Generate preview"],
        ))

        content_layout.addWidget(self._stack)
        layout.addWidget(content_wrap, 1)
        self._refresh_projects()
        return workspace

    def _build_top_bar(self) -> QWidget:
        top_bar = QFrame()
        top_bar.setObjectName("topBar")
        top_bar.setFixedHeight(74)

        layout = QHBoxLayout(top_bar)
        layout.setContentsMargins(28, 0, 28, 0)
        layout.setSpacing(16)

        self._page_title = QLabel("Projects")
        self._page_title.setObjectName("pageTitle")
        layout.addWidget(self._page_title)

        self._page_subtitle = QLabel("Start by selecting a project.")
        self._page_subtitle.setObjectName("pageSubtitle")
        layout.addWidget(self._page_subtitle, 1)

        return top_bar

    def _placeholder_page(
        self,
        title: str,
        subtitle: str,
        body: str,
        actions: list[str],
    ) -> QWidget:
        panel = QFrame()
        panel.setObjectName("contentPanel")
        panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(28, 26, 28, 28)
        layout.setSpacing(14)

        title_label = QLabel(title)
        title_label.setObjectName("panelTitle")
        layout.addWidget(title_label)

        subtitle_label = QLabel(subtitle)
        subtitle_label.setObjectName("muted")
        subtitle_label.setWordWrap(True)
        layout.addWidget(subtitle_label)

        body_label = QLabel(body)
        body_label.setObjectName("muted")
        body_label.setWordWrap(True)
        layout.addWidget(body_label)

        button_row = QHBoxLayout()
        button_row.setSpacing(10)
        for index, action in enumerate(actions):
            button = QPushButton(action)
            button.setObjectName("primaryButton" if index == 0 else "secondaryButton")
            button.setEnabled(False)
            button_row.addWidget(button)
        button_row.addStretch(1)
        layout.addLayout(button_row)

        layout.addStretch(1)
        return panel

    def _build_projects_page(self) -> QWidget:
        page = QWidget()
        layout = QHBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(18)

        list_panel = QFrame()
        list_panel.setObjectName("contentPanel")
        list_layout = QVBoxLayout(list_panel)
        list_layout.setContentsMargins(20, 18, 20, 20)
        list_layout.setSpacing(12)

        header = QLabel("Projects")
        header.setObjectName("panelTitle")
        list_layout.addWidget(header)

        self._project_list = QListWidget()
        self._project_list.setObjectName("projectList")
        self._project_list.currentItemChanged.connect(self._select_project_item)
        list_layout.addWidget(self._project_list, 1)

        button_row = QHBoxLayout()
        refresh_button = QPushButton("Refresh")
        refresh_button.setObjectName("secondaryButton")
        refresh_button.clicked.connect(self._refresh_projects)
        new_button = QPushButton("New project")
        new_button.setObjectName("primaryButton")
        new_button.clicked.connect(lambda: self._activate_page(1))
        button_row.addWidget(refresh_button)
        button_row.addWidget(new_button)
        list_layout.addLayout(button_row)

        details_panel = QFrame()
        details_panel.setObjectName("contentPanel")
        details_layout = QVBoxLayout(details_panel)
        details_layout.setContentsMargins(24, 22, 24, 24)
        details_layout.setSpacing(12)

        details_title = QLabel("Project Details")
        details_title.setObjectName("panelTitle")
        details_layout.addWidget(details_title)

        self._project_details = QLabel("Select a project to see its summary.")
        self._project_details.setObjectName("muted")
        self._project_details.setWordWrap(True)
        details_layout.addWidget(self._project_details)

        self._open_project_button = QPushButton("Open selected project")
        self._open_project_button.setObjectName("primaryButton")
        self._open_project_button.setEnabled(False)
        self._open_project_button.clicked.connect(self._open_selected_project)
        details_layout.addWidget(self._open_project_button, 0, Qt.AlignLeft)
        details_layout.addStretch(1)

        layout.addWidget(list_panel, 2)
        layout.addWidget(details_panel, 3)
        return page

    def _build_setup_page(self) -> QWidget:
        panel = QFrame()
        panel.setObjectName("contentPanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(28, 26, 28, 28)
        layout.setSpacing(14)

        title = QLabel("Create Project")
        title.setObjectName("panelTitle")
        layout.addWidget(title)

        subtitle = QLabel("Create a centralized project file while keeping GPX and videos in their original folders.")
        subtitle.setObjectName("muted")
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        self._project_name_input = QLineEdit()
        self._project_name_input.setPlaceholderText("Project name")
        layout.addWidget(self._labeled_field("Name", self._project_name_input))

        self._gpx_input = QLineEdit()
        self._gpx_input.setPlaceholderText("Select a .gpx file")
        layout.addWidget(self._path_field("GPX", self._gpx_input, self._browse_gpx))

        self._output_input = QLineEdit()
        self._output_input.setPlaceholderText("Select output folder")
        layout.addWidget(self._path_field("Output", self._output_input, self._browse_output))

        actions = QHBoxLayout()
        create_button = QPushButton("Create project")
        create_button.setObjectName("primaryButton")
        create_button.clicked.connect(self._create_project_from_form)
        cancel_button = QPushButton("Back to projects")
        cancel_button.setObjectName("secondaryButton")
        cancel_button.clicked.connect(lambda: self._activate_page(0))
        actions.addWidget(create_button)
        actions.addWidget(cancel_button)
        actions.addStretch(1)
        layout.addLayout(actions)
        layout.addStretch(1)
        return panel

    def _labeled_field(self, label: str, widget: QWidget) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        text = QLabel(label)
        text.setObjectName("fieldLabel")
        layout.addWidget(text)
        layout.addWidget(widget)
        return container

    def _path_field(self, label: str, line_edit: QLineEdit, browse_callback) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        text = QLabel(label)
        text.setObjectName("fieldLabel")
        layout.addWidget(text)

        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(8)
        row.addWidget(line_edit, 1)
        browse = QPushButton("Browse")
        browse.setObjectName("secondaryButton")
        browse.clicked.connect(browse_callback)
        row.addWidget(browse)
        layout.addLayout(row)
        return container

    def _refresh_projects(self) -> None:
        self._projects = list_projects()
        self._project_list.clear()
        for project in self._projects:
            item = QListWidgetItem(f"{project['name']}\n{project['id']}")
            item.setData(Qt.UserRole, project["id"])
            self._project_list.addItem(item)

        if self._projects:
            self._project_list.setCurrentRow(0)
            self.statusBar().showMessage(f"Loaded {len(self._projects)} project(s)")
        else:
            self._active_project = None
            self._project_details.setText("No projects found. Create one from Project Setup.")
            self._open_project_button.setEnabled(False)
            self.statusBar().showMessage("No projects found")

    def _select_project_item(self, current: QListWidgetItem | None, previous: QListWidgetItem | None = None) -> None:
        if current is None:
            return
        project_id = current.data(Qt.UserRole)
        try:
            project = load_project(project_id)
            summary = build_project_summary(project)
        except Exception as exc:
            self._active_project = None
            self._open_project_button.setEnabled(False)
            self._project_details.setText(f"Could not load project: {exc}")
            return

        self._active_project = project
        self._open_project_button.setEnabled(True)
        gpx = summary["gpx"]
        export = summary["export"]
        self._project_details.setText(
            f"Name: {summary['project']['name']}\n"
            f"ID: {summary['project']['id']}\n"
            f"Updated: {summary['project']['updated_at_utc']}\n\n"
            f"GPX: {gpx.get('start_utc')} -> {gpx.get('end_utc')}\n"
            f"Distance: {round(float(gpx.get('distance_m') or 0) / 1000, 3)} km\n"
            f"Videos: {summary['videos']['count']}\n"
            f"Output: {export.get('output_dir')}"
        )

    def _open_selected_project(self) -> None:
        if not self._active_project:
            return
        self.statusBar().showMessage(
            f"Active project: {self._active_project['project']['name']} ({self._active_project['project']['id']})"
        )
        self._activate_page(2)

    def _browse_gpx(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Select GPX", "", "GPX files (*.gpx);;All files (*.*)")
        if path:
            self._gpx_input.setText(path)
            if not self._project_name_input.text().strip():
                self._project_name_input.setText(Path(path).stem)

    def _browse_output(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Select output folder")
        if path:
            self._output_input.setText(path)

    def _create_project_from_form(self) -> None:
        name = self._project_name_input.text().strip()
        gpx_path = self._gpx_input.text().strip()
        output_dir = self._output_input.text().strip()

        if not name or not gpx_path or not output_dir:
            QMessageBox.warning(self, APP_NAME, "Name, GPX, and output folder are required.")
            return

        try:
            project = create_project(
                name=name,
                gpx_path=Path(gpx_path),
                output_dir=Path(output_dir),
                engine_root=ENGINE_ROOT,
            )
        except Exception as exc:
            QMessageBox.critical(self, APP_NAME, f"Could not create project:\n{exc}")
            return

        self._project_name_input.clear()
        self._gpx_input.clear()
        self._output_input.clear()
        self._refresh_projects()
        self._select_project_by_id(project["project"]["id"])
        self._activate_page(0)
        self.statusBar().showMessage(f"Project created: {project['project']['name']}")

    def _select_project_by_id(self, project_id: str) -> None:
        for row in range(self._project_list.count()):
            item = self._project_list.item(row)
            if item.data(Qt.UserRole) == project_id:
                self._project_list.setCurrentRow(row)
                return

    def _activate_page(self, index: int) -> None:
        self._stack.setCurrentIndex(index)
        for button_index, button in enumerate(self._nav_buttons):
            button.setProperty("active", button_index == index)
            button.style().unpolish(button)
            button.style().polish(button)

        button = self._nav_buttons[index]
        self._page_title.setText(button.text())
        subtitles = [
            "Select or create a project workspace.",
            "Prepare GPX and output settings.",
            "Import and classify camera footage.",
            "Check coverage and project readiness.",
            "Choose presets and render outputs.",
        ]
        self._page_subtitle.setText(subtitles[index])
