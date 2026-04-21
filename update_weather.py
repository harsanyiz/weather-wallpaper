#!/usr/bin/env python3
import os
import sys
import time
import json
import math
import random
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

ICON_SIZE = 80
# ============================================================

print("=== DINAMIKUS IKON TESZT ===")

os.makedirs("images", exist_ok=True)

# ----------------------------------------------------------------
# IKON MAPPING - IDŐJÁRÁS TÍPUS → IKON FÁJLNÉV
# ----------------------------------------------------------------
def get_icon_name(weather_type, is_night=False):
    """weather_type lehet: clear, partly_cloudy, cloudy, overcast, rain, thunder, sleet, snow, fog, mist, wind, tornado"""
    
    mapping = {
        # Derült
        "clear": f"{'night' if is_night else 'day'}_clear",
        # Pár felhős
        "partly_cloudy": f"{'night' if is_night else 'day'}_partial_cloud",
        # Felhős (alap)
        "cloudy": "cloudy",
        # Borult
        "overcast": "overcast",
        # Eső
        "rain": f"{'night' if is_night else 'day'}_rain",
        # Zivatar (eső + villám)
        "thunder": f"{'night' if is_night else 'day'}_rain_thunder",
        # Ónos eső
        "sleet": f"{'night' if is_night else 'day'}_sleet",
        # Hó
        "snow": f"{'night' if is_night else 'day'}_snow",
        # Hóvihar / hó + villám
        "snow_thunder": f"{'night' if is_night else 'day'}_snow_thunder",
        # Köd
        "fog": "fog",
        # Pára / köd
        "mist": "mist",
        # Szél
        "wind": "wind",
        # Tornádó
        "tornado": "tornado",
    }
    
    return mapping.get(weather_type, "cloudy")

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
    url = f"{BASE_URL}/images/ICONS_PNG80/{name}.png"
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        icon = Image.open(BytesIO(r.content)).convert("RGBA")
        if icon.size != (ICON_SIZE, ICON_SIZE):
            icon = icon.resize((ICON_SIZE, ICON_SIZE), Image.Resampling.LANCZOS)
        print(f"✓ Ikon betöltve: {name}.png")
        return icon
    except Exception as e:
        print(f"✗ Ikon hiba ({name}.png): {e}")
        return None

def paste_icon(img, icon, cx, cy):
    if icon is None:
        return
    x = cx - ICON_SIZE // 2
    y = cy - ICON_SIZE // 2
    img.paste(icon, (x, y), icon)

# ----------------------------------------------------------------
# HÁTTÉR – FEKETE
# ----------------------------------------------------------------
width, height = 3840, 2160
img = Image.new("RGB", (width, height), (0, 0, 0))
print("✓ Fekete háttér generálva")

# ----------------------------------------------------------------
# VÉLETLENSZERŰ IDŐJÁRÁS GENERÁLÁS (teszteléshez)
# ----------------------------------------------------------------
weather_types = ["clear", "partly_cloudy", "cloudy", "overcast", "rain", "thunder", "sleet", "snow", "fog", "mist", "wind", "tornado"]
descriptions = {
    "clear": "DERÜLT",
    "partly_cloudy": "PÁR FELHŐ",
    "cloudy": "FELHŐS",
    "overcast": "BORULT",
    "rain": "ESŐS",
    "thunder": "ZIVATAROS",
    "sleet": "ÓNOS ESŐ",
    "snow": "HAVAS",
    "fog": "KÖDÖS",
    "mist": "PÁRÁS",
    "wind": "SZELES",
    "tornado": "TORNÁDÓ",
}

# Véletlenszerű időjárás a mai napra
today_weather = random.choice(weather_types)
is_night = random.choice([True, False])  # Véletlenszerűen nappal/éjjel
today_icon_name = get_icon_name(today_weather, is_night)
today_desc = descriptions[today_weather]

# Véletlenszerű időjárás a 3 napra
forecast_weathers = random.choices(weather_types, k=3)
forecast_icons = [get_icon_name(w, False) for w in forecast_weathers]  # Előrejelzés nappal
forecast_descs = [descriptions[w] for w in forecast_weathers]

# Véletlenszerű hőmérséklet
temp = random.randint(-5, 35)
feels = temp + random.randint(-3, 3)
wind = random.randint(0, 40)
humidity = random.randint(30, 95)

print(f"✓ Mai időjárás: {today_desc} ({'éjjel' if is_night else 'nappal'}) - {temp}°C")
print(f"✓ Előrejelzés: {[descriptions[w] for w in forecast_weathers]}")

# ----------------------------------------------------------------
# IKONOK BETÖLTÉSE
# ----------------------------------------------------------------
today_icon = load_icon(today_icon_name)
forecast_icons_loaded = [load_icon(name) for name in forecast_icons]

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
day_txt  = "MA"
temp_txt = f"{temp}°C"
desc_txt = today_desc

day_w  = draw.textbbox((0,0), day_txt,  font=f_l)[2]
temp_w = draw.textbbox((0,0), temp_txt, font=f_t)[2]
desc_w = draw.textbbox((0,0), desc_txt, font=f_d)[2]
max_w  = max(day_w, temp_w, desc_w)

draw.text((int(curr_x + (max_w-day_w)  / 2), int(mid_y - 90)), day_txt,  font=f_l, fill=colors["dim"])
draw.text((int(curr_x + (max_w-temp_w) / 2), int(mid_y - 62)), temp_txt, font=f_t, fill=colors["main"])
draw.text((int(curr_x + (max_w-desc_w) / 2), int(mid_y + 38)), desc_txt, font=f_d, fill=colors["dim"])

# Ikon a hőfok jobb oldalán
icon_x = int(curr_x + max_w + 30 + ICON_SIZE // 2)
paste_icon(img, today_icon, icon_x, mid_y - 10)
curr_x += int(max_w + 30 + ICON_SIZE + 30)
sep()

# ----------------------------------------------------------------
# 2. SZEKCIÓ – ÉRZET / SZÉL / PÁRA
# ----------------------------------------------------------------
fields = [("Érzet", f"{feels}°C"), ("Szél", f"{wind} km/h"), ("Pára", f"{humidity}%")]
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
# 4. SZEKCIÓ – 3 NAPOS ELŐREJELZÉS DINAMIKUS IKONOKKAL
# ----------------------------------------------------------------
napok = ["HÉF", "KED", "SZE"]
forecast_data = []
for i in range(3):
    forecast_data.append((napok[i], f"{random.randint(-5, 35)}°C", forecast_descs[i], forecast_icons_loaded[i]))

for d_name, f_val, f_desc, f_icon in forecast_data:
    nw    = draw.textbbox((0,0), d_name, font=f_l)[2]
    vw    = draw.textbbox((0,0), f_val,  font=f_v)[2]
    dw    = draw.textbbox((0,0), f_desc, font=f_s)[2]
    col_w = max(nw, vw, dw, ICON_SIZE)

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
    "title": f"{today_desc} {temp}°C – {time.strftime('%Y-%m-%d %H:%M')}",
    "author": "GitHub Action",
    "url_img":   f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/{BRANCH}/images/current.jpg?v={unique_id}",
    "image_url": f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/{BRANCH}/images/current.jpg?v={unique_id}"
}]
with open("weather.json", "w", encoding="utf-8") as f:
    json.dump(weather_json, f, ensure_ascii=False, indent=2)
print("✓ weather.json frissítve")

print("=== KÉSZ ===")
