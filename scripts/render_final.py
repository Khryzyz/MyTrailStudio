import json
import math
import os
import shutil
from datetime import timedelta

from cleanup_pipeline import cleanup_auto_after_render
from ffmpeg_renderer import concat_videos, create_closing_clip, render_video_clip
from frame_renderer import render_frames_parallel
from gpx_track import enrich_points, read_gpx_points
from pipeline_utils import parse_dt, safe_name

def artifact_exists(path):
    return os.path.exists(path) and os.path.getsize(path) > 0


def render_overlay_frames(root, manifest, video, gpx_points, frames_dir):
    config = manifest["config"]
    resume = bool(config["output"].get("resume", True))

    overlay_fps = int(config["setting"]["layout"]["overlay_fps"])
    input_speed = float(config["input"]["hyperlapse_speed"])

    W = int(video["width"])
    H = int(video["height"])

    duration_seconds = float(video["duration_seconds"])
    total_frames = math.ceil(duration_seconds * overlay_fps)

    video_start = parse_dt(video["start_utc"])

    font_path = manifest["resolved_paths"]["font_path"]

    if os.path.exists(frames_dir) and not resume:
        shutil.rmtree(frames_dir)
    os.makedirs(frames_dir, exist_ok=True)

    print("")
    print("Generando frames del overlay final...")
    print("Video:", video["name"])
    print("Frames:", total_frames)
    print("Carpeta:", frames_dir)
    print("")

    frame_tasks = []
    for frame in range(total_frames):
        video_sec = frame / overlay_fps
        real_sec = video_sec * input_speed
        current_time = video_start + timedelta(seconds=real_sec)
        out = os.path.join(frames_dir, f"frame_{frame:05d}.png")
        frame_tasks.append((frame, "overlay", current_time, out))

    render_frames_parallel(W, H, config, gpx_points, font_path, frame_tasks, "Frames", resume=resume)
    return total_frames

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
    resume = bool(config["output"].get("resume", True))

    if config["output"]["preview"]["add"]:
        print("Preview activado. No se genera render final.")
        return

    gpx_points = enrich_points(read_gpx_points(manifest["gpx"]["path"]))

    output_dir = manifest["resolved_paths"]["output_dir"]
    final_dir = os.path.join(output_dir, "final")
    frames_base = os.path.join(output_dir, "frames")
    temp_dir = os.path.join(root, "temp")

    os.makedirs(final_dir, exist_ok=True)
    os.makedirs(frames_base, exist_ok=True)
    os.makedirs(temp_dir, exist_ok=True)

    rendered_clips = []
    videos = manifest["videos"]
    transition = config["output"].get("transition", {})
    transition_enabled = (
        bool(transition.get("add"))
        and transition.get("type") == "fade_black"
        and len(videos) > 1
        and bool(config["output"]["single_final_video"])
    )
    transition_time = float(transition.get("time", 0.5))

    for idx, video in enumerate(videos, start=1):
        video_base = safe_name(os.path.splitext(video["name"])[0])
        frames_dir = os.path.join(frames_base, f"final_{video_base}")
        clip_path = os.path.join(temp_dir, f"clip_{idx:03d}_{video_base}.mp4")

        if resume and artifact_exists(clip_path):
            print("")
            print("Clip existente reutilizado:")
            print(clip_path)
        else:
            render_overlay_frames(root, manifest, video, gpx_points, frames_dir)
            render_video_clip(
                manifest,
                video,
                frames_dir,
                clip_path,
                transition_enabled=transition_enabled,
                transition_time=transition_time,
                is_first_clip=idx == 1,
                is_last_clip=idx == len(videos)
            )

        rendered_clips.append(clip_path)

        if not config["setting"]["layout"]["keep_temp_frames"]:
            shutil.rmtree(frames_dir, ignore_errors=True)

    closing_clip = None

    if config["output"]["closing_screen"]["add"]:
        closing_clip = os.path.join(temp_dir, "clip_999_closing_screen.mp4")
        if resume and artifact_exists(closing_clip):
            print("")
            print("Pantalla final existente reutilizada:")
            print(closing_clip)
        else:
            create_closing_clip(root, manifest, gpx_points, closing_clip)
        rendered_clips.append(closing_clip)

    route_name = config["input"]["route_name"] or os.path.splitext(manifest["gpx"]["name"])[0]
    out_name = safe_name(route_name)
    speed_txt = str(config["output"]["hyperlapse_speed"]).replace(".", "p")
    resolution = config["output"]["resolution"]

    if config["output"]["single_final_video"]:
        final_path = os.path.join(final_dir, f"{out_name}_overlay_hyperlapse_{speed_txt}x_{resolution}.mp4")
        if resume and artifact_exists(final_path):
            print("")
            print("Video final existente reutilizado:")
            print(final_path)
        else:
            concat_videos(rendered_clips, final_path)
    else:
        for clip in rendered_clips:
            if "closing" not in clip:
                dest = os.path.join(final_dir, os.path.basename(clip))
                if resume and artifact_exists(dest):
                    print("")
                    print("Archivo final existente reutilizado:")
                    print(dest)
                else:
                    shutil.copy2(clip, final_dir)
        final_path = final_dir

    print("")
    print("Render final completado:")
    print(final_path)

    if config["output"].get("cleanup_after_render", True):
        cleanup_auto_after_render(root)

if __name__ == "__main__":
    main()
