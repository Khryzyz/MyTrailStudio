from __future__ import annotations

from datetime import datetime
from typing import Any


def parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value)


def overlaps(a_start: datetime, a_end: datetime, b_start: datetime, b_end: datetime) -> bool:
    return a_start < b_end and b_start < a_end


def build_timelines(videos: list[dict[str, Any]]) -> list[dict[str, Any]]:
    candidates = []
    for video in videos:
        start = parse_iso(video.get("real_start_utc") or video.get("creation_time_utc"))
        end = parse_iso(video.get("real_end_utc"))
        if not start or not end:
            continue
        candidates.append((start, end, video))

    candidates.sort(key=lambda item: (item[0], item[2]["name"].lower()))
    timelines: list[dict[str, Any]] = []

    for start, end, video in candidates:
        placed = False
        item = {
            "video_id": video["id"],
            "name": video["name"],
            "start_utc": start.isoformat(),
            "end_utc": end.isoformat(),
            "gpx_status": video.get("gpx_status"),
        }

        for timeline in timelines:
            has_overlap = any(
                overlaps(
                    start,
                    end,
                    parse_iso(existing["start_utc"]),
                    parse_iso(existing["end_utc"]),
                )
                for existing in timeline["items"]
            )
            if not has_overlap:
                timeline["items"].append(item)
                video["timeline_id"] = timeline["id"]
                placed = True
                break

        if not placed:
            timeline_id = len(timelines) + 1
            video["timeline_id"] = timeline_id
            timelines.append({
                "id": timeline_id,
                "priority": timeline_id,
                "items": [item],
            })

    return timelines


def summarize_timeline_gaps(project: dict[str, Any]) -> list[dict[str, Any]]:
    gpx_start = parse_iso(project["gpx_summary"].get("start_utc"))
    gpx_end = parse_iso(project["gpx_summary"].get("end_utc"))
    if not gpx_start or not gpx_end:
        return []

    gaps = []
    for timeline in project.get("timelines", []):
        cursor = gpx_start
        items = sorted(timeline["items"], key=lambda item: item["start_utc"])
        for item in items:
            item_start = parse_iso(item["start_utc"])
            item_end = parse_iso(item["end_utc"])
            if item_start and item_start > cursor:
                gaps.append({
                    "timeline_id": timeline["id"],
                    "start_utc": cursor.isoformat(),
                    "end_utc": min(item_start, gpx_end).isoformat(),
                    "seconds": round((min(item_start, gpx_end) - cursor).total_seconds(), 2),
                })
            if item_end and item_end > cursor:
                cursor = item_end
        if cursor < gpx_end:
            gaps.append({
                "timeline_id": timeline["id"],
                "start_utc": cursor.isoformat(),
                "end_utc": gpx_end.isoformat(),
                "seconds": round((gpx_end - cursor).total_seconds(), 2),
            })
    return [gap for gap in gaps if gap["seconds"] > 0]

