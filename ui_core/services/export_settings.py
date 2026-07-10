from __future__ import annotations

from typing import Any

from ui_core.models.project_model import touch_project
from ui_core.services.project_store import save_project


VALID_RESOLUTIONS = {"1080p", "2k", "4k"}
VALID_FPS = {15, 30, 60}


def update_export_settings(
    project: dict[str, Any],
    updates: dict[str, Any],
    *,
    preset_id: str | None = None,
) -> dict[str, Any]:
    export = project["export"]

    if "output_dir" in updates and updates["output_dir"] is not None:
        export["output_dir"] = updates["output_dir"]

    if "resolution" in updates and updates["resolution"] is not None:
        if updates["resolution"] not in VALID_RESOLUTIONS:
            raise ValueError("resolution must be 1080p, 2k, or 4k.")
        export["resolution"] = updates["resolution"]

    if "fps" in updates and updates["fps"] is not None:
        fps = int(updates["fps"])
        if fps not in VALID_FPS:
            raise ValueError("fps must be 15, 30, or 60.")
        export["fps"] = fps

    if "output_hyperlapse_speed" in updates and updates["output_hyperlapse_speed"] is not None:
        speed = float(updates["output_hyperlapse_speed"])
        if speed < 0.1 or speed > 50.0:
            raise ValueError("output_hyperlapse_speed must be between 0.1 and 50.0.")
        export["output_hyperlapse_speed"] = speed

    if "remove_audio" in updates and updates["remove_audio"] is not None:
        export["remove_audio"] = bool(updates["remove_audio"])
        export["include_audio"] = not bool(updates["remove_audio"])

    if "single_final_video" in updates and updates["single_final_video"] is not None:
        export["single_final_video"] = bool(updates["single_final_video"])

    if "apply_transitions" in updates and updates["apply_transitions"] is not None:
        export["apply_transitions"] = bool(updates["apply_transitions"])

    if "closing_enabled" in updates and updates["closing_enabled"] is not None:
        export["closing_screen"]["enabled"] = bool(updates["closing_enabled"])

    if "closing_message" in updates and updates["closing_message"] is not None:
        export["closing_screen"]["message"] = updates["closing_message"]

    if "closing_seconds" in updates and updates["closing_seconds"] is not None:
        seconds = int(updates["closing_seconds"])
        if seconds < 1 or seconds > 5:
            raise ValueError("closing_seconds must be between 1 and 5.")
        export["closing_screen"]["seconds"] = seconds

    if preset_id is not None:
        export["preset_id"] = preset_id
    elif any(value is not None for value in updates.values()):
        export["preset_id"] = "custom"

    touch_project(project)
    save_project(project)
    return export



