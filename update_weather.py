#!/usr/bin/env python3
import requests
import json
import os
import time
import math
from io import BytesIO
from datetime import datetime, timezone, timedelta
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageStat

# API kulcsot vedd ki környezeti változóból vagy írd be ide
API_KEY = os.environ.get("OWM_API_KEY")
GITHUB_USER = "harsanyiz"
GITHUB_REPO = "weather-wallpaper"
BRANCH = "main"
# Az ikonok elérési útja a repódban
BASE_URL = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/{BRANCH}"

# ============================================================
# KONFIGURÁCIÓ
# ============================================================
CITY = "Budapest"
WIDGET_WIDTH = 2200
WIDGET_HEIGHT = 220
WIDGET_Y = 80
OFFSET_LEFT = 135
INNER_MARGIN = 80
ICON_SIZE = 80

FONT_TEMP   = 90
FONT_DESC   = 32
FONT_LABEL  = 28
FONT_VALUE  = 36
FONT_UPDATE = 24
FONT_SUN    = 22
# ============================================================

def find_font(bold=False):
    paths = [
        "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    ]
    for p in paths:
        if os.path.exists(p): return p
    return None

def get_f(size, bold=False):
    path = find_font(bold)
    if path: return ImageFont.truetype(path, size)
    return ImageFont.load_default()

def get_icon_name(weather_id, is_night):
    """Leképezi az OWM ID-t a te ikon fájlneveidre"""
    suffix = "night" if is_night else "day"
    # Derült
    if weather_id == 800: return f"{suffix}_clear"
    # Felhős kategóriák
    if weather_id == 801: return f"{suffix}_partial_cloud"
    if weather_id in [802, 803]: return "cloudy"
    if weather_id == 804: return "overcast"
    # Eső / Ónos eső
    if weather_id == 511: return f"{suffix}_sleet"
    if weather_id in range(500, 599): return f"{suffix}_rain"
    # Hó
    if weather_id in range(600, 699): return f"{suffix}_snow"
    # Zivatar
    if weather_id in range(200, 299): return f"{suffix}_rain_thunder"
    return "cloudy"

def get_weather_hu(weather_id):
    mapping = {800: "DERÜLT", 801: "PÁR FELHŐ", 802: "FELHŐS",
               803: "ERŐSEN FELHŐS", 804: "BORULT", 511: "ÓNOS ESŐ"}
    return mapping.get(weather_id, "VÁLTOZÉKONY")

def load_icon(name):
    url = f"{BASE_URL}/images/ICONS_PNG80/{name}.png"
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        icon = Image.open(BytesIO(r.content)).convert("RGBA")
        return icon.resize((ICON_SIZE, ICON_SIZE), Image.Resampling.LANCZOS)
    except:
        return None

def draw_glass_bar(img, bx, by, bw, bh):
    region = img.crop((bx, by, bx + bw, by + bh))
    blurred = region.filter(ImageFilter.GaussianBlur(30))
    mask = Image.new("L", (bw, bh), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, bw, bh), radius=30, fill=180)
    overlay = Image.new("RGBA", (bw, bh), (0, 0, 10, 100))
    blurred = blurred.convert("RGBA")
    blurred.putalpha(mask)
    result = Image.alpha_composite(blurred, overlay)
    img.paste(result, (bx, by), result)
    return img

