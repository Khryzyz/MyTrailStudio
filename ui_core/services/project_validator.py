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
    seen_paths: dict[str, str] = {}
    seen_names: dict[str, int] = {}

    if not videos:
        warnings.append("The project has no videos.")

    gpx_path = Path(project["assets"]["gpx"]["path"])
    output_dir = Path(project["export"]["output_dir"])
    if not gpx_path.is_file():
        errors.append(f"GPX file does not exist: {gpx_path}")
    if not output_dir.exists():
        warnings.append(f"Output folder does not exist yet and will be created by the engine: {output_dir}")

    for video in videos:
        video_path = Path(video["path"])
        resolved_path = str(video_path.resolve()) if video_path.exists() else str(video_path)
        seen_names[video["name"].lower()] = seen_names.get(video["name"].lower(), 0) + 1
        if resolved_path in seen_paths:
            errors.append(f"{video['name']}: duplicates video path already used by {seen_paths[resolved_path]}.")
        else:
            seen_paths[resolved_path] = video["name"]
        if not video_path.is_file():
            errors.append(f"{video['name']}: video file does not exist: {video_path}")

        manual_start = parse_dt(video.get("manual_creation_time_utc"))
        metadata_start = parse_dt(video.get("creation_time_utc"))
        start = manual_start or metadata_start
        start_source = "manual" if manual_start else video.get("creation_time_source", "unknown")

        duration = float(video.get("duration_file_seconds") or 0)
        if duration <= 0:
            errors.append(f"{video['name']}: video duration is not valid.")

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
            warnings.append(f"{video['name']}: has no valid date; manual date/time is required.")
        elif analysis["status"] == "FUERA_DEL_GPX":
            warnings.append(f"{video['name']}: is outside the GPX range.")
        elif analysis["status"] == "GPX_PARCIAL":
            warnings.append(f"{video['name']}: partially covers the GPX range.")

        if start and (start < gpx["start"] - timedelta(days=2) or start > gpx["end"] + timedelta(days=2)):
            warnings.append(f"{video['name']}: date is more than 2 days away from the GPX range.")

    duplicate_names = [name for name, count in seen_names.items() if count > 1]
    for name in duplicate_names:
        warnings.append(f"Duplicate video name detected: {name}")

    modes = {video.get("mode", "normal") for video in videos}
    speeds = {float(video.get("hyperlapse_speed", 2.0)) for video in videos}
    if len(modes) > 1:
        warnings.append("Project mixes normal and hyperlapse videos. Engine config uses the first video mode.")
    if len(speeds) > 1:
        warnings.append("Project mixes input hyperlapse speeds. Engine config uses the first video speed.")

    project["timelines"] = build_timelines(videos)
    gaps = summarize_timeline_gaps(project)
    long_gaps = [gap for gap in gaps if float(gap["seconds"]) >= 60]
    if long_gaps:
        warnings.append(f"Detected {len(long_gaps)} timeline gap(s) of 60 seconds or more.")

    total_overlap_seconds = round(sum(float(video.get("overlap_seconds") or 0) for video in videos), 2)
    gpx_duration_seconds = float(project["gpx_summary"].get("duration_seconds") or 0)
    coverage_percent = round((total_overlap_seconds / gpx_duration_seconds) * 100, 2) if gpx_duration_seconds else 0.0

    report = {
        "project_id": project["project"]["id"],
        "videos": len(videos),
        "timelines": len(project["timelines"]),
        "gaps": gaps,
        "long_gaps": long_gaps,
        "coverage": {
            "overlap_seconds": total_overlap_seconds,
            "gpx_duration_seconds": round(gpx_duration_seconds, 2),
            "percent": coverage_percent,
        },
        "errors": errors,
        "warnings": warnings,
    }

    project["engine"]["last_validation"] = report
    touch_project(project)
    save_project(project)
    return report


