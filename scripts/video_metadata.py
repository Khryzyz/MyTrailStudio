import json
import os
import subprocess
from datetime import timedelta

from utils import parse_dt


def ffprobe_video(video_path):
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries",
        "format=duration:format_tags=creation_time:stream=width,height:stream_tags=creation_time",
        "-of", "json",
        video_path
    ]

    raw = subprocess.check_output(cmd, text=True, encoding="utf-8", errors="ignore")
    data = json.loads(raw)

    duration = float(data.get("format", {}).get("duration", 0))

    creation_time = None
    fmt_tags = data.get("format", {}).get("tags", {})
    creation_time = fmt_tags.get("creation_time")

    width = None
    height = None

    for stream in data.get("streams", []):
        if stream.get("width") and stream.get("height") and width is None:
            width = int(stream.get("width"))
            height = int(stream.get("height"))

        if not creation_time:
            tags = stream.get("tags", {})
            if tags.get("creation_time"):
                creation_time = tags.get("creation_time")

    start = parse_dt(creation_time)
    end = start + timedelta(seconds=duration) if start else None

    return {
        "path": video_path,
        "name": os.path.basename(video_path),
        "duration_seconds": duration,
        "start": start,
        "end": end,
        "creation_time_raw": creation_time,
        "width": width,
        "height": height
    }


def analyze_video(video, gpx, input_hyperlapse_speed):
    if not video["start"]:
        return {
            "status": "SIN_HORA_VIDEO",
            "real_duration_seconds": None,
            "real_end": None,
            "overlap_seconds": 0,
            "missing_before_seconds": None,
            "missing_after_seconds": None
        }

    real_duration = video["duration_seconds"] * input_hyperlapse_speed

    v_start = video["start"]
    v_end = v_start + timedelta(seconds=real_duration)
    g_start = gpx["start"]
    g_end = gpx["end"]

    overlap_start = max(v_start, g_start)
    overlap_end = min(v_end, g_end)
    overlap_seconds = max(0, (overlap_end - overlap_start).total_seconds())

    missing_before = max(0, (g_start - v_start).total_seconds())
    missing_after = max(0, (v_end - g_end).total_seconds())

    if overlap_seconds <= 0:
        status = "FUERA_DEL_GPX"
    elif missing_before > 0 or missing_after > 0:
        status = "GPX_PARCIAL"
    else:
        status = "OK"

    return {
        "status": status,
        "real_duration_seconds": round(real_duration, 2),
        "real_end": v_end,
        "overlap_seconds": round(overlap_seconds, 2),
        "missing_before_seconds": round(missing_before, 2),
        "missing_after_seconds": round(missing_after, 2)
    }
