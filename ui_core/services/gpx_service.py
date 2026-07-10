from __future__ import annotations

import sys
from pathlib import Path
from typing import Any


def _add_scripts_to_path(engine_root: Path) -> None:
    scripts_dir = str(engine_root / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)


def summarize_gpx(engine_root: Path, gpx_path: Path) -> dict[str, Any]:
    _add_scripts_to_path(engine_root)
    from gpx_track import enrich_points, read_gpx_points

    points = enrich_points(read_gpx_points(str(gpx_path)))
    if not points:
        raise ValueError(f"El GPX no tiene puntos validos: {gpx_path}")

    elevations = [p["ele"] for p in points]
    start = points[0]["time"]
    end = points[-1]["time"]

    return {
        "path": str(gpx_path),
        "start_utc": start.isoformat(),
        "end_utc": end.isoformat(),
        "duration_seconds": round((end - start).total_seconds(), 2),
        "distance_m": round(points[-1]["dist_m"], 2),
        "min_altitude_m": round(min(elevations), 2),
        "max_altitude_m": round(max(elevations), 2),
        "points_count": len(points),
    }

