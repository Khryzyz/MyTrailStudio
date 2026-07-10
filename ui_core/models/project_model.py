from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


SCHEMA_VERSION = 1


DEFAULT_EXPORT = {
    "output_dir": "",
    "file_name": None,
    "format": "mp4",
    "resolution": "1080p",
    "fps": 30,
    "output_hyperlapse_speed": 1.0,
    "include_audio": False,
    "remove_audio": True,
    "single_final_video": True,
    "apply_transitions": True,
    "preview": {
        "enabled": False,
        "seconds": 10,
    },
    "closing_screen": {
        "enabled": False,
        "message": "Route Completed",
        "seconds": 3,
    },
}


DEFAULT_LAYOUT = {
    "active_layout_id": "engine_default_sport",
    "layouts": [
        {
            "id": "engine_default_sport",
            "name": "Sport actual",
            "source": "engine_default",
            "editable": False,
            "settings": {},
        }
    ],
}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def new_project_document(
    *,
    name: str,
    timezone_name: str,
    engine_root: str,
    project_data_dir: str,
    gpx_path: str,
    output_dir: str,
    gpx_summary: dict[str, Any],
) -> dict[str, Any]:
    project_id = str(uuid4())
    now = utc_now_iso()
    export = deepcopy(DEFAULT_EXPORT)
    export["output_dir"] = output_dir

    return {
        "schema_version": SCHEMA_VERSION,
        "project": {
            "id": project_id,
            "name": name,
            "active": False,
            "created_at_utc": now,
            "updated_at_utc": now,
            "timezone": timezone_name,
        },
        "workspace": {
            "engine_root": engine_root,
            "project_data_dir": project_data_dir,
            "runtime_dir": f"{project_data_dir}/runtime",
            "temp_dir": f"{project_data_dir}/temp",
            "cache_dir": f"{project_data_dir}/cache",
            "logs_dir": f"{project_data_dir}/logs",
        },
        "assets": {
            "gpx": {
                "path": gpx_path,
                "import_mode": "reference",
            },
            "videos": [],
            "audios": [],
        },
        "gpx_summary": gpx_summary,
        "timelines": [],
        "layout": deepcopy(DEFAULT_LAYOUT),
        "auxiliary_views": [],
        "export": export,
        "engine": {
            "base_config_policy": "do_not_modify",
            "generated_config_path": None,
            "last_manifest_path": None,
            "last_validation": None,
        },
    }


def touch_project(document: dict[str, Any]) -> dict[str, Any]:
    document["project"]["updated_at_utc"] = utc_now_iso()
    return document



