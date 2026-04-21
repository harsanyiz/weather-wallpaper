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

ICON_SIZE = 80  # px – a te ikonjaid 80x80-asok
# ============================================================

print("=== IDŐJÁRÁS WIDGET INDÍTÁSA ===")

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
    """Ikon betöltése a TE ICONS_PNG80 mappádból (.jpg kiterjesztéssel)"""
    # A te mappádban .jpg van, nem .png
    url = f"{BASE_URL}/images/ICONS_PNG80/{name}.jpg"
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            icon = Image.open(BytesIO(r.content)).convert("RGBA")
            # Ha nem pont 80x80, resize-oljuk
            if icon.size != (ICON_SIZE, ICON_SIZE):
                icon = icon.resize((ICON_SIZE, ICON_SIZE), Image.Resampling.LANCZOS)
            print(f"✓ Ikon betöltve: {name}.jpg ({icon.size[0]}x{icon.size[1]})")
            return icon
    except Exception as e:
        print(f"✗ Ikon hiba ({name}.jpg): {e}")
    
    # Fallback: ha nincs meg az ikon, próbálkozzunk a cloudy-val
    if name != "cloudy_day" and name != "cloudy_night":
        fallback = "cloudy_day" if "day" in name else "cloudy_night"
        print(f"  → Fallback: {fallback}.jpg")
        return load_icon(fallback)
    return None

def paste_icon(img, icon, cx, cy):
    """Ikon beillesztése – cx/cy a középpont."""
    if icon is None:
        return
    x = cx - ICON_SIZE // 2
    y = cy - ICON_SIZE // 2
    img.paste(icon, (x, y), icon)

def get_icon_name(weather_id, is_night):
    """Időjárás ID alapján ikon név a te mappádban"""
    suffix = "night" if is_night else "day"
    
    if weather_id in range(200, 233):
        return f"hail_{suffix}"
    if weather_id in [511, 611, 612, 613, 615, 616]:
        return f"sleet_{suffix}"
    if weather_id in range(500, 532):
        return f"rainy_{suffix}"
    if weather_id in range(600, 623):
        return f"snow_{suffix}"
    if weather_id in [701, 711, 721, 731, 741, 751, 761, 762]:
        return f"foggy_{suffix}"
    if weather_id == 800:
        return f"sunny_{suffix}"
    if weather_id in [801, 802, 803, 804]:
        return f"cloudy_{suffix}"
    return f"cloudy_{suffix}"

# ----------------------------------------------------------------
# HÁTTÉRKÉP BETÖLTÉSE (vagy generálása teszt esetén)
# ----------------------------------------------------------------
# Itt töltsd be a valós háttérképet, vagy generálj teszt hátteret
# Ez a rész az eredeti update_weather.py-ból jön majd

# ----------------------------------------------------------------
# IDŐJÁRÁS ADATOK (ez majd az API-ból jön)
# ----------------------------------------------------------------
# Ez itt most csak TESZT adat
weather_id = 802  # részben felhős
is_night = False
icon_name = get_icon_name(weather_id, is_night)
print(f"Ikon keresés: {icon_name}.jpg")

# Ikon betöltése
weather_icon = load_icon(icon_name)

# ----------------------------------------------------------------
# GLASS BAR (a widget pozíciói az eredeti configból)
# ----------------------------------------------------------------
# Ez a rész is az eredeti update_weather.py-ból jön majd
