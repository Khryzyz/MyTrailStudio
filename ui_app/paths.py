from __future__ import annotations

import sys
from pathlib import Path


if getattr(sys, "frozen", False):
    ENGINE_ROOT = Path(getattr(sys, "_MEIPASS")).resolve()
else:
    ENGINE_ROOT = Path(__file__).resolve().parents[1]

ASSETS_DIR = ENGINE_ROOT / "resources" / "assets"
LOGO_PATH = ASSETS_DIR / "logo.png"
ISOTYPE_PATH = ASSETS_DIR / "iso.png"
