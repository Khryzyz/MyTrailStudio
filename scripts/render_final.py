import json
import math
import os
import shutil
from datetime import datetime, timedelta, timezone

from cleanup_pipeline import cleanup_auto_after_render
from ffmpeg_renderer import concat_videos, create_closing_clip, render_video_clip
from frame_renderer import render_frames_parallel
from gpx_track import enrich_points, read_gpx_points
from pipeline_utils import parse_dt, safe_name

def artifact_exists(path):
    return os.path.exists(path) and os.path.getsize(path) > 0


def value_token(value):
    return str(value).replace(".", "p").replace("-", "m")


def render_profile_name(config):
    input_mode = config["input"]["video_mode"]
    input_speed = config["input"]["hyperlapse_speed"] if input_mode == "hyperlapse" else 1.0
    output = config["output"]
    transition = output.get("transition", {})

    parts = [
        "in",
        input_mode,
        value_token(input_speed),
        "out",
        value_token(output["hyperlapse_speed"]),
        output["resolution"],
        f"{output['fps']}fps",
        "audiooff" if output["remove_audio"] else "audioon",
        f"overlay{config['setting']['layout']['overlay_fps']}fps",
    ]

    if transition.get("add") and transition.get("type") == "fade_black":
        parts.extend(["fadeblack", value_token(transition.get("time", 0.5))])
    else:
        parts.append("nofade")

    return safe_name("_".join(str(p) for p in parts))


def final_artifact_matches_profile(final_path, final_dir, profile_name):
    report_path = os.path.join(final_dir, "render_report.json")
    if not artifact_exists(final_path) or not artifact_exists(report_path):
        return False

    try:
        with open(report_path, "r", encoding="utf-8") as f:
            report = json.load(f)
    except Exception:
        return False

    return (
        report.get("final_output") == final_path
        and report.get("render_profile") == profile_name
    )


def print_render_summary(manifest):
    config = manifest["config"]
    videos = manifest["videos"]
    overlay_fps = int(config["setting"]["layout"]["overlay_fps"])
    output_speed = float(config["output"]["hyperlapse_speed"])
    closing_add = bool(config["output"]["closing_screen"]["add"])
    closing_seconds = int(config["output"]["closing_screen"]["time"]) if closing_add else 0

    input_file_seconds = sum(float(v["duration_file_seconds"]) for v in videos)
    input_real_seconds = sum(float(v["real_duration_seconds"] or 0) for v in videos)
    estimated_final_seconds = (input_file_seconds / output_speed) + closing_seconds
    estimated_frames = sum(math.ceil(float(v["duration_file_seconds"]) * overlay_fps) for v in videos)

    print("")
    print("===== RESUMEN ANTES DEL RENDER FINAL =====")
    print("Videos:", len(videos))
    print("Duracion total real:", str(timedelta(seconds=round(input_real_seconds))))
    print("Duracion final estimada:", str(timedelta(seconds=round(estimated_final_seconds))))
    print("Overlay FPS:", overlay_fps)
    print("Frames aproximados:", estimated_frames)
    print("Carpeta salida:", os.path.join(manifest["resolved_paths"]["output_dir"], "final"))
    print("Pantalla final:", closing_add, "-", closing_seconds, "s")
    print("Limpiar al terminar:", config["output"].get("cleanup_after_render", True))
    print("")


def write_render_report(manifest, manifest_path, final_path, render_profile):
    config = manifest["config"]
    videos = manifest["videos"]
    output_dir = manifest["resolved_paths"]["output_dir"]
    final_dir = os.path.join(output_dir, "final")
    os.makedirs(final_dir, exist_ok=True)

    input_file_seconds = sum(float(v["duration_file_seconds"]) for v in videos)
    input_real_seconds = sum(float(v["real_duration_seconds"] or 0) for v in videos)

    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "final_output": final_path,
        "render_profile": render_profile,
        "manifest_path": manifest_path,
        "videos": [
            {
                "name": v["name"],
                "path": v["path"],
                "start_utc": v["start_utc"],
                "real_end_utc": v["real_end_utc"],
                "gps_status": v["gps_status"],
            }
            for v in videos
        ],
        "gpx": manifest["gpx"],
        "input_duration_file_seconds": round(input_file_seconds, 2),
        "input_duration_real_seconds": round(input_real_seconds, 2),
        "output_hyperlapse_speed": config["output"]["hyperlapse_speed"],
        "resolution": config["output"]["resolution"],
        "fps": config["output"]["fps"],
        "remove_audio": config["output"]["remove_audio"],
        "closing_screen": config["output"]["closing_screen"],
        "transition": config["output"].get("transition"),
        "errors": [],
        "warnings": [],
    }

    json_path = os.path.join(final_dir, "render_report.json")
    txt_path = os.path.join(final_dir, "render_report.txt")

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    with open(txt_path, "w", encoding="utf-8") as f:
        f.write("DJI / GPX Overlay Render Report\n")
        f.write(f"Generado UTC: {report['generated_at_utc']}\n")
        f.write(f"Final: {final_path}\n")
        f.write(f"GPX: {manifest['gpx']['name']}\n")
        f.write(f"Videos: {len(videos)}\n")
        for idx, video in enumerate(videos, start=1):
            f.write(f"  {idx}. {video['name']} ({video['start_utc']} -> {video['real_end_utc']})\n")
        f.write(f"Resolucion: {config['output']['resolution']}\n")
        f.write(f"FPS: {config['output']['fps']}\n")
        f.write(f"Remove audio: {config['output']['remove_audio']}\n")

    print("")
    print("Reporte final creado:")
    print(json_path)
    print(txt_path)


def render_overlay_frames(root, manifest, video, gpx_points, frames_dir):
    config = manifest["config"]
    resume = bool(config["output"].get("resume", True))

    overlay_fps = int(config["setting"]["layout"]["overlay_fps"])
    input_speed = float(config["input"]["hyperlapse_speed"]) if config["input"]["video_mode"] == "hyperlapse" else 1.0

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

    print_render_summary(manifest)

    gpx_points = enrich_points(read_gpx_points(manifest["gpx"]["path"]))

    output_dir = manifest["resolved_paths"]["output_dir"]
    final_dir = os.path.join(output_dir, "final")
    frames_base = os.path.join(output_dir, "frames")
    profile_name = render_profile_name(config)
    temp_dir = os.path.join(root, "temp", profile_name)

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
        frames_dir = os.path.join(frames_base, profile_name, f"final_{video_base}")
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
        if resume and final_artifact_matches_profile(final_path, final_dir, profile_name):
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

    write_render_report(manifest, manifest_path, final_path, profile_name)

    if config["output"].get("cleanup_after_render", True):
        cleanup_auto_after_render(root)

if __name__ == "__main__":
    main()
