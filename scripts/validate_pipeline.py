import argparse
import json
import math
import os
import sys
from datetime import timedelta, timezone
from zoneinfo import ZoneInfo

from gpx_track import read_gpx
from pipeline_config import RESOLUTION_MAP, load_config, parse_float_1, parse_float_range, parse_overrides
from pipeline_utils import estimated_output_seconds, ffmpeg_output_speed_factor, fmt, resolve_path, safe_name
from video_metadata import analyze_video, apply_creation_time_override, ffprobe_video, list_video_files, sort_videos_by_start

def validate_config(config, root):
    errors = []
    warnings = []

    tz_name = config["input"]["timezone"]

    if tz_name in ["America/Bogota", "America/Bogotá", "UTC-5", "-05:00"]:
        tz = timezone(timedelta(hours=-5))
    elif tz_name.upper() == "UTC":
        tz = timezone.utc
    else:
        try:
            tz = ZoneInfo(tz_name)
        except Exception:
            errors.append("input.timezone no es valido o no esta disponible en este Python. Usa America/Bogota o UTC.")
            tz = timezone(timedelta(hours=-5))

    if config["input"]["video_mode"] not in ["normal", "hyperlapse"]:
        errors.append("input.video_mode debe ser normal|hyperlapse.")

    try:
        config["input"]["hyperlapse_speed"] = parse_float_range(
            config["input"]["hyperlapse_speed"],
            "input.hyperlapse_speed",
            1.0,
            50.0
        )
    except Exception as e:
        errors.append(str(e))

    if config["output"]["resolution"] not in RESOLUTION_MAP:
        errors.append("output.resolution debe ser 1080p|2k|4k.")

    if config["output"]["fps"] not in [15, 30, 60]:
        errors.append("output.fps debe ser 15|30|60.")

    try:
        config["output"]["hyperlapse_speed"] = parse_float_range(
            config["output"]["hyperlapse_speed"],
            "output.hyperlapse_speed",
            0.1,
            50.0
        )
    except Exception as e:
        errors.append(str(e))

    if not isinstance(config["output"].get("resume"), bool):
        errors.append("output.resume debe ser true|false.")

    if not isinstance(config["output"].get("cleanup_after_render"), bool):
        errors.append("output.cleanup_after_render debe ser true|false.")

    transition = config["output"].get("transition", {})
    if not isinstance(transition.get("add"), bool):
        errors.append("output.transition.add debe ser true|false.")

    if transition.get("type") not in ["fade_black"]:
        errors.append("output.transition.type debe ser fade_black.")

    try:
        transition["time"] = parse_float_1(transition.get("time"), "output.transition.time")
    except Exception as e:
        errors.append(str(e))

    if isinstance(transition.get("time"), (int, float)) and transition["time"] <= 0:
        errors.append("output.transition.time debe ser mayor que 0.")

    preview_time = config["output"]["preview"]["time"]
    if not isinstance(preview_time, int) or preview_time < 1 or preview_time > 60:
        errors.append("output.preview.time debe ser entero entre 1 y 60.")

    closing_time = config["output"]["closing_screen"]["time"]
    if not isinstance(closing_time, int) or closing_time < 1 or closing_time > 5:
        errors.append("output.closing_screen.time debe ser entero entre 1 y 5.")

    if not config["output"]["closing_screen"]["message"]:
        config["output"]["closing_screen"]["message"] = "Ruta Finalizada"

    if config["setting"]["layout"]["theme"] not in ["sport"]:
        errors.append("setting.layout.theme solo admite sport por ahora.")

    overlay_fps = config["setting"]["layout"]["overlay_fps"]
    if not isinstance(overlay_fps, int) or overlay_fps < 1 or overlay_fps > 60:
        errors.append("setting.layout.overlay_fps debe ser entero entre 1 y 60.")

    performance = config["setting"].get("performance", {})
    frame_workers = performance.get("frame_workers")
    ffmpeg_threads = performance.get("ffmpeg_threads")

    if not isinstance(frame_workers, int) or frame_workers < 0 or frame_workers > 64:
        errors.append("setting.performance.frame_workers debe ser entero entre 0 y 64. Usa 0 para automatico.")

    if not isinstance(ffmpeg_threads, int) or ffmpeg_threads < 0 or ffmpeg_threads > 64:
        errors.append("setting.performance.ffmpeg_threads debe ser entero entre 0 y 64. Usa 0 para automatico.")

    video_overrides = config.get("video_overrides", {})
    if not isinstance(video_overrides, dict):
        errors.append("video_overrides debe ser un objeto JSON.")
    else:
        for name, override in video_overrides.items():
            if not isinstance(override, dict):
                errors.append(f"video_overrides.{name} debe ser un objeto JSON.")
            elif "creation_time" in override and not isinstance(override["creation_time"], str):
                errors.append(f"video_overrides.{name}.creation_time debe ser texto ISO, por ejemplo 2026-06-28T16:33:40Z.")

    videos_dir = resolve_path(root, config["input"]["videos_dir"])
    gpx_dir = resolve_path(root, config["input"]["gpx_dir"])
    output_dir = resolve_path(root, config["output"]["dir"])
    font_path = resolve_path(root, config["setting"]["layout"]["font_path"])

    if not os.path.isdir(videos_dir):
        errors.append(f"input.videos_dir no existe: {videos_dir}")

    if not os.path.isdir(gpx_dir):
        errors.append(f"input.gpx_dir no existe: {gpx_dir}")

    if not os.path.isdir(output_dir):
        errors.append(f"output.dir no existe: {output_dir}")

    if not os.path.exists(font_path):
        warnings.append(f"No se encontro fuente personalizada, se usara fallback: {font_path}")

    return errors, warnings, tz, {
        "videos_dir": videos_dir,
        "gpx_dir": gpx_dir,
        "output_dir": output_dir,
        "font_path": font_path
    }

