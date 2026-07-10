from __future__ import annotations

import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ui_core.models.project_model import touch_project
from ui_core.services.engine_config_builder import build_engine_config
from ui_core.services.engine_root import resolve_engine_root
from ui_core.services.project_store import save_project


def _log_path(project: dict[str, Any], action: str) -> Path:
    logs_dir = Path(project["workspace"]["logs_dir"])
    logs_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return logs_dir / f"{stamp}_{action}.log"


def _run_logged(
    cmd: list[str],
    *,
    cwd: Path,
    log_path: Path,
    quiet: bool = False,
    label: str = "engine command",
) -> int:
    started_at = datetime.now(timezone.utc)
    if quiet:
        print(f"Running {label}...")
    with log_path.open("w", encoding="utf-8", errors="replace") as log:
        log.write(f"Started UTC: {started_at.isoformat()}\n")
        log.write(f"Working directory: {cwd}\n")
        log.write("Command:\n")
        log.write(" ".join(cmd))
        log.write("\n\nOutput:\n")
        log.flush()

        if quiet:
            completed = subprocess.run(
                cmd,
                cwd=str(cwd),
                stdout=log,
                stderr=subprocess.STDOUT,
                text=True,
            )
            ended_at = datetime.now(timezone.utc)
            duration = (ended_at - started_at).total_seconds()
            log.write("\n")
            log.write(f"Finished UTC: {ended_at.isoformat()}\n")
            log.write(f"Duration seconds: {round(duration, 2)}\n")
            log.write(f"Exit code: {completed.returncode}\n")
            return completed.returncode

        process = subprocess.Popen(
            cmd,
            cwd=str(cwd),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        assert process.stdout is not None
        for line in process.stdout:
            print(line, end="")
            log.write(line)
        code = process.wait()
        ended_at = datetime.now(timezone.utc)
        duration = (ended_at - started_at).total_seconds()
        log.write("\n")
        log.write(f"Finished UTC: {ended_at.isoformat()}\n")
        log.write(f"Duration seconds: {round(duration, 2)}\n")
        log.write(f"Exit code: {code}\n")
        print(f"{label} finished with exit code {code}. Log: {log_path}")
        return code


def _remember_log(project: dict[str, Any], action: str, log_path: Path) -> None:
    engine = project.setdefault("engine", {})
    logs = engine.setdefault("logs", {})
    logs[action] = str(log_path)
    touch_project(project)
    save_project(project)


def run_engine_validate(project: dict[str, Any], quiet: bool = False) -> int:
    engine_root = resolve_engine_root(project["workspace"].get("engine_root"))
    config_path = build_engine_config(project)
    validate_script = engine_root / "scripts" / "validate_pipeline.py"
    log_path = _log_path(project, "engine_validate")

    cmd = [
        sys.executable,
        str(validate_script),
        "--root",
        str(engine_root),
        "--config",
        str(config_path),
        "--validate-only",
    ]

    code = _run_logged(cmd, cwd=engine_root, log_path=log_path, quiet=quiet, label="engine validation")
    _remember_log(project, "engine_validate", log_path)
    manifest_path = Path(project["export"]["output_dir"]) / "data" / "manifest.json"
    if manifest_path.exists():
        project["engine"]["last_manifest_path"] = str(manifest_path)
        touch_project(project)
        save_project(project)

    if quiet:
        print(f"engine validation finished with exit code {code}. Log: {log_path}")
    return code


def run_engine_preview(project: dict[str, Any], seconds: int = 10, quiet: bool = False) -> int:
    if seconds < 1 or seconds > 60:
        raise ValueError("Preview must be between 1 and 60 seconds.")

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
    validate_log_path = _log_path(project, "engine_preview_validate")
    preview_log_path = _log_path(project, "engine_preview")

    validate_cmd = [
        sys.executable,
        str(validate_script),
        "--root",
        str(engine_root),
        "--config",
        str(config_path),
    ]

    validate_code = _run_logged(
        validate_cmd,
        cwd=engine_root,
        log_path=validate_log_path,
        quiet=quiet,
        label="preview validation",
    )
    _remember_log(project, "engine_preview_validate", validate_log_path)
    if validate_code != 0:
        if quiet:
            print(f"preview validation finished with exit code {validate_code}. Log: {validate_log_path}")
        return validate_code

    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found after validation: {manifest_path}")

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
    code = _run_logged(preview_cmd, cwd=engine_root, log_path=preview_log_path, quiet=quiet, label="preview render")
    _remember_log(project, "engine_preview", preview_log_path)
    if quiet:
        print(f"preview render finished with exit code {code}. Log: {preview_log_path}")
    return code


def run_engine_render_final(project: dict[str, Any], quiet: bool = False) -> int:
    engine_root = resolve_engine_root(project["workspace"].get("engine_root"))
    config_path = build_engine_config(project, overrides={
        "preview": {
            "enabled": False,
        }
    })

    validate_script = engine_root / "scripts" / "validate_pipeline.py"
    render_final_script = engine_root / "scripts" / "render_final.py"
    manifest_path = Path(project["export"]["output_dir"]) / "data" / "manifest.json"
    validate_log_path = _log_path(project, "engine_render_validate")
    render_log_path = _log_path(project, "engine_render_final")

    validate_cmd = [
        sys.executable,
        str(validate_script),
        "--root",
        str(engine_root),
        "--config",
        str(config_path),
    ]

    validate_code = _run_logged(
        validate_cmd,
        cwd=engine_root,
        log_path=validate_log_path,
        quiet=quiet,
        label="final render validation",
    )
    _remember_log(project, "engine_render_validate", validate_log_path)
    if validate_code != 0:
        if quiet:
            print(f"final render validation finished with exit code {validate_code}. Log: {validate_log_path}")
        return validate_code

    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found after validation: {manifest_path}")

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
    code = _run_logged(cmd=render_cmd, cwd=engine_root, log_path=render_log_path, quiet=quiet, label="final render")
    _remember_log(project, "engine_render_final", render_log_path)
    if quiet:
        print(f"final render finished with exit code {code}. Log: {render_log_path}")
    return code


