import csv
import math
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont

csv_path = r"J:\Fotos\DJI\20260628_153709_overlay_1s.csv"
out_path = r"J:\Fotos\DJI\overlay_preview_gps_no_disponible.png"

W, H = 2688, 1512
target_second = 60
video_start_local = datetime(2026, 6, 28, 10, 37, 0)

# ===== Layout base =====
M = 40   # margen uniforme contra borde
G = 35   # separación uniforme entre paneles

def load_font(size):
    candidates = [
        r"C:\Windows\Fonts\arial.ttf",
        r"C:\Windows\Fonts\segoeui.ttf",
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
font_gps = load_font(34)
font_speed = load_font(70)
font_small = load_font(32)
font_mid = load_font(39)

rows = []
with open(csv_path, newline="", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    for r in reader:
        rows.append({
            "VideoSecond": int(float(r["VideoSecond"])),
            "Latitud": float(r["Latitud"]),
            "Longitud": float(r["Longitud"]),
            "Altitud": float(r["Altitud"]),
            "DistanciaAcumM": float(r["DistanciaAcumM"]),
            "VelocidadKmh": float(r["VelocidadKmh"]),
        })

current = rows[target_second]

min_alt = min(r["Altitud"] for r in rows)
max_alt = max(r["Altitud"] for r in rows)
max_dist = max(r["DistanciaAcumM"] for r in rows)

img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)

panel_fill = (0, 0, 0, 110)
text_main = (255, 255, 255, 255)
text_soft = (255, 255, 255, 230)
track_soft = (255, 255, 255, 180)
accent = (0, 220, 255, 255)
accent2 = (255, 80, 80, 255)

# ===== Fecha / Hora =====
current_dt = video_start_local + timedelta(seconds=target_second)
fecha_txt = current_dt.strftime("%d/%m/%Y")
hora_txt = current_dt.strftime("%H:%M")

date_x = M
date_y = M
draw.text((date_x, date_y), fecha_txt, font=font_date, fill=text_main)
draw.text((date_x, date_y + 44), hora_txt, font=font_time, fill=text_main)

# ===== Ruta =====
route_w = 600
route_h = 320
route_x = W - M - route_w
route_y = H - M - route_h

draw.rounded_rectangle(
    [route_x, route_y, route_x + route_w, route_y + route_h],
    radius=28,
    fill=panel_fill
)

# ===== Altitud: ocupa todo el lado derecho =====
alt_w = 180
alt_x = route_x + route_w - alt_w
alt_y = M
alt_h = route_y - G - alt_y

draw.rounded_rectangle(
    [alt_x, alt_y, alt_x + alt_w, alt_y + alt_h],
    radius=28,
    fill=panel_fill
)

bar_center_x = alt_x + (alt_w / 2)
bar_w = 45
bar_x1 = bar_center_x - (bar_w / 2)
bar_x2 = bar_center_x + (bar_w / 2)
bar_y1 = alt_y + 110
bar_y2 = alt_y + alt_h - 110

draw.rectangle([bar_x1, bar_y1, bar_x2, bar_y2], outline=text_soft, width=5)

alt_ratio = 0 if max_alt == min_alt else (current["Altitud"] - min_alt) / (max_alt - min_alt)
fill_y = bar_y2 - ((bar_y2 - bar_y1) * alt_ratio)
draw.rectangle([bar_x1+4, fill_y, bar_x2-4, bar_y2-4], fill=accent)

# labels de altitud: todo centrado sobre el mismo eje horizontal
max_txt = f"{max_alt:.0f}"
min_txt = f"{min_alt:.0f}"
cur_txt = f"{current['Altitud']:.0f} m"

panel_center_x = alt_x + (alt_w / 2)

cur_bbox = draw.textbbox((0,0), cur_txt, font=font_mid)
cur_w = cur_bbox[2] - cur_bbox[0]
draw.text((panel_center_x - cur_w/2, alt_y + 20), cur_txt, font=font_mid, fill=text_main)

max_bbox = draw.textbbox((0,0), max_txt, font=font_small)
max_w = max_bbox[2] - max_bbox[0]
draw.text((panel_center_x - max_w/2, bar_y1 - 42), max_txt, font=font_small, fill=text_main)

min_bbox = draw.textbbox((0,0), min_txt, font=font_small)
min_w = min_bbox[2] - min_bbox[0]
draw.text((panel_center_x - min_w/2, bar_y2 + 12), min_txt, font=font_small, fill=text_main)

# ===== Panel velocímetro compacto, centrado como un solo bloque =====
speed_panel_x = M
speed_panel_y = 165
speed_panel_w = 430
speed_panel_h = 340

draw.rounded_rectangle(
    [speed_panel_x, speed_panel_y, speed_panel_x + speed_panel_w, speed_panel_y + speed_panel_h],
    radius=28,
    fill=panel_fill
)

max_speed_scale = 8.0
speed = current["VelocidadKmh"]
speed_ratio = max(0.0, min(speed / max_speed_scale, 1.0))

# grupo completo: velocímetro + label
group_center_x = speed_panel_x + (speed_panel_w // 2)
group_center_y = speed_panel_y + (speed_panel_h // 2)

gauge_r = 110
gauge_cx = group_center_x
gauge_cy = group_center_y - 20

bbox = [gauge_cx - gauge_r, gauge_cy - gauge_r, gauge_cx + gauge_r, gauge_cy + gauge_r]
draw.arc(bbox, start=180, end=360, fill=track_soft, width=10)

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
draw.line((gauge_cx, gauge_cy, nx, ny), fill=accent2, width=7)
draw.ellipse((gauge_cx-8, gauge_cy-8, gauge_cx+8, gauge_cy+8), fill=text_main)

speed_text = f"{speed:.1f} km/h"
speed_bbox = draw.textbbox((0,0), speed_text, font=font_speed)
speed_w = speed_bbox[2] - speed_bbox[0]

label_y = gauge_cy + 60
draw.text((gauge_cx - speed_w/2, label_y), speed_text, font=font_speed, fill=text_main)
# ===== Distancia =====
dist_x = M
dist_h = 150
dist_y = H - M - dist_h
dist_right = route_x - G
dist_w = dist_right - dist_x

draw.rounded_rectangle(
    [dist_x, dist_y, dist_x + dist_w, dist_y + dist_h],
    radius=28,
    fill=panel_fill
)

track_x1 = dist_x + 28
track_x2 = dist_x + dist_w - 28
track_y = dist_y + 105

draw.line((track_x1, track_y, track_x2, track_y), fill=track_soft, width=10)

dist_ratio = 0 if max_dist == 0 else current["DistanciaAcumM"] / max_dist
dot_x = track_x1 + ((track_x2 - track_x1) * dist_ratio)

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

# ===== Ruta dibujo =====
pad = 35
lats = [r["Latitud"] for r in rows]
lons = [r["Longitud"] for r in rows]
min_lat, max_lat2 = min(lats), max(lats)
min_lon, max_lon = min(lons), max(lons)

def project(lat, lon):
    x = route_x + pad + ((lon - min_lon) / (max_lon - min_lon)) * (route_w - pad * 2)
    y = route_y + route_h - pad - ((lat - min_lat) / (max_lat2 - min_lat)) * (route_h - pad * 2)
    return x, y

points = [project(r["Latitud"], r["Longitud"]) for r in rows]
if len(points) > 1:
    draw.line(points, fill=(255,255,255,120), width=4)

past = [project(r["Latitud"], r["Longitud"]) for r in rows if r["VideoSecond"] <= target_second]
if len(past) > 1:
    draw.line(past, fill=accent, width=7)

px, py = project(current["Latitud"], current["Longitud"])
draw.ellipse((px-11, py-11, px+11, py+11), fill=accent2)

# Mensaje GPS no disponible, dibujado encima de todo
gps_msg = "GPS no disponible"
gps_bbox = draw.textbbox((0,0), gps_msg, font=font_gps)
gps_w = gps_bbox[2] - gps_bbox[0]

gps_x = (W - (gps_w + 34)) / 2
gps_y = M

draw.rounded_rectangle(
    [gps_x, gps_y, gps_x + gps_w + 34, gps_y + 50],
    radius=18,
    fill=(0, 0, 0, 170)
)
draw.text((gps_x + 17, gps_y + 7), gps_msg, font=font_gps, fill=(255, 210, 90, 255))
img.save(out_path)
print("Imagen creada:", out_path)












