from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from ui_core.models.project_model import new_project_document
from ui_core.services.app_paths import resolve_app_data_dir
from ui_core.services.engine_root import resolve_engine_root
from ui_core.services.gpx_service import summarize_gpx
from ui_core.services.json_io import read_json, write_json


PROJECT_FILE_NAME = "project.overlayproject.json"


def projects_dir(app_data_dir: Path) -> Path:
    return app_data_dir / "projects"


def project_file(project_data_dir: Path) -> Path:
    return project_data_dir / PROJECT_FILE_NAME


def create_project(
    *,
    name: str,
    gpx_path: Path,
    output_dir: Path,
    engine_root: Path,
    app_data_dir: Path | None = None,
    timezone_name: str = "America/Bogota",
) -> dict[str, Any]:
    app_dir = resolve_app_data_dir(str(app_data_dir)) if app_data_dir else resolve_app_data_dir()
    engine_root = resolve_engine_root(str(engine_root) if engine_root else None)
    gpx_path = gpx_path.resolve()
    output_dir = output_dir.resolve()

    if not gpx_path.is_file():
        raise FileNotFoundError(f"No existe GPX: {gpx_path}")

    output_dir.mkdir(parents=True, exist_ok=True)
    gpx_summary = summarize_gpx(engine_root, gpx_path)

    temp_project_dir = projects_dir(app_dir) / "_creating"
    document = new_project_document(
        name=name,
        timezone_name=timezone_name,
        engine_root=str(engine_root),
        project_data_dir=str(temp_project_dir).replace("\\", "/"),
        gpx_path=str(gpx_path),
        output_dir=str(output_dir),
        gpx_summary=gpx_summary,
    )

    project_id = document["project"]["id"]
    final_project_dir = projects_dir(app_dir) / project_id
    document["workspace"]["project_data_dir"] = str(final_project_dir).replace("\\", "/")
    document["workspace"]["runtime_dir"] = str(final_project_dir / "runtime").replace("\\", "/")
    document["workspace"]["temp_dir"] = str(final_project_dir / "temp").replace("\\", "/")
    document["workspace"]["cache_dir"] = str(final_project_dir / "cache").replace("\\", "/")
    document["workspace"]["logs_dir"] = str(final_project_dir / "logs").replace("\\", "/")

    for key in ["runtime_dir", "temp_dir", "cache_dir", "logs_dir"]:
        Path(document["workspace"][key]).mkdir(parents=True, exist_ok=True)

    write_json(project_file(final_project_dir), document)
    return document


def load_project(project_path_or_id: str, app_data_dir: Path | None = None) -> dict[str, Any]:
    candidate = Path(project_path_or_id).expanduser()
    if candidate.exists():
        path = candidate if candidate.is_file() else project_file(candidate)
        return read_json(path)

    app_dir = resolve_app_data_dir(str(app_data_dir)) if app_data_dir else resolve_app_data_dir()
    path = project_file(projects_dir(app_dir) / project_path_or_id)
    if not path.is_file():
        raise FileNotFoundError(f"No existe proyecto: {project_path_or_id}")
    return read_json(path)


def list_projects(app_data_dir: Path | None = None) -> list[dict[str, Any]]:
    app_dir = resolve_app_data_dir(str(app_data_dir)) if app_data_dir else resolve_app_data_dir()
    root = projects_dir(app_dir)
    if not root.is_dir():
        return []

    result = []
    for path in root.glob(f"*/{PROJECT_FILE_NAME}"):
        try:
            project = read_json(path)
        except Exception:
            continue
        result.append({
            "id": project["project"]["id"],
            "name": project["project"]["name"],
            "updated_at_utc": project["project"].get("updated_at_utc"),
            "gpx_start_utc": project.get("gpx_summary", {}).get("start_utc"),
            "gpx_end_utc": project.get("gpx_summary", {}).get("end_utc"),
            "videos": len(project.get("assets", {}).get("videos", [])),
            "path": str(path),
        })

    return sorted(result, key=lambda item: item.get("updated_at_utc") or "", reverse=True)


def delete_project(project_path_or_id: str, app_data_dir: Path | None = None) -> dict[str, Any]:
    project = load_project(project_path_or_id, app_data_dir)
    project_dir = Path(project["workspace"]["project_data_dir"]).resolve()
    project_path = project_file(project_dir).resolve()

    if not project_path.is_file():
        raise FileNotFoundError(f"No existe archivo de proyecto: {project_path}")

    app_dir = resolve_app_data_dir(str(app_data_dir)) if app_data_dir else resolve_app_data_dir()
    allowed_root = projects_dir(app_dir).resolve()

    try:
        project_dir.relative_to(allowed_root)
    except ValueError:
        raise ValueError(f"No se elimina un proyecto fuera del almacen central: {project_dir}")

    shutil.rmtree(project_dir)
    return {
        "id": project["project"]["id"],
        "name": project["project"]["name"],
        "deleted_dir": str(project_dir),
    }


def save_project(document: dict[str, Any]) -> Path:
    path = project_file(Path(document["workspace"]["project_data_dir"]))
    write_json(path, document)
    return path
