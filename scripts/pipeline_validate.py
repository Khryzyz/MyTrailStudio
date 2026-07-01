import argparse
import json
import os
import sys
from datetime import timedelta, timezone
from zoneinfo import ZoneInfo

from config_io import RESOLUTION_MAP, load_config, parse_float_1, parse_overrides
from gpx_io import read_gpx
from utils import fmt, resolve_path
from video_metadata import analyze_video, ffprobe_video

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
        config["input"]["hyperlapse_speed"] = parse_float_1(config["input"]["hyperlapse_speed"], "input.hyperlapse_speed")
    except Exception as e:
        errors.append(str(e))

    if config["input"]["hyperlapse_speed"] < 1:
        errors.append("input.hyperlapse_speed debe ser >= 1.0.")

    if config["output"]["resolution"] not in RESOLUTION_MAP:
        errors.append("output.resolution debe ser 1080p|2k|4k.")

    if config["output"]["fps"] not in [15, 30, 60]:
        errors.append("output.fps debe ser 15|30|60.")

    try:
        config["output"]["hyperlapse_speed"] = parse_float_1(config["output"]["hyperlapse_speed"], "output.hyperlapse_speed")
    except Exception as e:
        errors.append(str(e))

    if config["output"]["hyperlapse_speed"] < 1:
        errors.append("output.hyperlapse_speed debe ser >= 1.0.")

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

def main():
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("--root", required=True)
    known, unknown = parser.parse_known_args()

    root = known.root
    config_path = os.path.join(root, "input", "config.json")

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
    print("Preview:", config["output"]["preview"]["add"], "-", config["output"]["preview"]["time"], "s")
    print("Closing screen:", config["output"]["closing_screen"]["add"], "-", config["output"]["closing_screen"]["time"], "s")
    print("Theme:", config["setting"]["layout"]["theme"])

    if warnings:
        print("")
        print("ADVERTENCIAS:")
        for w in warnings:
            print(" -", w)

    videos = sorted([
        os.path.join(paths["videos_dir"], f)
        for f in os.listdir(paths["videos_dir"])
        if f.lower().endswith(".mp4")
    ])

    gpx_files = sorted([
        os.path.join(paths["gpx_dir"], f)
        for f in os.listdir(paths["gpx_dir"])
        if f.lower().endswith(".gpx")
    ])

    if not videos:
        raise Exception("No hay videos MP4 en input.videos_dir.")

    if not gpx_files:
        raise Exception("No hay GPX en input.gpx_dir.")

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

    for video_path in videos:
        video = ffprobe_video(video_path)
        analysis = analyze_video(video, gpx, config["input"]["hyperlapse_speed"])

        print("Video:", video["name"])
        print("  Resolucion:", f'{video["width"]}x{video["height"]}')
        print("  Inicio:", fmt(video["start"], tz))
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
            "duration_seconds": video["duration_seconds"],
            "real_duration_seconds": analysis["real_duration_seconds"],
            "start_utc": video["start"].isoformat() if video["start"] else None,
            "end_file_utc": video["end"].isoformat() if video["end"] else None,
            "end_real_utc": analysis["real_end"].isoformat() if analysis["real_end"] else None,
            "start_local": fmt(video["start"], tz),
            "end_file_local": fmt(video["end"], tz),
            "end_real_local": fmt(analysis["real_end"], tz),
            "creation_time_raw": video["creation_time_raw"],
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
    print("")
    print("Validacion tecnica OK.")

if __name__ == "__main__":
    main()

