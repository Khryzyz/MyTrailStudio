from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
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
    QSpinBox,
    QStackedWidget,
    QStatusBar,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ui_app import APP_NAME, APP_VERSION
from ui_app.paths import ENGINE_ROOT, LOGO_PATH
from ui_core.services.export_presets import apply_export_preset, list_export_presets
from ui_core.services.pipeline_adapter import run_engine_preview, run_engine_render_final, run_engine_validate
from ui_core.services.project_store import create_project, list_projects, load_project
from ui_core.services.project_summary import build_project_summary
from ui_core.services.project_validator import validate_project
from ui_core.services.video_service import add_video, add_videos_from_dir, remove_video


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
        self._stack.addWidget(self._build_videos_page())
        self._stack.addWidget(self._build_validation_page())
        self._stack.addWidget(self._build_export_page())

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

    def _build_videos_page(self) -> QWidget:
        page = QWidget()
        layout = QHBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(18)

        list_panel = QFrame()
        list_panel.setObjectName("contentPanel")
        list_layout = QVBoxLayout(list_panel)
        list_layout.setContentsMargins(20, 18, 20, 20)
        list_layout.setSpacing(12)

        title = QLabel("Videos")
        title.setObjectName("panelTitle")
        list_layout.addWidget(title)

        self._video_list = QListWidget()
        self._video_list.setObjectName("projectList")
        list_layout.addWidget(self._video_list, 1)

        remove_button = QPushButton("Remove selected")
        remove_button.setObjectName("secondaryButton")
        remove_button.clicked.connect(self._remove_selected_video)
        list_layout.addWidget(remove_button, 0, Qt.AlignLeft)

        import_panel = QFrame()
        import_panel.setObjectName("contentPanel")
        import_layout = QVBoxLayout(import_panel)
        import_layout.setContentsMargins(24, 22, 24, 24)
        import_layout.setSpacing(12)

        import_title = QLabel("Import")
        import_title.setObjectName("panelTitle")
        import_layout.addWidget(import_title)

        self._video_mode = QComboBox()
        self._video_mode.addItems(["normal", "hyperlapse"])
        import_layout.addWidget(self._labeled_field("Mode", self._video_mode))

        self._video_speed = QDoubleSpinBox()
        self._video_speed.setRange(1.0, 50.0)
        self._video_speed.setDecimals(2)
        self._video_speed.setValue(2.0)
        import_layout.addWidget(self._labeled_field("Input hyperlapse speed", self._video_speed))

        self._include_out_of_gpx = QCheckBox("Include videos outside GPX range")
        import_layout.addWidget(self._include_out_of_gpx)

        self._recursive_import = QCheckBox("Scan folders recursively")
        import_layout.addWidget(self._recursive_import)

        buttons = QHBoxLayout()
        add_file = QPushButton("Add video")
        add_file.setObjectName("primaryButton")
        add_file.clicked.connect(self._add_video_file)
        add_folder = QPushButton("Add folder")
        add_folder.setObjectName("secondaryButton")
        add_folder.clicked.connect(self._add_video_folder)
        buttons.addWidget(add_file)
        buttons.addWidget(add_folder)
        buttons.addStretch(1)
        import_layout.addLayout(buttons)
        import_layout.addStretch(1)

        layout.addWidget(list_panel, 3)
        layout.addWidget(import_panel, 2)
        return page

    def _build_validation_page(self) -> QWidget:
        panel = QFrame()
        panel.setObjectName("contentPanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(28, 26, 28, 28)
        layout.setSpacing(14)

        title = QLabel("Validation")
        title.setObjectName("panelTitle")
        layout.addWidget(title)

        self._validation_output = QTextEdit()
        self._validation_output.setReadOnly(True)
        self._validation_output.setPlaceholderText("Run validation to inspect coverage, warnings, errors, and gaps.")
        layout.addWidget(self._validation_output, 1)

        buttons = QHBoxLayout()
        validate_button = QPushButton("Validate project")
        validate_button.setObjectName("primaryButton")
        validate_button.clicked.connect(self._validate_active_project)
        engine_button = QPushButton("Engine dry run")
        engine_button.setObjectName("secondaryButton")
        engine_button.clicked.connect(self._engine_validate_active_project)
        buttons.addWidget(validate_button)
        buttons.addWidget(engine_button)
        buttons.addStretch(1)
        layout.addLayout(buttons)
        return panel

    def _build_export_page(self) -> QWidget:
        panel = QFrame()
        panel.setObjectName("contentPanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(28, 26, 28, 28)
        layout.setSpacing(14)

        title = QLabel("Export")
        title.setObjectName("panelTitle")
        layout.addWidget(title)

        self._preset_combo = QComboBox()
        for preset in list_export_presets():
            self._preset_combo.addItem(f"{preset['name']} ({preset['id']})", preset["id"])
        layout.addWidget(self._labeled_field("Export preset", self._preset_combo))

        self._preview_seconds = QSpinBox()
        self._preview_seconds.setRange(1, 60)
        self._preview_seconds.setValue(10)
        layout.addWidget(self._labeled_field("Preview seconds", self._preview_seconds))

        self._export_output = QTextEdit()
        self._export_output.setReadOnly(True)
        self._export_output.setPlaceholderText("Export actions and logs will appear here.")
        layout.addWidget(self._export_output, 1)

        buttons = QHBoxLayout()
        apply_button = QPushButton("Apply preset")
        apply_button.setObjectName("secondaryButton")
        apply_button.clicked.connect(self._apply_export_preset)
        preview_button = QPushButton("Generate preview")
        preview_button.setObjectName("primaryButton")
        preview_button.clicked.connect(self._generate_preview)
        render_button = QPushButton("Render final")
        render_button.setObjectName("secondaryButton")
        render_button.clicked.connect(self._render_final)
        buttons.addWidget(apply_button)
        buttons.addWidget(preview_button)
        buttons.addWidget(render_button)
        buttons.addStretch(1)
        layout.addLayout(buttons)
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
        self._refresh_video_list()

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
        self._refresh_video_list()

    def _open_selected_project(self) -> None:
        if not self._active_project:
            return
        self.statusBar().showMessage(
            f"Active project: {self._active_project['project']['name']} ({self._active_project['project']['id']})"
        )
        self._activate_page(2)

    def _require_active_project(self) -> dict | None:
        if self._active_project:
            return self._active_project
        QMessageBox.warning(self, APP_NAME, "Select or create a project first.")
        return None

    def _reload_active_project(self) -> None:
        if not self._active_project:
            return
        self._active_project = load_project(self._active_project["project"]["id"])
        self._refresh_projects()
        self._select_project_by_id(self._active_project["project"]["id"])

    def _refresh_video_list(self) -> None:
        if not hasattr(self, "_video_list"):
            return
        self._video_list.clear()
        if not self._active_project:
            return
        for video in self._active_project.get("assets", {}).get("videos", []):
            item = QListWidgetItem(
                f"{video['name']}\n"
                f"{video.get('gpx_status', 'unknown')} | {video.get('mode', 'normal')} | "
                f"{video.get('creation_time_utc') or 'NO TIME'}"
            )
            item.setData(Qt.UserRole, video["id"])
            self._video_list.addItem(item)

    def _add_video_file(self) -> None:
        project = self._require_active_project()
        if not project:
            return
        path, _ = QFileDialog.getOpenFileName(self, "Add video", "", "Videos (*.mp4 *.mov);;All files (*.*)")
        if not path:
            return
        try:
            add_video(
                project,
                Path(path),
                mode=self._video_mode.currentText(),
                hyperlapse_speed=float(self._video_speed.value()),
            )
        except Exception as exc:
            QMessageBox.critical(self, APP_NAME, f"Could not add video:\n{exc}")
            return
        self._reload_active_project()
        self.statusBar().showMessage("Video added")

    def _add_video_folder(self) -> None:
        project = self._require_active_project()
        if not project:
            return
        path = QFileDialog.getExistingDirectory(self, "Add videos from folder")
        if not path:
            return
        try:
            result = add_videos_from_dir(
                project,
                Path(path),
                mode=self._video_mode.currentText(),
                hyperlapse_speed=float(self._video_speed.value()),
                recursive=self._recursive_import.isChecked(),
                include_out_of_gpx=self._include_out_of_gpx.isChecked(),
            )
        except Exception as exc:
            QMessageBox.critical(self, APP_NAME, f"Could not import folder:\n{exc}")
            return
        self._reload_active_project()
        self.statusBar().showMessage(
            f"Folder import: {len(result['added'])} added, {len(result['skipped'])} skipped, {len(result['failed'])} failed"
        )

    def _remove_selected_video(self) -> None:
        project = self._require_active_project()
        if not project:
            return
        item = self._video_list.currentItem()
        if item is None:
            QMessageBox.warning(self, APP_NAME, "Select a video first.")
            return
        video_id = item.data(Qt.UserRole)
        try:
            removed = remove_video(project, video_id)
        except Exception as exc:
            QMessageBox.critical(self, APP_NAME, f"Could not remove video:\n{exc}")
            return
        self._reload_active_project()
        self.statusBar().showMessage(f"Removed video: {removed['name']}")

    def _validate_active_project(self) -> None:
        project = self._require_active_project()
        if not project:
            return
        try:
            report = validate_project(project)
        except Exception as exc:
            QMessageBox.critical(self, APP_NAME, f"Could not validate project:\n{exc}")
            return
        self._active_project = load_project(project["project"]["id"])
        self._validation_output.setPlainText(self._format_validation_report(report))
        self._refresh_projects()
        self._select_project_by_id(project["project"]["id"])
        self.statusBar().showMessage("Project validation completed")

    def _engine_validate_active_project(self) -> None:
        project = self._require_active_project()
        if not project:
            return
        self._validation_output.setPlainText("Running engine dry run...")
        code = run_engine_validate(project, quiet=True)
        self._active_project = load_project(project["project"]["id"])
        self._validation_output.append(f"\nEngine dry run exit code: {code}")
        self.statusBar().showMessage(f"Engine dry run finished with exit code {code}")

    def _apply_export_preset(self) -> None:
        project = self._require_active_project()
        if not project:
            return
        preset_id = self._preset_combo.currentData()
        try:
            result = apply_export_preset(project, preset_id)
        except Exception as exc:
            QMessageBox.critical(self, APP_NAME, f"Could not apply preset:\n{exc}")
            return
        self._active_project = load_project(project["project"]["id"])
        self._export_output.setPlainText(f"Applied preset: {result['preset_name']} ({result['preset_id']})")
        self.statusBar().showMessage(f"Applied preset: {result['preset_id']}")

    def _generate_preview(self) -> None:
        project = self._require_active_project()
        if not project:
            return
        self._export_output.setPlainText("Generating preview...")
        code = run_engine_preview(project, seconds=int(self._preview_seconds.value()), quiet=True)
        self._active_project = load_project(project["project"]["id"])
        self._export_output.append(f"\nPreview exit code: {code}")
        self.statusBar().showMessage(f"Preview finished with exit code {code}")

    def _render_final(self) -> None:
        project = self._require_active_project()
        if not project:
            return
        confirm = QMessageBox.question(
            self,
            APP_NAME,
            "Render final video now? This can take a long time.",
            QMessageBox.Yes | QMessageBox.No,
        )
        if confirm != QMessageBox.Yes:
            return
        self._export_output.setPlainText("Rendering final video...")
        code = run_engine_render_final(project, quiet=True)
        self._active_project = load_project(project["project"]["id"])
        self._export_output.append(f"\nFinal render exit code: {code}")
        self.statusBar().showMessage(f"Final render finished with exit code {code}")

    def _format_validation_report(self, report: dict) -> str:
        lines = [
            "Project validation",
            f"Project: {report['project_id']}",
            f"Videos: {report['videos']}",
            f"Timelines: {report['timelines']}",
            f"Detected gaps: {len(report['gaps'])}",
        ]
        coverage = report.get("coverage", {})
        if coverage:
            lines.append(f"GPX coverage: {coverage.get('percent')}% ({coverage.get('overlap_seconds')} s)")
        if report.get("warnings"):
            lines.append("\nWarnings:")
            lines.extend(f" - {warning}" for warning in report["warnings"])
        if report.get("errors"):
            lines.append("\nErrors:")
            lines.extend(f" - {error}" for error in report["errors"])
        if report.get("gaps"):
            lines.append("\nGaps:")
            for gap in report["gaps"][:20]:
                lines.append(f" - Timeline {gap['timeline_id']}: {gap['seconds']} s")
            if len(report["gaps"]) > 20:
                lines.append(f" - ... {len(report['gaps']) - 20} more")
        return "\n".join(lines)

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
