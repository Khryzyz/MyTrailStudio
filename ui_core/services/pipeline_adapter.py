from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Any

from ui_core.models.project_model import touch_project
from ui_core.services.engine_config_builder import build_engine_config
from ui_core.services.engine_root import resolve_engine_root
from ui_core.services.project_store import save_project


def run_engine_validate(project: dict[str, Any]) -> int:
    engine_root = resolve_engine_root(project["workspace"].get("engine_root"))
    config_path = build_engine_config(project)
    validate_script = engine_root / "scripts" / "validate_pipeline.py"

    cmd = [
        sys.executable,
        str(validate_script),
        "--root",
        str(engine_root),
        "--config",
        str(config_path),
        "--validate-only",
    ]

    completed = subprocess.run(cmd, cwd=str(engine_root))
    manifest_path = Path(project["export"]["output_dir"]) / "data" / "manifest.json"
    if manifest_path.exists():
        project["engine"]["last_manifest_path"] = str(manifest_path)
        touch_project(project)
        save_project(project)

    return completed.returncode


def run_engine_preview(project: dict[str, Any], seconds: int = 10) -> int:
    if seconds < 1 or seconds > 60:
        raise ValueError("La preview debe estar entre 1 y 60 segundos.")

    engine_root = resolve_engine_root(project["workspace"].get("engine_root"))
    config_path = build_engine_config(project, overrides={
        "preview": {
            "enabled": True,
            "seconds": seconds,
        }
    })

    validate_script = engine_root / "scripts" / "validate_pipeline.py"
    render_preview_script = engine_root / "scripts" / "render_preview.py"
    manifest_path = Path(project["export"]["output_dir"]) / "data" / "manifest.json"

    validate_cmd = [
        sys.executable,
        str(validate_script),
        "--root",
        str(engine_root),
        "--config",
        str(config_path),
    ]

    validate_result = subprocess.run(validate_cmd, cwd=str(engine_root))
    if validate_result.returncode != 0:
        return validate_result.returncode

    if not manifest_path.exists():
        raise FileNotFoundError(f"No se encontro manifest despues de validar: {manifest_path}")

    project["engine"]["last_manifest_path"] = str(manifest_path)
    touch_project(project)
    save_project(project)

    preview_cmd = [
        sys.executable,
        str(render_preview_script),
        "--root",
        str(engine_root),
        "--manifest",
        str(manifest_path),
    ]
    return subprocess.run(preview_cmd, cwd=str(engine_root)).returncode


def run_engine_render_final(project: dict[str, Any]) -> int:
    engine_root = resolve_engine_root(project["workspace"].get("engine_root"))
    config_path = build_engine_config(project, overrides={
        "preview": {
            "enabled": False,
        }
    })

    validate_script = engine_root / "scripts" / "validate_pipeline.py"
    render_final_script = engine_root / "scripts" / "render_final.py"
    manifest_path = Path(project["export"]["output_dir"]) / "data" / "manifest.json"

    validate_cmd = [
        sys.executable,
        str(validate_script),
        "--root",
        str(engine_root),
        "--config",
        str(config_path),
    ]

    validate_result = subprocess.run(validate_cmd, cwd=str(engine_root))
    if validate_result.returncode != 0:
        return validate_result.returncode

    if not manifest_path.exists():
        raise FileNotFoundError(f"No se encontro manifest despues de validar: {manifest_path}")

    project["engine"]["last_manifest_path"] = str(manifest_path)
    touch_project(project)
    save_project(project)

    render_cmd = [
        sys.executable,
        str(render_final_script),
        "--root",
        str(engine_root),
        "--manifest",
        str(manifest_path),
    ]
    return subprocess.run(render_cmd, cwd=str(engine_root)).returncode