def main():
    try:
        # 1. ADATOK LEKÉRÉSE
        resp = requests.get(f"https://api.openweathermap.org/data/2.5/weather?q={CITY}&appid={API_KEY}&units=metric").json()
        f_resp = requests.get(f"https://api.openweathermap.org/data/2.5/forecast?q={CITY}&appid={API_KEY}&units=metric").json()

        temp = round(resp["main"]["temp"])
        feels = round(resp["main"]["feels_like"])
        humidity = resp["main"]["humidity"]
        wind = round(resp["wind"]["speed"] * 3.6)
        weather_id = resp["weather"][0]["id"]
        
        tz_offset = resp.get("timezone", 3600)
        now_ts = time.time()
        is_night = now_ts < resp["sys"]["sunrise"] or now_ts > resp["sys"]["sunset"]
        
        # Ikon és szöveg meghatározása
        today_icon_name = get_icon_name(weather_id, is_night)
        weather_hu = get_weather_hu(weather_id)
        
        # Napkelte/nyugta formázása
        sunrise_str = datetime.fromtimestamp(resp["sys"]["sunrise"], tz=timezone(timedelta(seconds=tz_offset))).strftime("%H:%M")
        sunset_str = datetime.fromtimestamp(resp["sys"]["sunset"], tz=timezone(timedelta(seconds=tz_offset))).strftime("%H:%M")

        # 2. HÁTTÉRKÉP ELŐKÉSZÍTÉSE
        # Megpróbáljuk betölteni az időjáráshoz illő hátteret
        bg_name = "sunny_day" if not is_night else "clear_night" 
        # (Itt használhatod a saját image_name logikádat is a háttérhez)
        
        img = Image.new("RGB", (3840, 2160), (0, 0, 0)) # Alap fekete, ha nincs kép
        # Ha van háttérképed a mappában, ide töltheted be:
        # img = Image.open(f"images/{bg_name}.jpg")

        img = img.convert("RGBA")
        img = draw_glass_bar(img, OFFSET_LEFT, WIDGET_Y, WIDGET_WIDTH, WIDGET_HEIGHT)
        
        draw = ImageDraw.Draw(img)
        region = img.crop((OFFSET_LEFT, WIDGET_Y, OFFSET_LEFT+WIDGET_WIDTH, WIDGET_Y+WIDGET_HEIGHT)).convert("L")
        avg_br = ImageStat.Stat(region).mean[0]
        
        # Színek beállítása a fényerő alapján
        c_main = (255,255,255,255) if avg_br < 145 else (0,0,0,230)
        c_dim = (255,255,255,160) if avg_br < 145 else (0,0,0,140)
        c_line = (255,255,255,60) if avg_br < 145 else (0,0,0,60)

        # Betűtípusok
        f_t, f_d, f_l, f_v, f_u, f_s = get_f(90, True), get_f(32), get_f(28), get_f(36, True), get_f(24), get_f(22)

        curr_x = OFFSET_LEFT + INNER_MARGIN
        mid_y = WIDGET_Y + WIDGET_HEIGHT // 2

        # --- 1. SZEKCIÓ: MA + HŐMÉRSÉKLET ---
        draw.text((curr_x, mid_y - 90), "MA", font=f_l, fill=c_dim)
        draw.text((curr_x, mid_y - 62), f"{temp}°C", font=f_t, fill=c_main)
        draw.text((curr_x, mid_y + 38), weather_hu, font=f_d, fill=c_dim)
        
        # Ikon kirakása
        icon_img = load_icon(today_icon_name)
        if icon_img:
            temp_w = draw.textbbox((0,0), f"{temp}°C", font=f_t)[2]
            img.paste(icon_img, (curr_x + temp_w + 30, mid_y - 45), icon_img)
            curr_x += temp_w + 150
        else:
            curr_x += 300

        # Elválasztó
        for dx in [0, 4]: draw.line([(curr_x + dx, WIDGET_Y+35), (curr_x + dx, WIDGET_Y+WIDGET_HEIGHT-35)], fill=c_line, width=1)
        curr_x += 40

        # --- 2. SZEKCIÓ: RÉSZLETEK ---
        for label, val in [("ÉRZET", f"{feels}°C"), ("SZÉL", f"{wind} km/h"), ("PÁRA", f"{humidity}%")]:
            draw.text((curr_x, mid_y - 48), label, font=f_l, fill=c_dim)
            draw.text((curr_x, mid_y + 2), val, font=f_v, fill=c_main)
            curr_x += 180
            
        for dx in [0, 4]: draw.line([(curr_x + dx, WIDGET_Y+35), (curr_x + dx, WIDGET_Y+WIDGET_HEIGHT-35)], fill=c_line, width=1)
        curr_x += 40

        # --- 3. SZEKCIÓ: NAPKELTE ---
        draw.text((curr_x, mid_y - 48), "NAPKELTE / NAPNYUGTA", font=f_s, fill=c_dim)
        draw.text((curr_x, mid_y + 2), f"{sunrise_str}  •  {sunset_str}", font=f_v, fill=c_main)
        curr_x += 320

        for dx in [0, 4]: draw.line([(curr_x + dx, WIDGET_Y+35), (curr_x + dx, WIDGET_Y+WIDGET_HEIGHT-35)], fill=c_line, width=1)
        curr_x += 40

        # --- 4. SZEKCIÓ: ELŐREJELZÉS ---
        napok = ["HÉ", "KE", "SZE", "CS", "PÉ", "SZO", "VA"]
        count = 0
        for entry in f_resp['list']:
            dt = datetime.fromtimestamp(entry['dt'], tz=timezone(timedelta(seconds=tz_offset)))
            if dt.hour == 12 and dt.date() > datetime.now().date():
                d_name = napok[dt.weekday()]
                f_icon = load_icon(get_icon_name(entry['weather'][0]['id'], False))
                f_temp = f"{round(entry['main']['temp'])}°C"
                
                if f_icon: img.paste(f_icon, (curr_x, mid_y - 75), f_icon)
                draw.text((curr_x, mid_y + 10), d_name, font=f_l, fill=c_dim)
                draw.text((curr_x, mid_y + 45), f_temp, font=f_v, fill=c_main)
                curr_x += 150
                count += 1
                if count == 3: break

        # --- 5. FRISSÍTÉS ---
        update_txt = f"FRISSÍTVE\n{datetime.now().strftime('%H:%M')}"
        draw.text((curr_x + 20, mid_y - 30), update_txt, font=f_u, fill=c_dim)

        # Mentés
        img.convert("RGB").save("images/current.jpg", "JPEG", quality=95)
        print("Kész!")

    except Exception as e:
        print(f"Hiba: {e}")

if __name__ == "__main__":
    main()
