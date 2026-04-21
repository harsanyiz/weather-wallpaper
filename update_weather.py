#!/usr/bin/env python3
import os
import sys
import time
import json
import math
import requests
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageStat
from datetime import datetime

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

os.makedirs("images", exist_ok=True)

# ----------------------------------------------------------------
# WMO KÓD → IDŐJÁRÁS TÍPUS ÉS LEÍRÁS MAPPING
# ----------------------------------------------------------------
def get_weather_info(wmo_code):
    mapping = {
        0:  ("clear", "DERÜLT"),
        1:  ("partly_cloudy", "KEVÉS FELHŐ"),
        2:  ("partly_cloudy", "KÖZEPESEN FELHŐS"),
        3:  ("overcast", "BORULT"),
        45: ("fog", "KÖDÖS"), 48: ("fog", "ZIMANKÓS KÖD"),
        51: ("rain", "SZITÁLÁS"), 53: ("rain", "ESŐS"), 55: ("rain", "ERŐS SZITÁLÁS"),
        61: ("rain", "GYENGE ESŐ"), 63: ("rain", "ESŐS"), 65: ("rain", "HEVES ESŐ"),
        66: ("sleet", "ÓNOS ESŐ"), 67: ("sleet", "ERŐS ÓNOS ESŐ"),
        71: ("snow", "GYENGE HAVAZÁS"), 73: ("snow", "HAVAZÁS"), 75: ("snow", "ERŐS HAVAZÁS"),
        77: ("snow", "HAVAS ESŐ"),
        80: ("rain", "ZÁPOR"), 81: ("rain", "ZÁPOR"), 82: ("rain", "HEVES ZÁPOR"),
        85: ("snow", "HÓZÁPOR"), 86: ("snow", "ERŐS HÓZÁPOR"),
        95: ("thunder", "ZIVATAROS"), 96: ("thunder", "JÉGESŐ + ZIVATAR"),
    }
    return mapping.get(wmo_code, ("cloudy", "FELHŐS"))

def get_icon_name(weather_type, is_night=False):
    mapping = {
        "clear": f"{'night' if is_night else 'day'}_clear",
        "partly_cloudy": f"{'night' if is_night else 'day'}_partial_cloud",
        "cloudy": "cloudy",
        "overcast": "overcast",
        "rain": f"{'night' if is_night else 'day'}_rain",
        "thunder": f"{'night' if is_night else 'day'}_rain_thunder",
        "sleet": f"{'night' if is_night else 'day'}_sleet",
        "snow": f"{'night' if is_night else 'day'}_snow",
        "fog": "fog", "mist": "mist", "wind": "wind", "tornado": "tornado"
    }
    return mapping.get(weather_type, "cloudy")

# ----------------------------------------------------------------
# ADATOK LEKÉRÉSE (Open-Meteo)
# ----------------------------------------------------------------
def fetch_weather():
    # Budapest koordináták
    url = "https://api.open-meteo.com/v1/forecast?latitude=47.4979&longitude=19.0402&current=temperature_2m,relative_humidity_2m,apparent_temperature,is_day,weather_code,wind_speed_10m&daily=weather_code,temperature_2m_max,sunrise,sunset&timezone=auto"
    r = requests.get(url, timeout=15)
    return r.json()

# ----------------------------------------------------------------
# PIL SEGÉDFÜGGVÉNYEK
# ----------------------------------------------------------------
def find_font(bold=False):
    paths = [
        "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
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
    region = img.crop((bx, by, bx+bw, by+bh))
    blurred = region.filter(ImageFilter.GaussianBlur(30))
    mask = Image.new("L", (bw, bh), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, bw, bh), radius=30, fill=180)
    overlay = Image.new("RGBA", (bw, bh), (0, 0, 10, 100))
    blurred = blurred.convert("RGBA")
    blurred.putalpha(mask)
    result = Image.alpha_composite(blurred, overlay)
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
                pixels[px, y_top + i] = (int(br*(1-a) + r*a), int(bg*(1-a) + g*a), int(bb*(1-a) + b*a), ba)

def load_icon(name):
    url = f"{BASE_URL}/images/ICONS_PNG80/{name}.png"
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        icon = Image.open(BytesIO(r.content)).convert("RGBA")
        if icon.size != (ICON_SIZE, ICON_SIZE):
            icon = icon.resize((ICON_SIZE, ICON_SIZE), Image.Resampling.LANCZOS)
        return icon
    except:
        return None

def paste_icon(img, icon, cx, cy):
    if icon:
        x, y = cx - ICON_SIZE // 2, cy - ICON_SIZE // 2
        img.paste(icon, (x, y), icon)

