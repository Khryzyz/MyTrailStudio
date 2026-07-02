import os
from datetime import datetime, timezone
from PIL import ImageFont


def resolve_path(root, value):
    if os.path.isabs(value):
        return value
    return os.path.join(root, value)


def parse_dt(value):
    if not value:
        return None
    value = value.strip()
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(value).astimezone(timezone.utc)
    except Exception:
        return None


def fmt(dt, tz):
    if not dt:
        return "SIN HORA"
    return dt.astimezone(tz).strftime("%Y-%m-%d %H:%M:%S")


def load_font(path, size):
    candidates = [
        path,
        r"C:\Windows\Fonts\bahnschrift.ttf",
        r"C:\Windows\Fonts\segoeui.ttf",
        r"C:\Windows\Fonts\arial.ttf",
        r"C:\Windows\Fonts\calibri.ttf"
    ]

    for p in candidates:
        try:
            if p and os.path.exists(p):
                return ImageFont.truetype(p, size)
        except:
            pass

    return ImageFont.load_default()


def safe_name(value):
    keep = []
    for c in value:
        if c.isalnum() or c in ["-", "_"]:
            keep.append(c)
        elif c in [" ", "."]:
            keep.append("_")
    return "".join(keep).strip("_")
