from __future__ import annotations

import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

from ui_core.models.project_model import touch_project
from ui_core.services.engine_root import resolve_engine_root
from ui_core.services.json_io import write_json
from ui_core.services.project_store import save_project


def _add_scripts_to_path(engine_root: Path) -> None:
    scripts_dir = str(engine_root / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)


def build_engine_config(project: dict[str, Any], overrides: dict[str, Any] | None = None) -> Path:
    engine_root = resolve_engine_root(project["workspace"].get("engine_root"))
    _add_scripts_to_path(engine_root)
    from pipeline_config import DEFAULT_CONFIG

    config = deepcopy(DEFAULT_CONFIG)
    export = project["export"]
    gpx_path = Path(project["assets"]["gpx"]["path"])
    videos = project["assets"].get("videos", [])

    config["input"]["gpx_dir"] = str(gpx_path.parent)
    config["input"]["gpx_path"] = str(gpx_path)
    config["input"]["route_name"] = project["project"]["name"]
    config["input"]["timezone"] = project["project"].get("timezone", "America/Bogota")

    if videos:
        first_video_path = Path(videos[0]["path"])
        config["input"]["videos_dir"] = str(first_video_path.parent)
        config["input"]["video_files"] = [video["path"] for video in videos]
        config["input"]["video_mode"] = videos[0].get("mode", "normal")
        config["input"]["hyperlapse_speed"] = float(videos[0].get("hyperlapse_speed", 2.0))
    else:
        config["input"]["videos_dir"] = str(engine_root / "input")

    config["output"]["dir"] = export["output_dir"]
    config["output"]["resolution"] = export["resolution"]
    config["output"]["fps"] = int(export["fps"])
    config["output"]["hyperlapse_speed"] = float(export["output_hyperlapse_speed"])
    config["output"]["remove_audio"] = bool(export["remove_audio"])
    config["output"]["single_final_video"] = bool(export["single_final_video"])
    config["output"]["transition"]["add"] = bool(export["apply_transitions"])
    config["output"]["preview"]["add"] = bool(export["preview"]["enabled"])
    config["output"]["preview"]["time"] = int(export["preview"]["seconds"])
    config["output"]["closing_screen"]["add"] = bool(export["closing_screen"]["enabled"])
    config["output"]["closing_screen"]["message"] = export["closing_screen"]["message"]
    config["output"]["closing_screen"]["time"] = int(export["closing_screen"]["seconds"])

    if overrides:
        preview = overrides.get("preview")
        if preview:
            config["output"]["preview"]["add"] = bool(preview.get("enabled", config["output"]["preview"]["add"]))
            config["output"]["preview"]["time"] = int(preview.get("seconds", config["output"]["preview"]["time"]))

    runtime_dir = Path(project["workspace"]["runtime_dir"])
    config_path = runtime_dir / "pipeline_config.generated.json"
    write_json(config_path, config)

    project["engine"]["generated_config_path"] = str(config_path)
    touch_project(project)
    save_project(project)
    return config_path