# --- ADATOK BETÖLTÉSE ---
try:
    data = fetch_weather()
    current = data["current"]
    daily = data["daily"]

    type_str, today_desc = get_weather_info(current["weather_code"])
    temp = round(current["temperature_2m"])
    feels = round(current["apparent_temperature"])
    wind = round(current["wind_speed_10m"])
    humidity = current["relative_humidity_2m"]
    is_night = current["is_day"] == 0
    today_icon = load_icon(get_icon_name(type_str, is_night))

    sunrise = current["time"][:11] + daily["sunrise"][0][-5:] # Egyszerűsített parszi
    sunset  = current["time"][:11] + daily["sunset"][0][-5:]
    sun_val = f"{daily['sunrise'][0][-5:]}  •  {daily['sunset'][0][-5:]}"

except Exception as e:
    print(f"Hiba az adatoknál: {e}")
    sys.exit(1)

# --- RAJZOLÁS ---
img = Image.new("RGB", (3840, 2160), (0, 0, 0)).convert("RGBA")
img = draw_glass_bar(img, OFFSET_LEFT, WIDGET_Y, WIDGET_WIDTH, WIDGET_HEIGHT)

region = img.crop((OFFSET_LEFT, WIDGET_Y, OFFSET_LEFT+WIDGET_WIDTH, WIDGET_Y+WIDGET_HEIGHT)).convert("L")
colors = get_text_colors(ImageStat.Stat(region).mean[0])
draw = ImageDraw.Draw(img)
f_t, f_d, f_l, f_v, f_u, f_s = get_f(90, True), get_f(32), get_f(28), get_f(36, True), get_f(24), get_f(22)

curr_x = OFFSET_LEFT + INNER_MARGIN
mid_y = WIDGET_Y + WIDGET_HEIGHT // 2

def sep():
    global curr_x
    draw_separator(img, curr_x, WIDGET_Y+20, WIDGET_Y+WIDGET_HEIGHT-20, colors["line"])
    curr_x += 40

# 1. MA
day_txt, temp_txt = "MA", f"{temp}°C"
tw = draw.textbbox((0,0), temp_txt, font=f_t)[2]
draw.text((curr_x, mid_y - 90), day_txt, font=f_l, fill=colors["dim"])
draw.text((curr_x, mid_y - 62), temp_txt, font=f_t, fill=colors["main"])
draw.text((curr_x, mid_y + 38), today_desc, font=f_d, fill=colors["dim"])
paste_icon(img, today_icon, curr_x + tw + 60, mid_y - 10)
curr_x += tw + 150
sep()

# 2. RÉSZLETEK
for label, val in [("Érzet", f"{feels}°C"), ("Szél", f"{wind} km/h"), ("Pára", f"{humidity}%")]:
    draw.text((curr_x, mid_y - 48), label.upper(), font=f_l, fill=colors["dim"])
    draw.text((curr_x, mid_y + 2), val, font=f_v, fill=colors["main"])
    curr_x += 180
sep()

# 3. NAP
draw.text((curr_x, mid_y - 48), "NAPKELTE / NAPNYUGTA", font=f_s, fill=colors["dim"])
draw.text((curr_x, mid_y + 2), sun_val, font=f_v, fill=colors["main"])
curr_x += 320
sep()

# 4. ELŐREJELZÉS (3 nap)
days_map = ["HÉF", "KED", "SZE", "CSÜ", "PÉN", "SZO", "VAS"]
for i in range(1, 4):
    d_idx = datetime.strptime(daily["time"][i], "%Y-%m-%d").weekday()
    d_name = days_map[d_idx]
    f_temp = f"{round(daily['temperature_2m_max'][i])}°C"
    f_type, f_desc = get_weather_info(daily["weather_code"][i])
    f_icon = load_icon(get_icon_name(f_type, False))
    
    paste_icon(img, f_icon, curr_x + 40, mid_y - 55)
    draw.text((curr_x, mid_y + 2), d_name, font=f_l, fill=colors["dim"])
    draw.text((curr_x, mid_y + 35), f_temp, font=f_v, fill=colors["main"])
    curr_x += 160
sep()

# 5. FRISSÍTÉS IDŐPONTJA - Most már a tényleges idő
update_txt = f"FRISSÍTVE\n{datetime.now().strftime('%H:%M')}"
draw.text((curr_x + 10, mid_y - 30), update_txt, font=f_u, fill=colors["dim"])

# MENTÉS
output_path = "images/current.jpg"
img.convert("RGB").save(output_path, "JPEG", quality=95)

# JSON (v=timestamp a cache elkerüléséhez)
ts = int(time.time())
weather_json = [{
    "location": "Budapest",
    "title": f"{today_desc} {temp}°C",
    "url_img": f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/{BRANCH}/images/current.jpg?v={ts}",
    "image_url": f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/{BRANCH}/images/current.jpg?v={ts}"
}]
with open("weather.json", "w", encoding="utf-8") as f:
    json.dump(weather_json, f, ensure_ascii=False, indent=2)

print(f"Kész! Frissítve: {datetime.now().strftime('%H:%M:%S')}")
