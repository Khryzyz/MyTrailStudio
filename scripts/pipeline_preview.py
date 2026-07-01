import json
import os
import shutil
import subprocess
from datetime import timedelta, timezone

from gpx_io import enrich_points, read_gpx_points, sample_at
from overlay_renderer import build_overlay_context, render_closing_frame, render_overlay_frame
from utils import load_font, parse_dt

def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    args = parser.parse_args()

    root = args.root
    manifest_path = os.path.join(root, "output", "data", "manifest.json")

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
    total_frames = preview_time * overlay_fps
    animated_frames = animated_seconds * overlay_fps

    input_speed = float(config["input"]["hyperlapse_speed"])

    video = manifest["videos"][0]
    video_path = video["path"]
    video_name = os.path.splitext(video["name"])[0]

    W = int(video["width"])
    H = int(video["height"])

    gpx_path = manifest["gpx"]["path"]
    gpx_points = enrich_points(read_gpx_points(gpx_path))

    route_name = config["input"]["route_name"] or os.path.splitext(manifest["gpx"]["name"])[0]

    font_path = os.path.join(root, config["setting"]["layout"]["font_path"])
    frames_dir = os.path.join(root, "output", "frames", f"preview_{video_name}")
    preview_out = os.path.join(root, "output", "previews", f"{video_name}_preview.mp4")

    if os.path.exists(frames_dir):
        shutil.rmtree(frames_dir)
    os.makedirs(frames_dir, exist_ok=True)

    max_alt = max(p["ele"] for p in gpx_points)
    max_dist = max(p["dist_m"] for p in gpx_points)

    stats = {
        "dist_km": max_dist / 1000,
        "max_alt": max_alt,
        "duration_text": str(parse_dt(manifest["gpx"]["end_utc"]) - parse_dt(manifest["gpx"]["start_utc"])),
        "date_text": parse_dt(manifest["gpx"]["start_utc"]).astimezone(timezone(timedelta(hours=-5))).strftime("%d/%m/%Y")
    }

    overlay_context = build_overlay_context(W, H, gpx_points, font_path)
    video_start = parse_dt(video["start_utc"])

    print("")
    print("Generando preview...")
    print("Frames:", total_frames)
    print("Carpeta:", frames_dir)
    print("Salida:", preview_out)
    print("")

    for frame in range(total_frames):
        if frame < animated_frames:
            video_sec = frame / overlay_fps
            real_sec = video_sec * input_speed
            current_time = video_start + timedelta(seconds=real_sec)
            current = sample_at(gpx_points, current_time)
            img = render_overlay_frame(W, H, config, gpx_points, current_time, current, frame, overlay_context)
        else:
            img = render_closing_frame(W, H, config, route_name, stats, font_path)

        out = os.path.join(frames_dir, f"frame_{frame:05d}.png")
        img.save(out)

        if frame % overlay_fps == 0 or frame == total_frames - 1:
            pct = ((frame + 1) / total_frames) * 100
            print(f"\rFrames preview: {frame + 1}/{total_frames} ({pct:.1f}%)", end="")

    print("")
    print("Frames preview creados.")

    target_resolution = config["output"]["resolution"]
    target_scale = {
        "1080p": "1920:1080",
        "2k": "2560:1440",
        "4k": "3840:2160"
    }[target_resolution]

    ffmpeg_cmd = [
        "ffmpeg", "-y",
        "-t", str(animated_seconds),
        "-i", video_path,
        "-framerate", str(overlay_fps),
        "-i", os.path.join(frames_dir, "frame_%05d.png"),
        "-filter_complex", f"[0:v][1:v]overlay=0:0:shortest=0,scale={target_scale},fps={config['output']['fps']}",
        "-an",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-crf", "20",
        "-preset", "medium",
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
