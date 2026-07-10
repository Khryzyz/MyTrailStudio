import json
import os
import subprocess
from datetime import datetime, timedelta, timezone

from pipeline_utils import parse_dt


VIDEO_EXTENSIONS = (".mp4", ".mov")
DERIVED_NAME_MARKERS = (
    "_overlay",
    "_preview",
    "_final",
    "_fixdate",
    "_corte",
    "_temp",
    "_sin_fecha",
)


def is_supported_video(path):
    return os.path.splitext(path)[1].lower() in VIDEO_EXTENSIONS


def is_derived_video_name(path):
    name = os.path.basename(path).lower()
    return any(marker in name for marker in DERIVED_NAME_MARKERS)


def list_video_files(videos_dir):
    return sorted([
        os.path.join(videos_dir, f)
        for f in os.listdir(videos_dir)
        if is_supported_video(f) and not is_derived_video_name(f)
    ])


def parse_rate(value):
    if not value or value == "0/0":
        return None

    try:
        if "/" in value:
            num, den = value.split("/", 1)
            den_value = float(den)
            if den_value == 0:
                return None
            return float(num) / den_value
        return float(value)
    except Exception:
        return None


def sort_videos_by_start(videos):
    missing = [v["name"] for v in videos if not v["start"]]
    if missing:
        names = ", ".join(missing)
        raise Exception(f"Falta creation_time valido para: {names}. Agrega metadata ffprobe valida o video_overrides en la configuracion.")

    invalid = [
        f'{v["name"]} (creation_time={v["creation_time_raw"]})'
        for v in videos
        if not v["start"]
    ]
    if invalid:
        names = ", ".join(invalid)
        raise Exception(f"No se pudo parsear creation_time con ffprobe para: {names}. No se usara fecha de modificacion.")

    return sorted(videos, key=lambda v: (v["start"], v["name"].lower()))


def ffprobe_video(video_path):
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries",
        "format=duration:format_tags=creation_time:stream=codec_type,width,height,r_frame_rate,avg_frame_rate:stream_tags=creation_time",
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
    fps = None
    fps_raw = None

    for stream in data.get("streams", []):
        if stream.get("codec_type") == "video" and stream.get("width") and stream.get("height") and width is None:
            width = int(stream.get("width"))
            height = int(stream.get("height"))
            fps_raw = stream.get("avg_frame_rate") or stream.get("r_frame_rate")
            fps = parse_rate(fps_raw)

        if not creation_time:
            tags = stream.get("tags", {})
            if tags.get("creation_time"):
                creation_time = tags.get("creation_time")

    start = parse_dt(creation_time)
    start_source = "ffprobe" if start else "unknown"
    creation_time_used = creation_time

    if not start:
        try:
            file_created = datetime.fromtimestamp(os.path.getctime(video_path), timezone.utc)
            start = file_created
            start_source = "filesystem_created"
            creation_time_used = file_created.isoformat()
        except Exception:
            pass

    end = start + timedelta(seconds=duration) if start else None

    return {
        "path": os.path.abspath(video_path),
        "name": os.path.basename(video_path),
        "duration_seconds": duration,
        "start": start,
        "end": end,
        "creation_time_raw": creation_time,
        "creation_time_used": creation_time_used,
        "width": width,
        "height": height,
        "fps": fps,
        "fps_raw": fps_raw,
        "start_source": start_source
    }


def apply_creation_time_override(video, override_creation_time):
    if video["start"]:
        return video

    override_start = parse_dt(override_creation_time)
    if not override_start:
        raise Exception(f"Override creation_time invalido para {video['name']}: {override_creation_time}")

    video = dict(video)
    video["start"] = override_start
    video["end"] = override_start + timedelta(seconds=video["duration_seconds"])
    video["creation_time_used"] = override_creation_time
    video["start_source"] = "override"
    return video


def analyze_video(video, gpx, input_video_mode, input_hyperlapse_speed):
    if not video["start"]:
        return {
            "status": "SIN_HORA_VIDEO",
            "real_duration_seconds": None,
            "real_end": None,
            "overlap_seconds": 0,
            "missing_before_seconds": None,
            "missing_after_seconds": None
        }

    if input_video_mode == "hyperlapse":
        real_duration = video["duration_seconds"] * input_hyperlapse_speed
    else:
        real_duration = video["duration_seconds"]

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
