from __future__ import annotations

import os
from pathlib import Path


APP_DIR_NAME = "DJIOverlayUI"


def default_app_data_dir() -> Path:
    appdata = os.environ.get("APPDATA")
    if appdata:
        return Path(appdata) / APP_DIR_NAME
    return Path.home() / f".{APP_DIR_NAME}"


def resolve_app_data_dir(value: str | None = None) -> Path:
    return Path(value).expanduser().resolve() if value else default_app_data_dir()

