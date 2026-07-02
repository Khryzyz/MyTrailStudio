import os
import subprocess
from datetime import timedelta, timezone

from overlay_renderer import render_closing_frame
from utils import parse_dt


RESOLUTION_SCALE = {
    "1080p": "1920:1080",
    "2k": "2560:1440",
    "4k": "3840:2160"
}


def ffmpeg_threads(config):
    threads = int(config["setting"]["performance"].get("ffmpeg_threads", 0))
    return max(0, threads)


def render_video_clip(
    manifest,
    video,
    frames_dir,
    out_path,
    transition_enabled=False,
    transition_time=0.5,
    is_first_clip=True,
    is_last_clip=True
):
    config = manifest["config"]

    overlay_fps = int(config["setting"]["layout"]["overlay_fps"])
    output_fps = int(config["output"]["fps"])
    output_speed = float(config["output"]["hyperlapse_speed"])
    resolution = config["output"]["resolution"]
    remove_audio = bool(config["output"]["remove_audio"])
    threads = ffmpeg_threads(config)

    scale = RESOLUTION_SCALE[resolution]

    if not remove_audio and output_speed != 1.0:
        print("ADVERTENCIA: remove_audio=false con hyperlapse_speed distinto de 1 no se soporta aun. Se exportara sin audio.")
        remove_audio = True

    filters = [
        "overlay=0:0:shortest=1",
        f"setpts=PTS/{output_speed}",
        f"scale={scale}",
        f"fps={output_fps}"
    ]

    if transition_enabled:
        output_duration = float(video["duration_seconds"]) / output_speed
        fade_time = min(float(transition_time), output_duration)

        if not is_first_clip:
            filters.append(f"fade=t=in:st=0:d={fade_time}")

        if not is_last_clip:
            fade_out_start = max(0, output_duration - fade_time)
            filters.append(f"fade=t=out:st={fade_out_start}:d={fade_time}")

    filter_complex = f"[0:v][1:v]{','.join(filters)}[v]"

    cmd = [
        "ffmpeg", "-y",
        "-i", video["path"],
        "-framerate", str(overlay_fps),
        "-start_number", "0",
        "-i", os.path.join(frames_dir, "frame_%05d.png"),
        "-filter_complex", filter_complex,
        "-map", "[v]"
    ]

    if remove_audio:
        cmd += ["-an"]
    else:
        cmd += ["-map", "0:a?", "-c:a", "copy"]

    cmd += [
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-crf", "20",
        "-preset", "medium",
        "-threads", str(threads),
        out_path
    ]

    print("")
    print("Renderizando clip:")
    print(out_path)
    subprocess.run(cmd, check=True)


def create_closing_clip(root, manifest, gpx_points, out_path):
    config = manifest["config"]

    if not config["output"]["closing_screen"]["add"]:
        return None

    first_video = manifest["videos"][0]
    W = int(first_video["width"])
    H = int(first_video["height"])

    route_name = config["input"]["route_name"] or os.path.splitext(manifest["gpx"]["name"])[0]
    font_path = manifest["resolved_paths"]["font_path"]

    max_dist = max(p["dist_m"] for p in gpx_points)
    max_alt = max(p["ele"] for p in gpx_points)

    gpx_start = parse_dt(manifest["gpx"]["start_utc"])
    gpx_end = parse_dt(manifest["gpx"]["end_utc"])

    stats = {
        "dist_km": max_dist / 1000,
        "max_alt": max_alt,
        "duration_text": str(gpx_end - gpx_start),
        "date_text": gpx_start.astimezone(timezone(timedelta(hours=-5))).strftime("%d/%m/%Y")
    }

    img = render_closing_frame(W, H, config, route_name, stats, font_path)

    temp_dir = os.path.join(root, "temp")
    closing_png = os.path.join(temp_dir, "closing_screen.png")
    img.save(closing_png)

    seconds = int(config["output"]["closing_screen"]["time"])
    fps = int(config["output"]["fps"])
    scale = RESOLUTION_SCALE[config["output"]["resolution"]]
    threads = ffmpeg_threads(config)

    cmd = [
        "ffmpeg", "-y",
        "-loop", "1",
        "-t", str(seconds),
        "-i", closing_png,
        "-vf", f"scale={scale},fps={fps}",
        "-an",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-crf", "20",
        "-preset", "medium",
        "-threads", str(threads),
        out_path
    ]

    print("")
    print("Creando pantalla final:")
    print(out_path)
    subprocess.run(cmd, check=True)

    return out_path


def concat_videos(paths, output_path):
    list_path = os.path.join(os.path.dirname(output_path), "concat_list.txt")

    with open(list_path, "w", encoding="utf-8") as f:
        for p in paths:
            safe_path = p.replace("\\", "/")
            f.write(f"file '{safe_path}'\n")

    cmd = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", list_path,
        "-c", "copy",
        output_path
    ]

    print("")
    print("Uniendo clips:")
    print(output_path)
    subprocess.run(cmd, check=True)
