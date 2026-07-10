from __future__ import annotations

import sys
from datetime import timedelta
from pathlib import Path
from typing import Any

from ui_core.models.project_model import touch_project
from ui_core.services.engine_root import resolve_engine_root
from ui_core.services.project_store import save_project
from ui_core.services.timeline_service import build_timelines, summarize_timeline_gaps


def _add_scripts_to_path(engine_root: Path) -> None:
    scripts_dir = str(engine_root / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)


def validate_project(project: dict[str, Any]) -> dict[str, Any]:
    engine_root = resolve_engine_root(project["workspace"].get("engine_root"))
    _add_scripts_to_path(engine_root)
    from pipeline_utils import parse_dt
    from video_metadata import analyze_video

    gpx = {
        "start": parse_dt(project["gpx_summary"]["start_utc"]),
        "end": parse_dt(project["gpx_summary"]["end_utc"]),
    }

    errors = []
    warnings = []
    videos = project["assets"].get("videos", [])

    if not videos:
        warnings.append("El proyecto no tiene videos agregados.")

    for video in videos:
        manual_start = parse_dt(video.get("manual_creation_time_utc"))
        metadata_start = parse_dt(video.get("creation_time_utc"))
        start = manual_start or metadata_start
        start_source = "manual" if manual_start else video.get("creation_time_source", "unknown")

        duration = float(video.get("duration_file_seconds") or 0)
        file_end = start + timedelta(seconds=duration) if start else None
        engine_video = {
            "name": video["name"],
            "start": start,
            "end": file_end,
            "duration_seconds": duration,
        }

        analysis = analyze_video(
            engine_video,
            gpx,
            video.get("mode", "normal"),
            float(video.get("hyperlapse_speed", 2.0)),
        )

        video["creation_time_effective_utc"] = start.isoformat() if start else None
        video["creation_time_effective_source"] = start_source if start else "unknown"
        video["end_file_utc"] = file_end.isoformat() if file_end else None
        video["real_start_utc"] = start.isoformat() if start else None
        video["real_end_utc"] = analysis["real_end"].isoformat() if analysis["real_end"] else None
        video["duration_real_seconds"] = analysis["real_duration_seconds"]
        video["gpx_status"] = analysis["status"]
        video["overlap_seconds"] = analysis["overlap_seconds"]
        video["missing_before_seconds"] = analysis["missing_before_seconds"]
        video["missing_after_seconds"] = analysis["missing_after_seconds"]

        if analysis["status"] == "SIN_HORA_VIDEO":
            warnings.append(f"{video['name']}: no tiene fecha valida; requiere fecha/hora manual.")
        elif analysis["status"] == "FUERA_DEL_GPX":
            warnings.append(f"{video['name']}: queda fuera del rango del GPX.")
        elif analysis["status"] == "GPX_PARCIAL":
            warnings.append(f"{video['name']}: cubre parcialmente el rango del GPX.")

    project["timelines"] = build_timelines(videos)
    gaps = summarize_timeline_gaps(project)

    report = {
        "project_id": project["project"]["id"],
        "videos": len(videos),
        "timelines": len(project["timelines"]),
        "gaps": gaps,
        "errors": errors,
        "warnings": warnings,
    }

    project["engine"]["last_validation"] = report
    touch_project(project)
    save_project(project)
    return report
