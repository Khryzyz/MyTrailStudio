from __future__ import annotations

from copy import deepcopy
from typing import Any

from ui_core.services.export_settings import update_export_settings


EXPORT_PRESETS: dict[str, dict[str, Any]] = {
    "preview-fast": {
        "name": "Preview Fast",
        "description": "Low-friction settings for quick preview iterations.",
        "settings": {
            "resolution": "1080p",
            "fps": 30,
            "output_hyperlapse_speed": 3.5,
            "remove_audio": True,
            "single_final_video": True,
            "apply_transitions": False,
            "closing_enabled": False,
            "closing_message": "Route Completed",
            "closing_seconds": 3,
        },
    },
    "standard-1080p": {
        "name": "Standard 1080p",
        "description": "Balanced default for final MP4 exports.",
        "settings": {
            "resolution": "1080p",
            "fps": 30,
            "output_hyperlapse_speed": 3.5,
            "remove_audio": True,
            "single_final_video": True,
            "apply_transitions": True,
            "closing_enabled": True,
            "closing_message": "Route Completed",
            "closing_seconds": 3,
        },
    },
    "final-4k": {
        "name": "Final 4K",
        "description": "Higher-resolution final export when source footage supports it.",
        "settings": {
            "resolution": "4k",
            "fps": 30,
            "output_hyperlapse_speed": 3.5,
            "remove_audio": True,
            "single_final_video": True,
            "apply_transitions": True,
            "closing_enabled": True,
            "closing_message": "Route Completed",
            "closing_seconds": 3,
        },
    },
    "social-vertical-source": {
        "name": "Social Vertical Source",
        "description": "Compact 1080p export baseline for social edits from vertical footage.",
        "settings": {
            "resolution": "1080p",
            "fps": 30,
            "output_hyperlapse_speed": 4.0,
            "remove_audio": True,
            "single_final_video": True,
            "apply_transitions": True,
            "closing_enabled": False,
            "closing_message": "Route Completed",
            "closing_seconds": 3,
        },
    },
}


def list_export_presets() -> list[dict[str, Any]]:
    return [
        {
            "id": preset_id,
            "name": preset["name"],
            "description": preset["description"],
            "settings": deepcopy(preset["settings"]),
        }
        for preset_id, preset in EXPORT_PRESETS.items()
    ]


def get_export_preset(preset_id: str) -> dict[str, Any]:
    try:
        return deepcopy(EXPORT_PRESETS[preset_id])
    except KeyError as exc:
        choices = ", ".join(sorted(EXPORT_PRESETS))
        raise ValueError(f"Unknown export preset: {preset_id}. Available presets: {choices}") from exc


def apply_export_preset(project: dict[str, Any], preset_id: str) -> dict[str, Any]:
    preset = get_export_preset(preset_id)
    export = update_export_settings(project, preset["settings"], preset_id=preset_id)
    return {
        "preset_id": preset_id,
        "preset_name": preset["name"],
        "export": export,
    }
