import json
import math
import os
import shutil
import subprocess
from datetime import timedelta, timezone

from ffmpeg_renderer import ffmpeg_threads
from frame_renderer import render_frames_parallel
from gpx_track import enrich_points, read_gpx_points
from pipeline_utils import ffmpeg_output_speed_factor, parse_dt

def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    parser.add_argument("--manifest")
    args = parser.parse_args()

    root = args.root
    manifest_path = args.manifest or os.path.join(root, "output", "data", "manifest.json")

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    config = manifest["config"]

    if not config["output"]["preview"]["add"]:
        print("Preview desactivado. No se genera preview.")
        return

    preview_time = int(config["output"]["preview"]["time"])
    if preview_time < 1 or preview_time > 60:
        raise Exception("La preview debe estar entre 1 y 60 segundos.")

    overlay_fps = int(config["setting"]["layout"]["overlay_fps"])
    closing_add = bool(config["output"]["closing_screen"]["add"])
    closing_seconds = int(config["output"]["closing_screen"]["time"]) if closing_add else 0
    closing_seconds = min(closing_seconds, preview_time)

    animated_seconds = preview_time - closing_seconds

    input_speed = float(config["input"]["hyperlapse_speed"]) if config["input"]["video_mode"] == "hyperlapse" else 1.0
    output_speed_factor = ffmpeg_output_speed_factor(config)

    video = manifest["videos"][0]
    video_path = video["path"]
    video_name = os.path.splitext(video["name"])[0]

    W = int(video["width"])
    H = int(video["height"])

    gpx_path = manifest["gpx"]["path"]
    gpx_points = enrich_points(read_gpx_points(gpx_path))

    route_name = config["input"]["route_name"] or os.path.splitext(manifest["gpx"]["name"])[0]

    output_dir = manifest["resolved_paths"]["output_dir"]
    font_path = manifest["resolved_paths"]["font_path"]
    frames_dir = os.path.join(output_dir, "frames", f"preview_{video_name}")
    preview_out = os.path.join(output_dir, "previews", f"{video_name}_preview.mp4")

    if os.path.exists(frames_dir):
        shutil.rmtree(frames_dir)
    os.makedirs(frames_dir, exist_ok=True)
    os.makedirs(os.path.dirname(preview_out), exist_ok=True)

    max_alt = max(p["ele"] for p in gpx_points)
    max_dist = max(p["dist_m"] for p in gpx_points)

    stats = {
        "dist_km": max_dist / 1000,
        "max_alt": max_alt,
        "duration_text": str(parse_dt(manifest["gpx"]["end_utc"]) - parse_dt(manifest["gpx"]["start_utc"])),
        "date_text": parse_dt(manifest["gpx"]["start_utc"]).astimezone(timezone(timedelta(hours=-5))).strftime("%d/%m/%Y")
    }

    video_start = parse_dt(video["start_utc"])
    source_seconds = min(float(video["duration_seconds"]), animated_seconds * output_speed_factor)
    if output_speed_factor > 0:
        animated_seconds = source_seconds / output_speed_factor
    animated_frames = math.ceil(animated_seconds * overlay_fps)
    closing_frames = closing_seconds * overlay_fps
    total_frames = animated_frames + closing_frames

    print("")
    print("Generando preview...")
    print("Frames:", total_frames)
    print("Velocidad final deseada:", config["output"]["hyperlapse_speed"], "x")
    print("Factor tecnico FFmpeg:", round(output_speed_factor, 6), "x")
    print("Carpeta:", frames_dir)
    print("Salida:", preview_out)
    print("")

    frame_tasks = []
    for frame in range(total_frames):
        out = os.path.join(frames_dir, f"frame_{frame:05d}.png")

        if frame < animated_frames:
            output_sec = frame / overlay_fps
            video_sec = output_sec * output_speed_factor
            real_sec = video_sec * input_speed
            current_time = video_start + timedelta(seconds=real_sec)
            frame_tasks.append((frame, "overlay", current_time, out))
        else:
            frame_tasks.append((frame, "closing", None, out))

    render_frames_parallel(W, H, config, gpx_points, font_path, frame_tasks, "Frames preview", route_name, stats)
    print("Frames preview creados.")

    target_resolution = config["output"]["resolution"]
    target_scale = {
        "1080p": "1920:1080",
        "2k": "2560:1440",
        "4k": "3840:2160"
    }[target_resolution]

    ffmpeg_cmd = [
        "ffmpeg", "-y",
        "-t", str(source_seconds),
        "-i", video_path,
        "-framerate", str(overlay_fps),
        "-i", os.path.join(frames_dir, "frame_%05d.png"),
        "-filter_complex", f"[0:v]setpts=PTS/{output_speed_factor}[base];[base][1:v]overlay=0:0:shortest=0,scale={target_scale},fps={config['output']['fps']}",
        "-an",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-crf", "20",
        "-preset", "medium",
        "-threads", str(ffmpeg_threads(config)),
        preview_out
    ]

    print("")
    print("Generando MP4 preview...")
    subprocess.run(ffmpeg_cmd, check=True)

    print("")
    print("Preview creado:")
    print(preview_out)

if __name__ == "__main__":
    main()
