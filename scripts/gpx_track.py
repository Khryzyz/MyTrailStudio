import math
import xml.etree.ElementTree as ET

from pipeline_utils import parse_dt


def child_text(elem, suffix):
    for child in elem:
        if child.tag.lower().endswith(suffix.lower()):
            return child.text
    return None


def read_gpx(gpx_path):
    tree = ET.parse(gpx_path)
    root = tree.getroot()
    points = []

    for elem in root.iter():
        if elem.tag.lower().endswith("trkpt"):
            lat = elem.attrib.get("lat")
            lon = elem.attrib.get("lon")
            ele = child_text(elem, "ele")
            time_text = child_text(elem, "time")
            dt = parse_dt(time_text)

            if lat and lon and dt:
                points.append({
                    "lat": float(lat),
                    "lon": float(lon),
                    "ele": float(ele) if ele else None,
                    "time": dt
                })

    points.sort(key=lambda x: x["time"])

    if not points:
        raise Exception("The GPX has no trkpt points with valid time.")

    return {
        "path": gpx_path,
        "points": points,
        "start": points[0]["time"],
        "end": points[-1]["time"],
        "count": len(points)
    }


def read_gpx_points(gpx_path):
    tree = ET.parse(gpx_path)
    root = tree.getroot()
    points = []

    for elem in root.iter():
        if elem.tag.lower().endswith("trkpt"):
            lat = elem.attrib.get("lat")
            lon = elem.attrib.get("lon")
            ele = child_text(elem, "ele")
            time_text = child_text(elem, "time")
            dt = parse_dt(time_text)

            if lat and lon and dt:
                points.append({
                    "lat": float(lat),
                    "lon": float(lon),
                    "ele": float(ele) if ele else 0.0,
                    "time": dt
                })

    points.sort(key=lambda x: x["time"])
    return points


def haversine_m(lat1, lon1, lat2, lon2):
    r = 6371000
    p1 = math.radians(lat1)
    p2 = math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)

    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return r * c


def enrich_points(points):
    total = 0.0

    for i, p in enumerate(points):
        if i == 0:
            p["dist_m"] = 0.0
            p["speed_kmh"] = 0.0
        else:
            prev = points[i - 1]
            d = haversine_m(prev["lat"], prev["lon"], p["lat"], p["lon"])
            dt = (p["time"] - prev["time"]).total_seconds()
            total += d
            p["dist_m"] = total
            p["speed_kmh"] = (d / dt) * 3.6 if dt > 0 else 0.0

    return points


def lerp(a, b, t):
    return a + ((b - a) * t)


def sample_at(points, target_time):
    if target_time <= points[0]["time"]:
        base = points[0].copy()
        base["gps_available"] = False
        return base

    if target_time >= points[-1]["time"]:
        base = points[-1].copy()
        base["gps_available"] = False
        return base

    for i in range(len(points) - 1):
        a = points[i]
        b = points[i + 1]

        if a["time"] <= target_time <= b["time"]:
            span = (b["time"] - a["time"]).total_seconds()
            ratio = 0 if span == 0 else (target_time - a["time"]).total_seconds() / span

            return {
                "lat": lerp(a["lat"], b["lat"], ratio),
                "lon": lerp(a["lon"], b["lon"], ratio),
                "ele": lerp(a["ele"], b["ele"], ratio),
                "dist_m": lerp(a["dist_m"], b["dist_m"], ratio),
                "speed_kmh": lerp(a["speed_kmh"], b["speed_kmh"], ratio),
                "time": target_time,
                "gps_available": True
            }

    base = points[-1].copy()
    base["gps_available"] = False
    return base


