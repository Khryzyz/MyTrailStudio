import csv
import math
import os
import shutil
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont

csv_path = r"J:\Fotos\ActionCamera\20260628_153709_overlay_1s.csv"
frames_dir = r"J:\Fotos\ActionCamera\overlay_frames_temaA_pulso_cierre_60_70_v2"

W, H = 2688, 1512
start_second = 60
duration_seconds = 10
fps = 10
total_frames = duration_seconds * fps
video_start_local = datetime(2026, 6, 28, 10, 37, 0)

M = 40
G = 35

if os.path.exists(frames_dir):
    shutil.rmtree(frames_dir)
os.makedirs(frames_dir, exist_ok=True)

def load_font(size):
    candidates = [
        r"J:\Fotos\ActionCamera\font\font.otf",
        r"C:\Windows\Fonts\bahnschrift.ttf",
        r"C:\Windows\Fonts\segoeui.ttf",
        r"C:\Windows\Fonts\arial.ttf",
        r"C:\Windows\Fonts\calibri.ttf"
    ]
    for p in candidates:
        try:
            return ImageFont.truetype(p, size)
        except:
            pass
    return ImageFont.load_default()

font_date = load_font(42)
font_time = load_font(64)
font_speed = load_font(70)
font_small = load_font(32)
font_mid = load_font(39)

