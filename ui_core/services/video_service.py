from __future__ import annotations

import sys
from pathlib import Path
from typing import Any
from uuid import uuid4

from ui_core.models.project_model import touch_project
from ui_core.services.engine_root import resolve_engine_root
from ui_core.services.project_store import save_project

VIDEO_EXTENSIONS = {".mp4", ".mov"}


def _add_scripts_to_path(engine_root: Path) -> None:
    scripts_dir = str(engine_root / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)


def add_video(
    project: dict[str, Any],
    video_path: Path,
    *,
    mode: str = "normal",
    hyperlapse_speed: float = 2.0,
) -> dict[str, Any]:
    if mode not in {"normal", "hyperlapse"}:
        raise ValueError("mode debe ser normal o hyperlapse")
    if hyperlapse_speed < 1.0 or hyperlapse_speed > 50.0:
        raise ValueError("hyperlapse_speed debe estar entre 1.0 y 50.0")

    video_path = video_path.resolve()
    if not video_path.is_file():
        raise FileNotFoundError(f"No existe video: {video_path}")

    for existing in project["assets"].get("videos", []):
        if Path(existing["path"]).resolve() == video_path:
            raise ValueError(f"El video ya esta agregado a este proyecto: {existing['name']}")

    engine_root = resolve_engine_root(project["workspace"].get("engine_root"))
    _add_scripts_to_path(engine_root)
    from pipeline_utils import parse_dt
    from video_metadata import analyze_video
    from video_metadata import ffprobe_video

    metadata = ffprobe_video(str(video_path))
    gpx = {
        "start": parse_dt(project["gpx_summary"]["start_utc"]),
        "end": parse_dt(project["gpx_summary"]["end_utc"]),
    }
    engine_video = {
        "name": metadata["name"],
        "start": metadata["start"],
        "end": metadata["end"],
        "duration_seconds": metadata["duration_seconds"],
    }
    analysis = analyze_video(engine_video, gpx, mode, float(hyperlapse_speed))

    video = {
        "id": str(uuid4()),
        "path": metadata["path"],
        "name": metadata["name"],
        "import_mode": "reference",
        "creation_time_utc": metadata["start"].isoformat() if metadata["start"] else None,
        "creation_time_source": metadata["start_source"],
        "manual_creation_time_utc": None,
        "duration_file_seconds": metadata["duration_seconds"],
        "duration_real_seconds": analysis["real_duration_seconds"],
        "width": metadata["width"],
        "height": metadata["height"],
        "fps": metadata["fps"],
        "fps_raw": metadata["fps_raw"],
        "mode": mode,
        "hyperlapse_speed": float(hyperlapse_speed),
        "gpx_status": analysis["status"],
        "real_start_utc": metadata["start"].isoformat() if metadata["start"] else None,
        "real_end_utc": analysis["real_end"].isoformat() if analysis["real_end"] else None,
        "overlap_seconds": analysis["overlap_seconds"],
        "missing_before_seconds": analysis["missing_before_seconds"],
        "missing_after_seconds": analysis["missing_after_seconds"],
        "timeline_id": None,
        "cuts": [],
        "transitions": [],
    }

    project["assets"]["videos"].append(video)
    touch_project(project)
    save_project(project)
    return video


def list_candidate_videos(folder: Path, recursive: bool = False) -> list[Path]:
    if not folder.is_dir():
        raise FileNotFoundError(f"No existe carpeta de videos: {folder}")

    iterator = folder.rglob("*") if recursive else folder.glob("*")
    return sorted(
        [
            path
            for path in iterator
            if path.is_file() and path.suffix.lower() in VIDEO_EXTENSIONS
        ],
        key=lambda path: path.name.lower(),
    )


def add_videos_from_dir(
    project: dict[str, Any],
    folder: Path,
    *,
    mode: str = "normal",
    hyperlapse_speed: float = 2.0,
    recursive: bool = False,
    include_out_of_gpx: bool = False,
) -> dict[str, Any]:
    candidates = list_candidate_videos(folder.resolve(), recursive=recursive)
    added = []
    skipped = []
    failed = []

    for path in candidates:
        try:
            added.append(add_video(
                project,
                path,
                mode=mode,
                hyperlapse_speed=hyperlapse_speed,
            ))
            if added[-1].get("gpx_status") == "FUERA_DEL_GPX" and not include_out_of_gpx:
                removed = remove_video(project, added[-1]["id"])
                added.pop()
                skipped.append({
                    "path": str(path),
                    "reason": f"Fuera del rango GPX: {removed['name']}",
                })
        except ValueError as exc:
            if "ya esta agregado" in str(exc):
                skipped.append({
                    "path": str(path),
                    "reason": str(exc),
                })
            else:
                failed.append({
                    "path": str(path),
                    "error": str(exc),
                })
        except Exception as exc:
            failed.append({
                "path": str(path),
                "error": str(exc),
            })

    statuses: dict[str, int] = {}
    for video in added:
        status = video.get("gpx_status", "unknown")
        statuses[status] = statuses.get(status, 0) + 1

    return {
        "folder": str(folder),
        "recursive": recursive,
        "include_out_of_gpx": include_out_of_gpx,
        "candidates": len(candidates),
        "added": added,
        "skipped": skipped,
        "failed": failed,
        "statuses": statuses,
    }


def remove_video(project: dict[str, Any], video_key: str) -> dict[str, Any]:
    videos = project["assets"].get("videos", [])
    remaining = []
    removed = None

    for video in videos:
        if video["id"] == video_key or video["name"].lower() == video_key.lower():
            removed = video
            continue
        remaining.append(video)

    if not removed:
        raise ValueError(f"No se encontro video por id o nombre: {video_key}")

    project["assets"]["videos"] = remaining
    project["timelines"] = []
    touch_project(project)
    save_project(project)
    return removed
