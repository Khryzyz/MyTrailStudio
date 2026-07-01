import math
from datetime import timedelta, timezone
from PIL import Image, ImageDraw

from utils import load_font


def text_center(draw, box_x, box_w, y, text, font, fill):
    bbox = draw.textbbox((0,0), text, font=font)
    tw = bbox[2] - bbox[0]
    draw.text((box_x + (box_w - tw) / 2, y), text, font=font, fill=fill)


def build_overlay_context(W, H, gpx_points, font_path):
    font_date = load_font(font_path, 42)
    font_time = load_font(font_path, 64)
    font_speed = load_font(font_path, 70)
    font_small = load_font(font_path, 32)
    font_mid = load_font(font_path, 39)
    font_gps = load_font(font_path, 34)

    M = 40
    G = 35

    panel_fill = (5, 15, 12, 60)
    text_main = (245, 255, 248, 255)
    text_soft = (210, 245, 225, 235)
    track_soft = (135, 210, 175, 180)
    accent = (0, 255, 145, 255)
    accent2 = (0, 210, 255, 255)

    min_alt = min(p["ele"] for p in gpx_points)
    max_alt = max(p["ele"] for p in gpx_points)
    max_dist = max(p["dist_m"] for p in gpx_points)

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

    pad = 35
    lats = [p["lat"] for p in gpx_points]
    lons = [p["lon"] for p in gpx_points]
    min_lat, max_lat = min(lats), max(lats)
    min_lon, max_lon = min(lons), max(lons)

    def project(lat, lon):
        x = route_x + pad + ((lon - min_lon) / (max_lon - min_lon)) * (route_w - pad * 2)
        y = route_y + route_h - pad - ((lat - min_lat) / (max_lat - min_lat)) * (route_h - pad * 2)
        return x, y

    route_points = [project(p["lat"], p["lon"]) for p in gpx_points]

    return {
        "font_date": font_date,
        "font_time": font_time,
        "font_speed": font_speed,
        "font_small": font_small,
        "font_mid": font_mid,
        "font_gps": font_gps,
        "M": M,
        "panel_fill": panel_fill,
        "text_main": text_main,
        "text_soft": text_soft,
        "track_soft": track_soft,
        "accent": accent,
        "accent2": accent2,
        "min_alt": min_alt,
        "max_alt": max_alt,
        "max_dist": max_dist,
        "route_w": route_w,
        "route_h": route_h,
        "route_x": route_x,
        "route_y": route_y,
        "alt_w": alt_w,
        "alt_x": alt_x,
        "alt_y": alt_y,
        "alt_h": alt_h,
        "bar_x1": bar_x1,
        "bar_x2": bar_x2,
        "bar_y1": bar_y1,
        "bar_y2": bar_y2,
        "speed_panel_x": speed_panel_x,
        "speed_panel_y": speed_panel_y,
        "speed_panel_w": speed_panel_w,
        "speed_panel_h": speed_panel_h,
        "dist_x": dist_x,
        "dist_y": dist_y,
        "dist_w": dist_w,
        "dist_h": dist_h,
        "track_x1": track_x1,
        "track_x2": track_x2,
        "track_y": track_y,
        "project": project,
        "route_points": route_points
    }


