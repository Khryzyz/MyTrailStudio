import json
import os
import re
from copy import deepcopy


DEFAULT_CONFIG = {
    "input": {
        "videos_dir": "input",
        "gpx_dir": "input",
        "timezone": "America/Bogota",
        "video_mode": "normal",
        "hyperlapse_speed": 1.0,
        "route_name": ""
    },
    "output": {
        "dir": "output",
        "resolution": "1080p",
        "fps": 30,
        "hyperlapse_speed": 1.0,
        "remove_audio": False,
        "single_final_video": False,
        "resume": True,
        "cleanup_after_render": True,
        "transition": {
            "add": True,
            "type": "fade_black",
            "time": 0.5
        },
        "preview": {
            "add": False,
            "time": 10
        },
        "closing_screen": {
            "add": False,
            "message": "Ruta Finalizada",
            "time": 3
        }
    },
    "setting": {
        "performance": {
            "frame_workers": 0,
            "ffmpeg_threads": 0
        },
        "layout": {
            "theme": "sport",
            "font_path": "resources/font/font.otf",
            "overlay_fps": 10,
            "pulse_map_point": True,
            "show_gps_unavailable": True,
            "keep_temp_frames": True
        }
    }
}

PARAM_MAP = {
    "input.videosdir": ("input", "videos_dir"),
    "input.gpxdir": ("input", "gpx_dir"),
    "input.timezone": ("input", "timezone"),
    "input.videomode": ("input", "video_mode"),
    "input.hyperlapsespeed": ("input", "hyperlapse_speed"),
    "input.routename": ("input", "route_name"),

    "output.dir": ("output", "dir"),
    "output.resolution": ("output", "resolution"),
    "output.fps": ("output", "fps"),
    "output.hyperlapsespeed": ("output", "hyperlapse_speed"),
    "output.removeaudio": ("output", "remove_audio"),
    "output.singlefinalvideo": ("output", "single_final_video"),
    "output.resume": ("output", "resume"),
    "output.cleanupafterrender": ("output", "cleanup_after_render"),
    "output.cleanup_after_render": ("output", "cleanup_after_render"),
    "output.transition.add": ("output", "transition", "add"),
    "output.transition.type": ("output", "transition", "type"),
    "output.transition.time": ("output", "transition", "time"),

    "output.preview.add": ("output", "preview", "add"),
    "output.preview.time": ("output", "preview", "time"),

    "output.closingscreen.add": ("output", "closing_screen", "add"),
    "output.closingscreen.message": ("output", "closing_screen", "message"),
    "output.closingscreen.time": ("output", "closing_screen", "time"),

    "setting.performance.frame_workers": ("setting", "performance", "frame_workers"),
    "setting.performance.ffmpegthreads": ("setting", "performance", "ffmpeg_threads"),
    "setting.performance.ffmpeg_threads": ("setting", "performance", "ffmpeg_threads"),

    "setting.layout.theme": ("setting", "layout", "theme"),
    "setting.layout.fontpath": ("setting", "layout", "font_path"),
    "setting.layout.overlayfps": ("setting", "layout", "overlay_fps"),
    "setting.layout.pulsemappoint": ("setting", "layout", "pulse_map_point"),
    "setting.layout.showgpsunavailable": ("setting", "layout", "show_gps_unavailable"),
    "setting.layout.keeptempframes": ("setting", "layout", "keep_temp_frames"),
}

RESOLUTION_MAP = {
    "1080p": (1920, 1080),
    "2k": (2560, 1440),
    "4k": (3840, 2160),
}


def deep_merge(base, override):
    result = deepcopy(base)
    for k, v in override.items():
        if isinstance(v, dict) and isinstance(result.get(k), dict):
            result[k] = deep_merge(result[k], v)
        else:
            result[k] = v
    return result


def set_nested(config, path, value):
    ref = config
    for key in path[:-1]:
        ref = ref[key]
    ref[path[-1]] = value


def get_nested(config, path):
    ref = config
    for key in path:
        ref = ref[key]
    return ref


def parse_bool(value):
    if isinstance(value, bool):
        return value
    v = str(value).strip().lower()
    if v in ["true", "1", "yes", "y", "si", "sí"]:
        return True
    if v in ["false", "0", "no", "n"]:
        return False
    raise ValueError(f"Valor booleano invalido: {value}")


def parse_float_1(value, name):
    text = str(value).strip()
    if not re.fullmatch(r"\d+(\.\d)?", text):
        raise ValueError(f"{name} debe ser float con maximo 1 decimal. Valor recibido: {value}")
    return float(text)


def parse_overrides(argv, config):
    args = list(argv)
    i = 0

    while i < len(args):
        raw_key = args[i]

        if not raw_key.startswith("--"):
            raise ValueError(f"Parametro invalido: {raw_key}")

        key = raw_key[2:].lower()

        if key not in PARAM_MAP:
            valid = ", ".join(sorted("--" + k for k in PARAM_MAP.keys()))
            raise ValueError(f"Parametro no soportado: {raw_key}\nParametros validos:\n{valid}")

        if i + 1 >= len(args):
            raise ValueError(f"Falta valor para parametro: {raw_key}")

        raw_value = args[i + 1]
        path = PARAM_MAP[key]
        current_value = get_nested(config, path)

        if isinstance(current_value, bool):
            value = parse_bool(raw_value)
        elif isinstance(current_value, int):
            value = int(raw_value)
        elif isinstance(current_value, float):
            value = parse_float_1(raw_value, key)
        else:
            value = raw_value

        set_nested(config, path, value)
        i += 2

    return config


def load_config(config_path):
    if not os.path.exists(config_path):
        raise Exception("No existe input/config.json.")

    with open(config_path, "r", encoding="utf-8") as f:
        user_config = json.load(f)

    return deep_merge(DEFAULT_CONFIG, user_config)
