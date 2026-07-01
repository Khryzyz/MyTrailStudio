import json
import math
import os
import shutil
from datetime import timedelta

from ffmpeg_render import concat_videos, create_closing_clip, render_video_clip
from gpx_io import enrich_points, read_gpx_points, sample_at
from overlay_renderer import build_overlay_context, render_overlay_frame
from utils import parse_dt, safe_name

def render_overlay_frames(root, manifest, video, gpx_points, frames_dir):
    config = manifest["config"]

    overlay_fps = int(config["setting"]["layout"]["overlay_fps"])
    input_speed = float(config["input"]["hyperlapse_speed"])

    W = int(video["width"])
    H = int(video["height"])

    duration_seconds = float(video["duration_seconds"])
    total_frames = math.ceil(duration_seconds * overlay_fps)

    video_start = parse_dt(video["start_utc"])

    font_path = manifest["resolved_paths"]["font_path"]
    overlay_context = build_overlay_context(W, H, gpx_points, font_path)

    if os.path.exists(frames_dir):
        shutil.rmtree(frames_dir)
    os.makedirs(frames_dir, exist_ok=True)

    print("")
    print("Generando frames del overlay final...")
    print("Video:", video["name"])
    print("Frames:", total_frames)
    print("Carpeta:", frames_dir)
    print("")

    for frame in range(total_frames):
        video_sec = frame / overlay_fps
        real_sec = video_sec * input_speed
        current_time = video_start + timedelta(seconds=real_sec)
        current = sample_at(gpx_points, current_time)
        img = render_overlay_frame(W, H, config, gpx_points, current_time, current, frame, overlay_context)

        out = os.path.join(frames_dir, f"frame_{frame:05d}.png")
        img.save(out)

        if frame % overlay_fps == 0 or frame == total_frames - 1:
            pct = ((frame + 1) / total_frames) * 100
            print(f"\rFrames: {frame + 1}/{total_frames} ({pct:.1f}%)", end="")

    print("")
    return total_frames

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

    if config["output"]["preview"]["add"]:
        print("Preview activado. No se genera render final.")
        return

    gpx_points = enrich_points(read_gpx_points(manifest["gpx"]["path"]))

    final_dir = os.path.join(root, "output", "final")
    frames_base = os.path.join(root, "output", "frames")
    temp_dir = os.path.join(root, "temp")

    os.makedirs(final_dir, exist_ok=True)
    os.makedirs(frames_base, exist_ok=True)
    os.makedirs(temp_dir, exist_ok=True)

    rendered_clips = []

    for idx, video in enumerate(manifest["videos"], start=1):
        video_base = safe_name(os.path.splitext(video["name"])[0])
        frames_dir = os.path.join(frames_base, f"final_{video_base}")
        clip_path = os.path.join(temp_dir, f"clip_{idx:03d}_{video_base}.mp4")

        render_overlay_frames(root, manifest, video, gpx_points, frames_dir)
        render_video_clip(manifest, video, frames_dir, clip_path)

        rendered_clips.append(clip_path)

        if not config["setting"]["layout"]["keep_temp_frames"]:
            shutil.rmtree(frames_dir, ignore_errors=True)

    closing_clip = None

    if config["output"]["closing_screen"]["add"]:
        closing_clip = os.path.join(temp_dir, "clip_999_closing_screen.mp4")
        create_closing_clip(root, manifest, gpx_points, closing_clip)
        rendered_clips.append(closing_clip)

    route_name = config["input"]["route_name"] or os.path.splitext(manifest["gpx"]["name"])[0]
    out_name = safe_name(route_name)
    speed_txt = str(config["output"]["hyperlapse_speed"]).replace(".", "p")
    resolution = config["output"]["resolution"]

    if config["output"]["single_final_video"]:
        final_path = os.path.join(final_dir, f"{out_name}_overlay_hyperlapse_{speed_txt}x_{resolution}.mp4")
        concat_videos(rendered_clips, final_path)
    else:
        for clip in rendered_clips:
            if "closing" not in clip:
                shutil.copy2(clip, final_dir)
        final_path = final_dir

    print("")
    print("Render final completado:")
    print(final_path)

if __name__ == "__main__":
    main()
