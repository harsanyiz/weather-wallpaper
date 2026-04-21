#!/usr/bin/env python3
import os
import sys
import time
import json
import math
import requests
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageStat

GITHUB_USER = "harsanyiz"
GITHUB_REPO = "weather-wallpaper"
BRANCH = "main"
BASE_URL = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/{BRANCH}"

# ============================================================
# KONFIGURÁCIÓ
# ============================================================
WIDGET_WIDTH  = 2200
WIDGET_HEIGHT = 220
WIDGET_Y      = 80
OFFSET_LEFT   = 135
INNER_MARGIN  = 80

FONT_TEMP   = 90
FONT_DESC   = 32
FONT_LABEL  = 28
FONT_VALUE  = 36
FONT_UPDATE = 24
FONT_SUN    = 22

ICON_SIZE = 80  # px – 512x512 PNG → 80x80
# ============================================================

print("=== TEST_OVERFLIGHT INDÍTÁSA ===")

os.makedirs("images", exist_ok=True)

# ----------------------------------------------------------------
# SEGÉDFÜGGVÉNYEK
# ----------------------------------------------------------------
def find_font(bold=False):
    paths = [
        "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf"    if bold else "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for p in paths:
        if os.path.exists(p): return p
    return None

def get_f(size, bold=False):
    p = find_font(bold)
    if p: return ImageFont.truetype(p, size)
    return ImageFont.load_default()

def get_text_colors(brightness):
    if brightness > 145:
        return {"main": (0,0,0,230), "dim": (0,0,0,140), "line": (0,0,0)}
    return {"main": (255,255,255,255), "dim": (255,255,255,160), "line": (255,255,255)}

def draw_glass_bar(img, bx, by, bw, bh):
    region  = img.crop((bx, by, bx+bw, by+bh))
    blurred = region.filter(ImageFilter.GaussianBlur(30))
    mask    = Image.new("L", (bw, bh), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, bw, bh), radius=30, fill=180)
    overlay = Image.new("RGBA", (bw, bh), (0, 0, 10, 100))
    blurred = blurred.convert("RGBA")
    blurred.putalpha(mask)
    result  = Image.alpha_composite(blurred, overlay)
    img.paste(result, (bx, by), result)
    return img

def draw_separator(img, x, y_top, y_bot, color_rgb, max_alpha=160, gap=4):
    """Penge-szerű gradiens elválasztó – szinuszos alpha, dupla vonal."""
    height = y_bot - y_top
    pixels = img.load()
    iw, ih = img.size
    for i in range(height):
        alpha = int(math.sin(i / height * math.pi) * max_alpha)
        r, g, b = color_rgb
        for dx in (0, gap):
            px = x + dx
            if 0 <= px < iw and 0 <= y_top + i < ih:
                br, bg, bb, ba = img.getpixel((px, y_top + i))
                a = alpha / 255.0
                pixels[px, y_top + i] = (
                    int(br*(1-a) + r*a),
                    int(bg*(1-a) + g*a),
                    int(bb*(1-a) + b*a),
                    ba
                )

def load_icon(name):
    """PNG ikon letöltése a repóból – már 80x80 RGBA, nincs resize."""
    url = f"{BASE_URL}/images/PNG/{name}.png"
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        icon = Image.open(BytesIO(r.content)).convert("RGBA")
        print(f"✓ Ikon betöltve: {name}.png ({icon.size[0]}x{icon.size[1]})")
        return icon
    except Exception as e:
        print(f"✗ Ikon hiba ({name}): {e}")
        return None

def paste_icon(img, icon, cx, cy):
    """Ikon beillesztése – cx/cy a középpont."""
    if icon is None:
        return
    x = cx - ICON_SIZE // 2
    y = cy - ICON_SIZE // 2
    img.paste(icon, (x, y), icon)

# ----------------------------------------------------------------
# HÁTTÉR – sötétkék gradiens tesztkép
# ----------------------------------------------------------------
width, height = 3840, 2160
img = Image.new("RGB", (width, height), (15, 25, 45))
draw_bg = ImageDraw.Draw(img)
for y in range(height):
    t = y / height
    draw_bg.line([(0, y), (width, y)], fill=(
        int(15 + t*10), int(25 + t*15), int(45 + t*30)
    ))
print("✓ Háttér generálva")

# ----------------------------------------------------------------
# IKON BETÖLTÉSE
# ----------------------------------------------------------------
icon_cloudy = load_icon("cloudy")

# ----------------------------------------------------------------
# GLASS BAR
# ----------------------------------------------------------------
bx = OFFSET_LEFT
by = WIDGET_Y
bw = WIDGET_WIDTH
bh = WIDGET_HEIGHT

img = img.convert("RGBA")
img = draw_glass_bar(img, bx, by, bw, bh)

region = img.crop((bx, by, bx+bw, by+bh)).convert("L")
colors = get_text_colors(ImageStat.Stat(region).mean[0])

draw = ImageDraw.Draw(img)
f_t  = get_f(FONT_TEMP,   True)
f_d  = get_f(FONT_DESC)
f_l  = get_f(FONT_LABEL)
f_v  = get_f(FONT_VALUE,  True)
f_u  = get_f(FONT_UPDATE)
f_s  = get_f(FONT_SUN)