def final_output_path(manifest):
    config = manifest["config"]
    output_dir = manifest["resolved_paths"]["output_dir"]
    final_dir = os.path.join(output_dir, "final")
    route_name = config["input"]["route_name"] or os.path.splitext(manifest["gpx"]["name"])[0]
    out_name = safe_name(route_name)
    speed_txt = str(config["output"]["hyperlapse_speed"]).replace(".", "p")
    resolution = config["output"]["resolution"]

    if config["output"]["single_final_video"]:
        return os.path.join(final_dir, f"{out_name}_overlay_hyperlapse_{speed_txt}x_{resolution}.mp4")
    return final_dir


def print_validate_only_summary(manifest):
    config = manifest["config"]
    videos = manifest["videos"]
    overlay_fps = int(config["setting"]["layout"]["overlay_fps"])
    closing_add = bool(config["output"]["closing_screen"]["add"])
    closing_seconds = int(config["output"]["closing_screen"]["time"]) if closing_add else 0

    input_file_seconds = sum(float(v["duration_file_seconds"]) for v in videos)
    input_real_seconds = sum(float(v["real_duration_seconds"] or 0) for v in videos)
    estimated_final_seconds = sum(
        estimated_output_seconds(config, v["duration_file_seconds"], v.get("real_duration_seconds"))
        for v in videos
    ) + closing_seconds
    estimated_frames = sum(math.ceil(float(v["duration_file_seconds"]) * overlay_fps) for v in videos)

    print("")
    print("===== VALIDATE ONLY / DRY RUN =====")
    print("Videos detectados:", len(videos))
    for idx, video in enumerate(videos, start=1):
        print(f"  {idx}. {video['name']}")
        print("     Inicio:", video["start_local"])
        print("     Fin real:", video["real_end_local"])
        print("     GPS:", video["gps_status"])
    print("GPX usado:", manifest["gpx"]["name"])
    print("Duracion total archivos:", str(timedelta(seconds=round(input_file_seconds))))
    print("Duracion real total:", str(timedelta(seconds=round(input_real_seconds))))
    print("Duracion final estimada:", str(timedelta(seconds=round(estimated_final_seconds))))
    print("Velocidad final deseada:", config["output"]["hyperlapse_speed"], "x")
    print("Factor tecnico FFmpeg:", round(ffmpeg_output_speed_factor(config), 6), "x")
    print("Frames estimados:", estimated_frames)
    print("Resolucion final:", config["output"]["resolution"])
    print("FPS final:", config["output"]["fps"])
    print("Archivo final esperado:", final_output_path(manifest))
    print("No se generaron frames ni videos.")


