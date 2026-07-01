from PIL import Image, ImageDraw, ImageFont

out_path = r"J:\Fotos\DJI\preview_cierre_ruta_tema_A.png"

W, H = 1920, 1080

titulo = "Ruta Finalizada"
subtitulo = "Paramo de Arabia"

distancia_total = "5.80 km"
altura_maxima = "2,828 m"
duracion = "5 h 43 min"
fecha = "28/06/2026"

def load_font(size):
    candidates = [
        r"J:\Fotos\DJI\font\font.otf",
        r"C:\Windows\Fonts\bahnschrift.ttf",
        r"C:\Windows\Fonts\segoeui.ttf",
        r"C:\Windows\Fonts\arial.ttf",
        r"C:\Windows\Fonts\calibri.ttf",
    ]
    for p in candidates:
        try:
            return ImageFont.truetype(p, size)
        except:
            pass
    return ImageFont.load_default()

font_title = load_font(82)
font_sub = load_font(44)
font_label = load_font(34)
font_value = load_font(54)
font_footer = load_font(30)

img = Image.new("RGBA", (W, H), (0, 0, 0, 255))
draw = ImageDraw.Draw(img)

panel_fill = (5, 15, 12, 210)
card_fill = (5, 15, 12, 165)
text_main = (245, 255, 248, 255)
text_soft = (210, 245, 225, 235)
accent = (0, 255, 145, 255)
accent_glow = (0, 255, 145, 55)
accent2 = (0, 210, 255, 255)

# Marco principal
panel = [140, 120, W - 140, H - 120]
draw.rounded_rectangle(panel, radius=46, fill=panel_fill)

# Línea/acento superior con glow
line_y = 175
draw.line((520, line_y, W - 520, line_y), fill=accent_glow, width=22)
draw.line((560, line_y, W - 560, line_y), fill=accent, width=6)

# Título
title_bbox = draw.textbbox((0, 0), titulo, font=font_title)
title_w = title_bbox[2] - title_bbox[0]
draw.text(((W - title_w) / 2, 225), titulo, font=font_title, fill=text_main)

# Subtítulo
sub_bbox = draw.textbbox((0, 0), subtitulo, font=font_sub)
sub_w = sub_bbox[2] - sub_bbox[0]
draw.text(((W - sub_w) / 2, 325), subtitulo, font=font_sub, fill=text_soft)

# Tarjetas
cards_y = 465
card_w = 460
card_h = 190
gap = 45
total_w = card_w * 3 + gap * 2
start_x = (W - total_w) / 2

cards = [
    ("Distancia total", distancia_total),
    ("Altura maxima", altura_maxima),
    ("Duracion", duracion),
]

for i, (label, value) in enumerate(cards):
    x1 = start_x + i * (card_w + gap)
    y1 = cards_y
    x2 = x1 + card_w
    y2 = y1 + card_h

    draw.rounded_rectangle(
        [x1-4, y1-4, x2+4, y2+4],
        radius=32,
        fill=accent_glow
    )

    draw.rounded_rectangle(
        [x1, y1, x2, y2],
        radius=28,
        fill=card_fill
    )

    label_bbox = draw.textbbox((0, 0), label, font=font_label)
    label_w = label_bbox[2] - label_bbox[0]
    draw.text((x1 + (card_w - label_w) / 2, y1 + 36), label, font=font_label, fill=text_soft)

    value_bbox = draw.textbbox((0, 0), value, font=font_value)
    value_w = value_bbox[2] - value_bbox[0]
    draw.text((x1 + (card_w - value_w) / 2, y1 + 98), value, font=font_value, fill=text_main)

# Punto decorativo inferior
dot_x = W / 2
dot_y = 765
draw.ellipse((dot_x-18, dot_y-18, dot_x+18, dot_y+18), fill=(0, 255, 145, 60))
draw.ellipse((dot_x-9, dot_y-9, dot_x+9, dot_y+9), fill=accent2)

# Footer
footer_text = f"Fecha: {fecha}"
footer_bbox = draw.textbbox((0, 0), footer_text, font=font_footer)
footer_w = footer_bbox[2] - footer_bbox[0]
draw.text(((W - footer_w) / 2, 835), footer_text, font=font_footer, fill=text_soft)

img.save(out_path)
print("Imagen creada:", out_path)