curr_x = int(bx + INNER_MARGIN)
mid_y  = int(by + bh // 2)

sep_color = colors["line"]
def sep():
    global curr_x
    draw_separator(img, curr_x, by+20, by+bh-20, sep_color, max_alpha=160, gap=4)
    curr_x += 40

# ----------------------------------------------------------------
# 1. SZEKCIÓ – NAP + HŐMÉRSÉKLET + IKON + LEÍRÁS
# ----------------------------------------------------------------
day_txt  = "KEDD"
temp_txt = "9°C"
desc_txt = "RÉSZBEN FELHŐS"

day_w  = draw.textbbox((0,0), day_txt,  font=f_l)[2]
temp_w = draw.textbbox((0,0), temp_txt, font=f_t)[2]
desc_w = draw.textbbox((0,0), desc_txt, font=f_d)[2]
max_w  = max(day_w, temp_w, desc_w)

draw.text((int(curr_x + (max_w-day_w)  / 2), int(mid_y - 90)), day_txt,  font=f_l, fill=colors["dim"])
draw.text((int(curr_x + (max_w-temp_w) / 2), int(mid_y - 62)), temp_txt, font=f_t, fill=colors["main"])
draw.text((int(curr_x + (max_w-desc_w) / 2), int(mid_y + 38)), desc_txt, font=f_d, fill=colors["dim"])

# Ikon: hőfok jobb oldalán, függőlegesen középre
icon_x = int(curr_x + max_w + 30 + ICON_SIZE // 2)
paste_icon(img, icon_cloudy, icon_x, mid_y - 10)
curr_x += int(max_w + 30 + ICON_SIZE + 30)
sep()

# ----------------------------------------------------------------
# 2. SZEKCIÓ – ÉRZET / SZÉL / PÁRA
# ----------------------------------------------------------------
fields = [("Érzet", "7°C"), ("Szél", "16 km/h"), ("Pára", "67%")]
for label, val in fields:
    lw = draw.textbbox((0,0), label.upper(), font=f_l)[2]
    vw = draw.textbbox((0,0), val,           font=f_v)[2]
    draw.text((curr_x, int(mid_y - 48)), label.upper(), font=f_l, fill=colors["dim"])
    draw.text((curr_x, int(mid_y + 2)),  val,           font=f_v, fill=colors["main"])
    curr_x += max(lw, vw) + 70
sep()

# ----------------------------------------------------------------
# 3. SZEKCIÓ – NAPKELTE / NAPNYUGTA
# ----------------------------------------------------------------
sun_label = "NAPKELTE / NAPNYUGTA"
sun_val   = "05:44  •  19:40"
slw = draw.textbbox((0,0), sun_label, font=f_s)[2]
svw = draw.textbbox((0,0), sun_val,   font=f_v)[2]
col_w = max(slw, svw)
draw.text((int(curr_x + (col_w-slw)/2), int(mid_y - 48)), sun_label, font=f_s, fill=colors["dim"])
draw.text((int(curr_x + (col_w-svw)/2), int(mid_y + 2)),  sun_val,   font=f_v, fill=colors["main"])
curr_x += col_w + 70
sep()

# ----------------------------------------------------------------
# 4. SZEKCIÓ – 3 NAPOS ELŐREJELZÉS ikonnal
# ----------------------------------------------------------------
forecast = [
    ("SZE", "15°C", "BORULT", icon_cloudy),
    ("CSÜ", "16°C", "BORULT", icon_cloudy),
    ("PÉN", "16°C", "BORULT", icon_cloudy),
]
for d_name, f_val, f_desc, f_icon in forecast:
    nw    = draw.textbbox((0,0), d_name, font=f_l)[2]
    vw    = draw.textbbox((0,0), f_val,  font=f_v)[2]
    dw    = draw.textbbox((0,0), f_desc, font=f_s)[2]
    col_w = max(nw, vw, dw, ICON_SIZE)

    # Ikon középen, szövegek alatta
    paste_icon(img, f_icon, int(curr_x + col_w//2), int(mid_y - 55))
    draw.text((int(curr_x + (col_w-nw)/2), int(mid_y + 2)),  d_name, font=f_l, fill=colors["dim"])
    draw.text((int(curr_x + (col_w-vw)/2), int(mid_y + 35)), f_val,  font=f_v, fill=colors["main"])
    draw.text((int(curr_x + (col_w-dw)/2), int(mid_y + 80)), f_desc, font=f_s, fill=colors["dim"])
    curr_x += col_w + 55
sep()

# ----------------------------------------------------------------
# 5. FRISSÍTÉS
# ----------------------------------------------------------------
update_txt = f"FRISSÍTVE\n{time.strftime('%H:%M')}"
draw.text((curr_x + 10, int(mid_y - 30)), update_txt, font=f_u, fill=colors["dim"])

# ----------------------------------------------------------------
# MENTÉS
# ----------------------------------------------------------------
output_path = "images/current.jpg"
img.convert("RGB").save(output_path, "JPEG", quality=95, subsampling=0)
print(f"✓ Kép mentve: {output_path} ({os.path.getsize(output_path):,} bytes)")

# ----------------------------------------------------------------
# WEATHER.JSON
# ----------------------------------------------------------------
unique_id = int(time.time() * 1000)
weather_json = [{
    "location": "TEST - Budapest",
    "title": f"Részben felhős 9°C – {time.strftime('%Y-%m-%d %H:%M')}",
    "author": "GitHub Action",
    "url_img":   f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/{BRANCH}/images/current.jpg?v={unique_id}",
    "image_url": f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/{BRANCH}/images/current.jpg?v={unique_id}"
}]
with open("weather.json", "w", encoding="utf-8") as f:
    json.dump(weather_json, f, ensure_ascii=False, indent=2)
print("✓ weather.json frissítve")

print("=== KÉSZ ===")