rows = []
with open(csv_path, newline="", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    for r in reader:
        rows.append({
            "VideoSecond": float(r["VideoSecond"]),
            "Latitud": float(r["Latitud"]),
            "Longitud": float(r["Longitud"]),
            "Altitud": float(r["Altitud"]),
            "DistanciaAcumM": float(r["DistanciaAcumM"]),
            "VelocidadKmh": float(r["VelocidadKmh"]),
        })

rows = sorted(rows, key=lambda x: x["VideoSecond"])

min_alt = min(r["Altitud"] for r in rows)
max_alt = max(r["Altitud"] for r in rows)
max_dist = max(r["DistanciaAcumM"] for r in rows)

panel_fill = (5, 15, 12, 60)
text_main = (245, 255, 248, 255)
text_soft = (210, 245, 225, 235)
track_soft = (135, 210, 175, 180)
accent = (0, 255, 145, 255)
accent2 = (0, 210, 255, 255)

def lerp(a, b, t):
    return a + ((b - a) * t)

def sample_at(sec):
    if sec <= rows[0]["VideoSecond"]:
        return rows[0]
    if sec >= rows[-1]["VideoSecond"]:
        return rows[-1]

    for i in range(len(rows) - 1):
        if rows[i]["VideoSecond"] <= sec <= rows[i + 1]["VideoSecond"]:
            prev = rows[i]
            nxt = rows[i + 1]
            span = nxt["VideoSecond"] - prev["VideoSecond"]
            ratio = 0 if span == 0 else (sec - prev["VideoSecond"]) / span
            return {
                "VideoSecond": sec,
                "Latitud": lerp(prev["Latitud"], nxt["Latitud"], ratio),
                "Longitud": lerp(prev["Longitud"], nxt["Longitud"], ratio),
                "Altitud": lerp(prev["Altitud"], nxt["Altitud"], ratio),
                "DistanciaAcumM": lerp(prev["DistanciaAcumM"], nxt["DistanciaAcumM"], ratio),
                "VelocidadKmh": lerp(prev["VelocidadKmh"], nxt["VelocidadKmh"], ratio),
            }

    return rows[-1]

# Layout fijo
route_w = 600
route_h = 320
route_x = W - M - route_w
route_y = H - M - route_h

alt_w = 180
alt_x = route_x + route_w - alt_w
alt_y = M
alt_h = route_y - G - alt_y

bar_center_x = alt_x + (alt_w / 2)
bar_w = 45
bar_x1 = bar_center_x - (bar_w / 2)
bar_x2 = bar_center_x + (bar_w / 2)
bar_y1 = alt_y + 110
bar_y2 = alt_y + alt_h - 110

speed_panel_x = M
speed_panel_y = 165
speed_panel_w = 430
speed_panel_h = 340

dist_x = M
dist_h = 150
dist_y = H - M - dist_h
dist_right = route_x - G
dist_w = dist_right - dist_x

track_x1 = dist_x + 28
track_x2 = dist_x + dist_w - 28
track_y = dist_y + 105

# Ruta
pad = 35
lats = [r["Latitud"] for r in rows]
lons = [r["Longitud"] for r in rows]
min_lat, max_lat = min(lats), max(lats)
min_lon, max_lon = min(lons), max(lons)

def project(lat, lon):
    x = route_x + pad + ((lon - min_lon) / (max_lon - min_lon)) * (route_w - pad * 2)
    y = route_y + route_h - pad - ((lat - min_lat) / (max_lat - min_lat)) * (route_h - pad * 2)
    return x, y

route_points = [project(r["Latitud"], r["Longitud"]) for r in rows]

for frame in range(total_frames):
    sec = start_second + (frame / fps)
    current = sample_at(sec)

    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Fecha / Hora
    current_dt = video_start_local + timedelta(seconds=sec)
    draw.text((M, M), current_dt.strftime("%d/%m/%Y"), font=font_date, fill=text_main)
    draw.text((M, M + 44), current_dt.strftime("%H:%M"), font=font_time, fill=text_main)

    # Velocímetro
    draw.rounded_rectangle(
        [speed_panel_x, speed_panel_y, speed_panel_x + speed_panel_w, speed_panel_y + speed_panel_h],
        radius=28,
        fill=panel_fill
    )

    max_speed_scale = 8.0
    speed = current["VelocidadKmh"]
    speed_ratio = max(0.0, min(speed / max_speed_scale, 1.0))

    group_center_x = speed_panel_x + (speed_panel_w // 2)
    group_center_y = speed_panel_y + (speed_panel_h // 2)

    gauge_r = 110
    gauge_cx = group_center_x
    gauge_cy = group_center_y - 20

    bbox = [gauge_cx - gauge_r, gauge_cy - gauge_r, gauge_cx + gauge_r, gauge_cy + gauge_r]
    draw.arc(bbox, start=180, end=360, fill=track_soft, width=10)

    progress_end = 180 + (180 * speed_ratio)
    draw.arc(bbox, start=180, end=progress_end, fill=(0, 255, 145, 60), width=22)
    draw.arc(bbox, start=180, end=progress_end, fill=accent, width=10)

    needle_angle = 180 + (180 * speed_ratio)

    for i in range(0, 9):
        a = math.radians(180 + (180 * (i / 8)))
        x1 = gauge_cx + math.cos(a) * (gauge_r - 4)
        y1 = gauge_cy + math.sin(a) * (gauge_r - 4)
        x2 = gauge_cx + math.cos(a) * (gauge_r - 20)
        y2 = gauge_cy + math.sin(a) * (gauge_r - 20)
        draw.line((x1, y1, x2, y2), fill=(255,255,255,170), width=3)

    a = math.radians(needle_angle)
    nx = gauge_cx + math.cos(a) * (gauge_r - 28)
    ny = gauge_cy + math.sin(a) * (gauge_r - 28)
    draw.line((gauge_cx, gauge_cy, nx, ny), fill=(0, 210, 255, 80), width=17)
    draw.line((gauge_cx, gauge_cy, nx, ny), fill=accent2, width=7)
    draw.ellipse((gauge_cx-8, gauge_cy-8, gauge_cx+8, gauge_cy+8), fill=text_main)

    speed_text = f"{speed:.1f} km/h"
    speed_bbox = draw.textbbox((0,0), speed_text, font=font_speed)
    speed_w = speed_bbox[2] - speed_bbox[0]
    draw.text((gauge_cx - speed_w/2, gauge_cy + 60), speed_text, font=font_speed, fill=text_main)

    # Altitud
    draw.rounded_rectangle(
        [alt_x, alt_y, alt_x + alt_w, alt_y + alt_h],
        radius=28,
        fill=panel_fill
    )

    draw.rectangle([bar_x1, bar_y1, bar_x2, bar_y2], outline=text_soft, width=5)

    alt_ratio = 0 if max_alt == min_alt else (current["Altitud"] - min_alt) / (max_alt - min_alt)
    fill_y = bar_y2 - ((bar_y2 - bar_y1) * alt_ratio)
    draw.rectangle([bar_x1-3, fill_y-3, bar_x2+3, bar_y2+3], fill=(0, 255, 145, 55))
    draw.rectangle([bar_x1+4, fill_y, bar_x2-4, bar_y2-4], fill=accent)

    panel_center_x = alt_x + (alt_w / 2)

    cur_txt = f"{current['Altitud']:.0f} m"
    cur_bbox = draw.textbbox((0,0), cur_txt, font=font_mid)
    cur_w = cur_bbox[2] - cur_bbox[0]
    draw.text((panel_center_x - cur_w/2, alt_y + 20), cur_txt, font=font_mid, fill=text_main)

    max_txt = f"{max_alt:.0f} m"
    max_bbox = draw.textbbox((0,0), max_txt, font=font_small)
    max_w = max_bbox[2] - max_bbox[0]
    draw.text((panel_center_x - max_w/2, bar_y1 - 42), max_txt, font=font_small, fill=text_main)

    min_txt = f"{min_alt:.0f} m"
    min_bbox = draw.textbbox((0,0), min_txt, font=font_small)
    min_w = min_bbox[2] - min_bbox[0]
    draw.text((panel_center_x - min_w/2, bar_y2 + 12), min_txt, font=font_small, fill=text_main)

    # Distancia
    draw.rounded_rectangle(
        [dist_x, dist_y, dist_x + dist_w, dist_y + dist_h],
        radius=28,
        fill=panel_fill
    )

    draw.line((track_x1, track_y, track_x2, track_y), fill=track_soft, width=10)

    dist_ratio = 0 if max_dist == 0 else current["DistanciaAcumM"] / max_dist
    dot_x = track_x1 + ((track_x2 - track_x1) * dist_ratio)

    draw.line((track_x1, track_y, dot_x, track_y), fill=(0, 255, 145, 70), width=26)
    draw.line((track_x1, track_y, dot_x, track_y), fill=accent, width=12)
    draw.ellipse((dot_x-12, track_y-12, dot_x+12, track_y+12), fill=accent2)

    dist_text = f"{current['DistanciaAcumM']/1000:.2f} km"
    dist_bbox = draw.textbbox((0,0), dist_text, font=font_mid)
    dist_w_text = dist_bbox[2] - dist_bbox[0]
    draw.text((dist_x + (dist_w - dist_w_text)/2, dist_y + 20), dist_text, font=font_mid, fill=text_main)

    draw.text((dist_x + 28, dist_y + 62), "0.00 km", font=font_small, fill=text_main)

    max_txt2 = f"{(max_dist/1000):.2f} km"
    max_bbox2 = draw.textbbox((0,0), max_txt2, font=font_small)
    max_w2 = max_bbox2[2] - max_bbox2[0]
    draw.text((track_x2 - max_w2, dist_y + 62), max_txt2, font=font_small, fill=text_main)

    # Ruta
    draw.rounded_rectangle(
        [route_x, route_y, route_x + route_w, route_y + route_h],
        radius=28,
        fill=panel_fill
    )

    if len(route_points) > 1:
        draw.line(route_points, fill=(190,255,220,75), width=3)

    past_rows = [r for r in rows if r["VideoSecond"] <= sec]
    past_points = [project(r["Latitud"], r["Longitud"]) for r in past_rows]
    past_points.append(project(current["Latitud"], current["Longitud"]))

    if len(past_points) > 1:
        draw.line(past_points, fill=(0, 255, 145, 65), width=17)
        draw.line(past_points, fill=accent, width=7)

    px, py = project(current["Latitud"], current["Longitud"])
    pulse = (math.sin(frame * 0.35) + 1) / 2
    pulse_r = 16 + (pulse * 14)
    pulse_alpha = int(90 - (pulse * 50))

    draw.ellipse(
        (px-pulse_r, py-pulse_r, px+pulse_r, py+pulse_r),
        fill=(0, 255, 145, pulse_alpha)
    )

    draw.ellipse((px-14, py-14, px+14, py+14), fill=(0, 255, 145, 95))
    draw.ellipse((px-8, py-8, px+8, py+8), fill=accent2)

    out = os.path.join(frames_dir, f"frame_{frame:05d}.png")
    img.save(out)

closing_image_path = r"J:\Fotos\ActionCamera\preview_cierre_ruta_tema_A.png"

for cierre_frame in range(70, 100):
    cierre = Image.new("RGBA", (W, H), (0, 0, 0, 255))

    if os.path.exists(closing_image_path):
        cierre_src = Image.open(closing_image_path).convert("RGBA")
        ow, oh = cierre_src.size
        scale = min(W / ow, H / oh)
        nw = int(ow * scale)
        nh = int(oh * scale)
        cierre_src = cierre_src.resize((nw, nh), Image.LANCZOS)
        x = (W - nw) // 2
        y = (H - nh) // 2
        cierre.paste(cierre_src, (x, y), cierre_src)

    cierre.save(os.path.join(frames_dir, f"frame_{cierre_frame:05d}.png"))
print("Frames creados:", total_frames)
print("Carpeta:", frames_dir)



