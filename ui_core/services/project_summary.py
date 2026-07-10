from __future__ import annotations

from pathlib import Path
from typing import Any


def seconds_to_hms(seconds: float | int | None) -> str:
    if seconds is None:
        return "N/D"
    seconds = int(round(float(seconds)))
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def existing_preview_files(project: dict[str, Any]) -> list[str]:
    previews_dir = Path(project["export"]["output_dir"]) / "previews"
    if not previews_dir.is_dir():
        return []
    return [str(path) for path in sorted(previews_dir.glob("*.mp4"))]


def build_project_summary(project: dict[str, Any]) -> dict[str, Any]:
    videos = project.get("assets", {}).get("videos", [])
    timelines = project.get("timelines", [])
    validation = project.get("engine", {}).get("last_validation") or {}
    manifest_path = project.get("engine", {}).get("last_manifest_path")

    statuses: dict[str, int] = {}
    for video in videos:
        status = video.get("gpx_status", "unknown")
        statuses[status] = statuses.get(status, 0) + 1

    total_file_seconds = sum(float(video.get("duration_file_seconds") or 0) for video in videos)
    total_real_seconds = sum(float(video.get("duration_real_seconds") or 0) for video in videos)

    return {
        "project": {
            "id": project["project"]["id"],
            "name": project["project"]["name"],
            "updated_at_utc": project["project"].get("updated_at_utc"),
            "timezone": project["project"].get("timezone"),
        },
        "gpx": project.get("gpx_summary", {}),
        "videos": {
            "count": len(videos),
            "statuses": statuses,
            "total_file_seconds": round(total_file_seconds, 2),
            "total_real_seconds": round(total_real_seconds, 2),
            "items": [
                {
                    "name": video["name"],
                    "mode": video.get("mode"),
                    "start_utc": video.get("creation_time_effective_utc") or video.get("creation_time_utc"),
                    "real_end_utc": video.get("real_end_utc"),
                    "duration_file_seconds": video.get("duration_file_seconds"),
                    "duration_real_seconds": video.get("duration_real_seconds"),
                    "gpx_status": video.get("gpx_status"),
                    "timeline_id": video.get("timeline_id"),
                }
                for video in videos
            ],
        },
        "timelines": {
            "count": len(timelines),
            "items": timelines,
        },
        "gaps": validation.get("gaps", []),
        "warnings": validation.get("warnings", []),
        "errors": validation.get("errors", []),
        "engine": {
            "generated_config_path": project.get("engine", {}).get("generated_config_path"),
            "last_manifest_path": manifest_path,
            "manifest_exists": bool(manifest_path and Path(manifest_path).is_file()),
            "previews": existing_preview_files(project),
        },
        "export": project.get("export", {}),
        "duration_text": {
            "gpx": seconds_to_hms(project.get("gpx_summary", {}).get("duration_seconds")),
            "videos_file": seconds_to_hms(total_file_seconds),
            "videos_real": seconds_to_hms(total_real_seconds),
        },
    }