def render_overlay_frame(W, H, config, gpx_points, current_time, current, frame, context):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    font_date = context["font_date"]
    font_time = context["font_time"]
    font_speed = context["font_speed"]
    font_small = context["font_small"]
    font_mid = context["font_mid"]
    font_gps = context["font_gps"]

    M = context["M"]

    panel_fill = context["panel_fill"]
    text_main = context["text_main"]
    text_soft = context["text_soft"]
    track_soft = context["track_soft"]
    accent = context["accent"]
    accent2 = context["accent2"]

    min_alt = context["min_alt"]
    max_alt = context["max_alt"]
    max_dist = context["max_dist"]

    route_w = context["route_w"]
    route_h = context["route_h"]
    route_x = context["route_x"]
    route_y = context["route_y"]

    alt_w = context["alt_w"]
    alt_x = context["alt_x"]
    alt_y = context["alt_y"]
    alt_h = context["alt_h"]

    bar_x1 = context["bar_x1"]
    bar_x2 = context["bar_x2"]
    bar_y1 = context["bar_y1"]
    bar_y2 = context["bar_y2"]

    speed_panel_x = context["speed_panel_x"]
    speed_panel_y = context["speed_panel_y"]
    speed_panel_w = context["speed_panel_w"]
    speed_panel_h = context["speed_panel_h"]

    dist_x = context["dist_x"]
    dist_y = context["dist_y"]
    dist_w = context["dist_w"]
    dist_h = context["dist_h"]

    track_x1 = context["track_x1"]
    track_x2 = context["track_x2"]
    track_y = context["track_y"]

    project = context["project"]
    route_points = context["route_points"]

    current_local = current_time.astimezone(timezone(timedelta(hours=-5)))
    fecha_txt = current_local.strftime("%d/%m/%Y")
    hora_txt = current_local.strftime("%H:%M")

    draw.text((M, M), fecha_txt, font=font_date, fill=text_main, stroke_width=3, stroke_fill=(0,0,0,255))
    draw.text((M, M + 44), hora_txt, font=font_time, fill=text_main, stroke_width=3, stroke_fill=(0,0,0,255))

    if not current["gps_available"] and config["setting"]["layout"]["show_gps_unavailable"]:
        gps_msg = "GPS no disponible"
        gps_bbox = draw.textbbox((0,0), gps_msg, font=font_gps)
        gps_w = gps_bbox[2] - gps_bbox[0]
        gps_x = (W - (gps_w + 34)) / 2
        gps_y = M
        draw.rounded_rectangle([gps_x, gps_y, gps_x + gps_w + 34, gps_y + 50], radius=18, fill=(0,0,0,170))
        draw.text((gps_x + 17, gps_y + 7), gps_msg, font=font_gps, fill=(255,210,90,255))

    # Velocimetro
    draw.rounded_rectangle([speed_panel_x, speed_panel_y, speed_panel_x + speed_panel_w, speed_panel_y + speed_panel_h], radius=28, fill=panel_fill)

    max_speed_scale = 8.0
    speed = current["speed_kmh"]
    speed_ratio = max(0.0, min(speed / max_speed_scale, 1.0))

    gauge_cx = speed_panel_x + (speed_panel_w // 2)
    gauge_cy = speed_panel_y + (speed_panel_h // 2) - 20
    gauge_r = 110

    bbox = [gauge_cx - gauge_r, gauge_cy - gauge_r, gauge_cx + gauge_r, gauge_cy + gauge_r]
    draw.arc(bbox, start=180, end=360, fill=track_soft, width=10)

    progress_end = 180 + (180 * speed_ratio)
    draw.arc(bbox, start=180, end=progress_end, fill=(0,255,145,60), width=22)
    draw.arc(bbox, start=180, end=progress_end, fill=accent, width=10)

    for i in range(0, 9):
        a = math.radians(180 + (180 * (i / 8)))
        x1 = gauge_cx + math.cos(a) * (gauge_r - 4)
        y1 = gauge_cy + math.sin(a) * (gauge_r - 4)
        x2 = gauge_cx + math.cos(a) * (gauge_r - 20)
        y2 = gauge_cy + math.sin(a) * (gauge_r - 20)
        draw.line((x1, y1, x2, y2), fill=(255,255,255,170), width=3)

    needle_angle = 180 + (180 * speed_ratio)
    a = math.radians(needle_angle)
    nx = gauge_cx + math.cos(a) * (gauge_r - 28)
    ny = gauge_cy + math.sin(a) * (gauge_r - 28)
    draw.line((gauge_cx, gauge_cy, nx, ny), fill=(0,210,255,80), width=17)
    draw.line((gauge_cx, gauge_cy, nx, ny), fill=accent2, width=7)
    draw.ellipse((gauge_cx-8, gauge_cy-8, gauge_cx+8, gauge_cy+8), fill=text_main)

    speed_text = f"{speed:.1f} km/h"
    speed_bbox = draw.textbbox((0,0), speed_text, font=font_speed)
    speed_w = speed_bbox[2] - speed_bbox[0]
    draw.text((gauge_cx - speed_w/2, gauge_cy + 60), speed_text, font=font_speed, fill=text_main)

    # Altitud
    draw.rounded_rectangle([alt_x, alt_y, alt_x + alt_w, alt_y + alt_h], radius=28, fill=panel_fill)
    draw.rectangle([bar_x1, bar_y1, bar_x2, bar_y2], outline=text_soft, width=5)

    alt_ratio = 0 if max_alt == min_alt else (current["ele"] - min_alt) / (max_alt - min_alt)
    fill_y = bar_y2 - ((bar_y2 - bar_y1) * alt_ratio)

    draw.rectangle([bar_x1-3, fill_y-3, bar_x2+3, bar_y2+3], fill=(0,255,145,55))
    draw.rectangle([bar_x1+4, fill_y, bar_x2-4, bar_y2-4], fill=accent)

    panel_center_x = alt_x + (alt_w / 2)

    cur_txt = f"{current['ele']:.0f} m"
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
    draw.rounded_rectangle([dist_x, dist_y, dist_x + dist_w, dist_y + dist_h], radius=28, fill=panel_fill)
    draw.line((track_x1, track_y, track_x2, track_y), fill=track_soft, width=10)

    dist_ratio = 0 if max_dist == 0 else current["dist_m"] / max_dist
    dot_x = track_x1 + ((track_x2 - track_x1) * dist_ratio)

    draw.line((track_x1, track_y, dot_x, track_y), fill=(0,255,145,70), width=26)
    draw.line((track_x1, track_y, dot_x, track_y), fill=accent, width=12)
    draw.ellipse((dot_x-12, track_y-12, dot_x+12, track_y+12), fill=accent2)

    dist_text = f"{current['dist_m']/1000:.2f} km"
    dist_bbox = draw.textbbox((0,0), dist_text, font=font_mid)
    dist_w_text = dist_bbox[2] - dist_bbox[0]
    draw.text((dist_x + (dist_w - dist_w_text)/2, dist_y + 20), dist_text, font=font_mid, fill=text_main)

    draw.text((dist_x + 28, dist_y + 62), "0.00 km", font=font_small, fill=text_main)

    max_txt2 = f"{(max_dist/1000):.2f} km"
    max_bbox2 = draw.textbbox((0,0), max_txt2, font=font_small)
    max_w2 = max_bbox2[2] - max_bbox2[0]
    draw.text((track_x2 - max_w2, dist_y + 62), max_txt2, font=font_small, fill=text_main)

    # Mapa
    draw.rounded_rectangle([route_x, route_y, route_x + route_w, route_y + route_h], radius=28, fill=panel_fill)

    if len(route_points) > 1:
        draw.line(route_points, fill=(190,255,220,75), width=3)

    past_points = [project(p["lat"], p["lon"]) for p in gpx_points if p["time"] <= current_time]
    past_points.append(project(current["lat"], current["lon"]))

    if len(past_points) > 1:
        draw.line(past_points, fill=(0,255,145,65), width=17)
        draw.line(past_points, fill=accent, width=7)

    px, py = project(current["lat"], current["lon"])

    if config["setting"]["layout"]["pulse_map_point"]:
        pulse = (math.sin(frame * 0.35) + 1) / 2
        pulse_r = 16 + (pulse * 14)
        pulse_alpha = int(90 - (pulse * 50))
        draw.ellipse((px-pulse_r, py-pulse_r, px+pulse_r, py+pulse_r), fill=(0,255,145,pulse_alpha))

    draw.ellipse((px-14, py-14, px+14, py+14), fill=(0,255,145,95))
    draw.ellipse((px-8, py-8, px+8, py+8), fill=accent2)

    return img


def render_closing_frame(W, H, config, route_name, stats, font_path):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    draw = ImageDraw.Draw(img)

    font_title = load_font(font_path, 92)
    font_sub = load_font(font_path, 48)
    font_label = load_font(font_path, 38)
    font_value = load_font(font_path, 58)
    font_footer = load_font(font_path, 32)

    panel_fill = (5, 15, 12, 230)
    card_fill = (5, 15, 12, 180)
    text_main = (245, 255, 248, 255)
    text_soft = (210, 245, 225, 235)
    accent = (0, 255, 145, 255)
    accent_glow = (0, 255, 145, 55)
    accent2 = (0, 210, 255, 255)

    msg = config["output"]["closing_screen"]["message"] or "Ruta Finalizada"

    panel = [int(W * 0.075), int(H * 0.11), int(W * 0.925), int(H * 0.89)]
    draw.rounded_rectangle(panel, radius=46, fill=panel_fill)

    line_y = int(H * 0.17)
    draw.line((int(W * 0.28), line_y, int(W * 0.72), line_y), fill=accent_glow, width=22)
    draw.line((int(W * 0.30), line_y, int(W * 0.70), line_y), fill=accent, width=6)

    title_bbox = draw.textbbox((0, 0), msg, font=font_title)
    title_w = title_bbox[2] - title_bbox[0]
    draw.text(((W - title_w) / 2, int(H * 0.22)), msg, font=font_title, fill=text_main)

    subtitle = route_name or "Ruta"
    sub_bbox = draw.textbbox((0, 0), subtitle, font=font_sub)
    sub_w = sub_bbox[2] - sub_bbox[0]
    draw.text(((W - sub_w) / 2, int(H * 0.32)), subtitle, font=font_sub, fill=text_soft)

    cards = [
        ("Distancia total", f"{stats['dist_km']:.2f} km"),
        ("Altura maxima", f"{stats['max_alt']:.0f} m"),
        ("Duracion", stats["duration_text"]),
    ]

    card_w = int(W * 0.24)
    card_h = int(H * 0.17)
    gap = int(W * 0.025)
    total_w = card_w * 3 + gap * 2
    start_x = (W - total_w) / 2
    cards_y = int(H * 0.46)

    for i, (label, value) in enumerate(cards):
        x1 = start_x + i * (card_w + gap)
        y1 = cards_y
        x2 = x1 + card_w
        y2 = y1 + card_h

        draw.rounded_rectangle([x1-4, y1-4, x2+4, y2+4], radius=32, fill=accent_glow)
        draw.rounded_rectangle([x1, y1, x2, y2], radius=28, fill=card_fill)

        text_center(draw, x1, card_w, y1 + int(card_h * 0.20), label, font_label, text_soft)
        text_center(draw, x1, card_w, y1 + int(card_h * 0.52), value, font_value, text_main)

    dot_x = W / 2
    dot_y = int(H * 0.76)
    draw.ellipse((dot_x-18, dot_y-18, dot_x+18, dot_y+18), fill=(0, 255, 145, 60))
    draw.ellipse((dot_x-9, dot_y-9, dot_x+9, dot_y+9), fill=accent2)

    footer_text = f"Fecha: {stats['date_text']}"
    footer_bbox = draw.textbbox((0, 0), footer_text, font=font_footer)
    footer_w = footer_bbox[2] - footer_bbox[0]
    draw.text(((W - footer_w) / 2, int(H * 0.84)), footer_text, font=font_footer, fill=text_soft)

    return img