def main():
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("--root", required=True)
    parser.add_argument("--validate-only", action="store_true")
    known, unknown = parser.parse_known_args()

    root = known.root
    config_path = os.path.join(root, "input", "pipeline_config.json")

    config = load_config(config_path)
    config = parse_overrides(unknown, config)

    errors, warnings, tz, paths = validate_config(config, root)

    if errors:
        print("")
        print("ERRORES DE CONFIGURACION:")
        for e in errors:
            print(" -", e)
        sys.exit(1)

    print("CONFIGURACION RESUELTA")
    print("Input videos:", paths["videos_dir"])
    print("Input GPX:", paths["gpx_dir"])
    print("Output:", paths["output_dir"])
    print("Video mode:", config["input"]["video_mode"])
    print("Input hyperlapse speed:", config["input"]["hyperlapse_speed"])
    print("Output hyperlapse speed:", config["output"]["hyperlapse_speed"])
    print("Resolution:", config["output"]["resolution"])
    print("FPS:", config["output"]["fps"])
    print("Remove audio:", config["output"]["remove_audio"])
    print("Resume:", config["output"]["resume"])
    print("Preview:", config["output"]["preview"]["add"], "-", config["output"]["preview"]["time"], "s")
    print("Closing screen:", config["output"]["closing_screen"]["add"], "-", config["output"]["closing_screen"]["time"], "s")
    print("Frame workers:", config["setting"]["performance"]["frame_workers"])
    print("FFmpeg threads:", config["setting"]["performance"]["ffmpeg_threads"])
    print("Theme:", config["setting"]["layout"]["theme"])

    if warnings:
        print("")
        print("ADVERTENCIAS:")
        for w in warnings:
            print(" -", w)

    videos = list_video_files(paths["videos_dir"])

    gpx_files = sorted([
        os.path.join(paths["gpx_dir"], f)
        for f in os.listdir(paths["gpx_dir"])
        if f.lower().endswith(".gpx")
    ])

    if not videos:
        raise Exception("No hay videos MP4/MOV en input.videos_dir.")

    if not gpx_files:
        raise Exception("No hay GPX en input.gpx_dir.")

    if len(gpx_files) > 1:
        names = ", ".join(os.path.basename(p) for p in gpx_files)
        raise Exception(f"Hay mas de un GPX en input.gpx_dir. Deja solo uno por ejecucion. GPX encontrados: {names}")

    gpx_path = gpx_files[0]
    gpx = read_gpx(gpx_path)

    print("")
    print("===== VALIDACION TECNICA =====")
    print("")
    print("GPX usado:", os.path.basename(gpx_path))
    print("Puntos GPX:", gpx["count"])
    print("Inicio GPX:", fmt(gpx["start"], tz))
    print("Fin GPX:", fmt(gpx["end"], tz))
    print("Duracion GPX:", str(gpx["end"] - gpx["start"]))
    print("")

    video_results = []
    target_w, target_h = RESOLUTION_MAP[config["output"]["resolution"]]
    video_overrides = {
        name.lower(): value
        for name, value in config.get("video_overrides", {}).items()
    }

    probed = []
    for video_path in videos:
        video = ffprobe_video(video_path)
        override = video_overrides.get(video["name"].lower(), {}).get("creation_time")
        if override:
            video = apply_creation_time_override(video, override)
        probed.append(video)

    probed_videos = sort_videos_by_start(probed)

    for video in probed_videos:
        analysis = analyze_video(video, gpx, config["input"]["video_mode"], config["input"]["hyperlapse_speed"])

        print("Video:", video["name"])
        print("  Resolucion:", f'{video["width"]}x{video["height"]}')
        print("  FPS original:", video["fps_raw"] or "SIN FPS")
        print("  Inicio:", fmt(video["start"], tz))
        print("  Fuente inicio:", video["start_source"])
        print("  Fin archivo:", fmt(video["end"], tz))
        print("  Fin real segun modo:", fmt(analysis["real_end"], tz))
        print("  Duracion archivo:", str(timedelta(seconds=round(video["duration_seconds"]))))
        print("  Duracion real:", str(timedelta(seconds=round(analysis["real_duration_seconds"] or 0))))
        print("  Estado GPS:", analysis["status"])

        if video["width"] and video["height"]:
            if video["width"] < target_w or video["height"] < target_h:
                raise Exception(
                    f'La resolucion de salida {config["output"]["resolution"]} '
                    f'es mayor que el video {video["name"]} ({video["width"]}x{video["height"]}).'
                )

        if analysis["status"] == "GPX_PARCIAL":
            print("  Sin GPS al inicio:", analysis["missing_before_seconds"], "seg")
            print("  Sin GPS al final:", analysis["missing_after_seconds"], "seg")

        print("")

        video_results.append({
            "name": video["name"],
            "path": video["path"],
            "width": video["width"],
            "height": video["height"],
            "fps": video["fps"],
            "fps_raw": video["fps_raw"],
            "duration_seconds": video["duration_seconds"],
            "duration_file_seconds": video["duration_seconds"],
            "input_video_mode": config["input"]["video_mode"],
            "input_hyperlapse_speed": config["input"]["hyperlapse_speed"],
            "real_duration_seconds": analysis["real_duration_seconds"],
            "start_utc": video["start"].isoformat() if video["start"] else None,
            "real_start_utc": video["start"].isoformat() if video["start"] else None,
            "end_file_utc": video["end"].isoformat() if video["end"] else None,
            "end_real_utc": analysis["real_end"].isoformat() if analysis["real_end"] else None,
            "real_end_utc": analysis["real_end"].isoformat() if analysis["real_end"] else None,
            "start_local": fmt(video["start"], tz),
            "real_start_local": fmt(video["start"], tz),
            "end_file_local": fmt(video["end"], tz),
            "end_real_local": fmt(analysis["real_end"], tz),
            "real_end_local": fmt(analysis["real_end"], tz),
            "creation_time_raw": video["creation_time_raw"],
            "creation_time_used": video["creation_time_used"],
            "start_source": video["start_source"],
            "gps_status": analysis["status"],
            "overlap_seconds": analysis["overlap_seconds"],
            "missing_before_seconds": analysis["missing_before_seconds"],
            "missing_after_seconds": analysis["missing_after_seconds"]
        })

    output_data_dir = os.path.join(paths["output_dir"], "data")
    os.makedirs(output_data_dir, exist_ok=True)

    manifest = {
        "project_root": root,
        "config": config,
        "resolved_paths": paths,
        "gpx": {
            "name": os.path.basename(gpx_path),
            "path": gpx_path,
            "points": gpx["count"],
            "start_utc": gpx["start"].isoformat(),
            "end_utc": gpx["end"].isoformat(),
            "start_local": fmt(gpx["start"], tz),
            "end_local": fmt(gpx["end"], tz)
        },
        "videos": video_results
    }

    manifest_path = os.path.join(output_data_dir, "manifest.json")

    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    print("Manifest creado:")
    print(manifest_path)
    if known.validate_only:
        print_validate_only_summary(manifest)
    print("")
    print("Validacion tecnica OK.")

if __name__ == "__main__":
    main()

