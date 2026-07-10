from __future__ import annotations

from pathlib import Path


REQUIRED_ENGINE_PATHS = [
    "scripts",
    "resources",
    "scripts/gpx_track.py",
    "scripts/video_metadata.py",
    "scripts/pipeline_config.py",
    "scripts/validate_pipeline.py",
]


def resolve_engine_root(value: str | None = None) -> Path:
    root = Path(value).expanduser() if value else Path.cwd()
    root = root.resolve()
    missing = [relative for relative in REQUIRED_ENGINE_PATHS if not (root / relative).exists()]
    if missing:
        missing_text = ", ".join(missing)
        raise FileNotFoundError(
            "La carpeta actual no parece ser el engine My Trail Studio. "
            f"Root usado: {root}. Faltan: {missing_text}. "
            "Ejecuta el comando desde la carpeta del engine o usa --engine-root."
        )
    return root


