#!/usr/bin/env python3
import requests
import json
import os
import time
from io import BytesIO
from datetime import datetime, timezone, timedelta
from PIL import Image, ImageDraw, ImageFont, ImageFilter

API_KEY = os.environ.get("OWM_API_KEY")
GITHUB_USER = "harsanyiz"
GITHUB_REPO = "weather-wallpaper"
BRANCH = "main"
BASE_URL = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/{BRANCH}"

# ============================================================
# KONFIGURÁCIÓ - MODERN 4K DESIGN
# ============================================================
CITY = "Budapest"

# Képernyő méret (4K)
SCREEN_W = 3840
SCREEN_H = 2160

# Widget elhelyezkedése és mérete
WIDGET_WIDTH = 2400          # Szellősebb elrendezés
WIDGET_HEIGHT = 320          # Több "levegő" az adatoknak
WIDGET_X = 80                
WIDGET_Y = 80

# Margók és térközök
INNER_MARGIN = 60            # Nagyobb belső margó a prémium érzetért

# Ikon méretek
ICON_SIZE = 110              # Fő ikon hangsúlyosabb
FC_ICON_SIZE = 60            
SUN_ICON_SIZE = 32
WIND_ICON_SIZE = 28
HUM_ICON_SIZE = 28

# Betűméretek (Noto Sans / DejaVu Sans-ra optimalizálva)
FONT_TEMP = 100              # Domináns hőmérséklet
FONT_DESC = 32               # Időjárás leírás
FONT_LABEL = 22              # Kisebb, diszkrét feliratok (MA, NÉVNAP)
FONT_SUN = 30                
FONT_FC_DAY = 30             
FONT_FC_TMP = 38             
FONT_FC_DSC = 24             
FONT_NAMEDAY = 36            
FONT_UPDATE = 20             
# ============================================================

BG_MAP = {
    "sunny_day": "images/sunny_day.jpg",
    "sunny_night": "images/sunny_night.jpg",
    "cloudy_day": "images/cloudy_day.jpg",
    "cloudy_night": "images/cloudy_night.jpg",
    "rainy_day": "images/rainy_day.jpg",
    "rainy_night": "images/rainy_night.jpg",
    "snow_day": "images/snow_day.jpg",
    "snow_night": "images/snow_night.jpg",
    "foggy_day": "images/foggy_day.jpg",
    "foggy_night": "images/foggy_night.jpg",
    "sleet_day": "images/sleet_day.jpg",
    "sleet_night": "images/sleet_night.jpg",
    "hail_day": "images/hail_day.jpg",
    "hail_night": "images/hail_night.jpg",
}

def get_bg_key(weather_id, is_night):
    suffix = "night" if is_night else "day"
    if weather_id == 800: return f"sunny_{suffix}"
    if weather_id in [801, 802, 803, 804]: return f"cloudy_{suffix}"
    if weather_id in range(500, 599): return f"rainy_{suffix}"
    if weather_id == 511: return f"sleet_{suffix}"
    if weather_id in range(600, 699): return f"snow_{suffix}"
    if weather_id in range(700, 799): return f"foggy_{suffix}"
    if weather_id in range(200, 299): return f"rainy_{suffix}"
    return f"cloudy_{suffix}"

def load_bg(weather_id, is_night):
    key = get_bg_key(weather_id, is_night)
    path = BG_MAP.get(key)
    if path and os.path.exists(path):
        img = Image.open(path).convert("RGBA")
        if img.size != (SCREEN_W, SCREEN_H):
            img = img.resize((SCREEN_W, SCREEN_H), Image.Resampling.LANCZOS)
        return img
    return Image.new("RGBA", (SCREEN_W, SCREEN_H), (10, 12, 20, 255))

def find_font(bold=False):
    paths = [
        "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "C:\\Windows\\Fonts\\arialbd.ttf" if bold else "C:\\Windows\\Fonts\\arial.ttf"
    ]
    for p in paths:
        if os.path.exists(p): return p
    return None

def get_f(size, bold=False):
    path = find_font(bold)
    if path: return ImageFont.truetype(path, size)
    return ImageFont.load_default()

def get_icon_name(weather_id, is_night):
    suffix = "night" if is_night else "day"
    if weather_id == 800: return f"{suffix}_clear"
    if weather_id == 801: return f"{suffix}_partial_cloud"
    if weather_id in [802, 803]: return "cloudy"
    if weather_id == 804: return "overcast"
    if weather_id == 511: return f"{suffix}_sleet"
    if weather_id in range(500, 599): return f"{suffix}_rain"
    if weather_id in range(600, 699): return f"{suffix}_snow"
    if weather_id in range(200, 299): return f"{suffix}_rain_thunder"
    return "cloudy"

def get_weather_hu(weather_id):
    mapping = {800: "DERÜLT", 801: "PÁR FELHŐ", 802: "FELHŐS", 803: "ERŐSEN FELHŐS", 804: "BORULT", 511: "ÓNOS ESŐ"}
    if weather_id in mapping: return mapping[weather_id]
    if weather_id in range(500, 599): return "ESŐS"
    if weather_id in range(600, 699): return "HAVAS"
    if weather_id in range(700, 799): return "KÖDÖS"
    if weather_id in range(200, 299): return "ZIVATAROS"
    return "VÁLTOZÉKONY"

def get_forecast_hu(weather_id):
    if weather_id == 800: return "NAP"
    if weather_id in [801, 802, 803]: return "FELHŐS"
    if weather_id == 804: return "BORULT"
    if weather_id in range(500, 599): return "ESŐ"
    if weather_id in range(600, 699): return "HÓ"
    return "BORULT"

def load_icon(name, size=None):
    target = size or ICON_SIZE
    url = f"{BASE_URL}/images/ICONS_PNG80/{name}.png"
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        icon = Image.open(BytesIO(r.content)).convert("RGBA")
        return icon.resize((target, target), Image.Resampling.LANCZOS)
    except:
        return None

def draw_glass_bar(img, bx, by, bw, bh, blur=50, dark=45):
    region = img.crop((bx, by, bx + bw, by + bh)).convert("RGBA")
    blurred = region.filter(ImageFilter.GaussianBlur(blur))
    mask = Image.new("L", (bw, bh), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, bw - 1, bh - 1), radius=35, fill=255)
    overlay = Image.new("RGBA", (bw, bh), (15, 20, 35, dark))
    blurred.putalpha(mask)
    result = Image.alpha_composite(blurred, overlay)
    draw = ImageDraw.Draw(result)
    draw.rounded_rectangle((0, 0, bw - 1, bh - 1), radius=35, outline=(255, 255, 255, 40), width=2)
    img.paste(result, (bx, by), result)
    return img

def draw_divider(draw, x, y_top, y_bot, color):
    draw.line([(x, y_top + 30), (x, y_bot - 30)], fill=color, width=1)

def load_namedays():
    namedays = {}
    ics_path = "Data/Magyarnevnapok.ics"
    if not os.path.exists(ics_path): return namedays
    try:
        with open(ics_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        current_date = None
        for line in lines:
            line = line.strip()
            if line.startswith("DTSTART"):
                date_part = line.split(":")[-1]
                if len(date_part) >= 8: current_date = f"{date_part[4:6]}-{date_part[6:8]}"
            elif line.startswith("SUMMARY") and current_date:
                summary = line.split(":", 1)[1]
                if summary and summary != "Névnap":
                    for a, b in [("ű","u"),("ő","o"),("ú","u"),("ó","o"),("ö","o"),("ü","u"),("á","a"),("é","e"),("í","i")]:
                        summary = summary.replace(a, b)
                    namedays[current_date] = summary
                    current_date = None
    except: pass
    return namedays

def main():
    try:
        NAMEDAYS = load_namedays()
        resp = requests.get(f"https://api.openweathermap.org/data/2.5/weather?q={CITY}&appid={API_KEY}&units=metric").json()
        f_resp = requests.get(f"https://api.openweathermap.org/data/2.5/forecast?q={CITY}&appid={API_KEY}&units=metric").json()

        temp, feels = round(resp["main"]["temp"]), round(resp["main"]["feels_like"])
        humidity, wind = resp["main"]["humidity"], round(resp["wind"]["speed"] * 3.6)
        weather_id, tz_offset = resp["weather"][0]["id"], resp.get("timezone", 3600)
        is_night = time.time() < resp["sys"]["sunrise"] or time.time() > resp["sys"]["sunset"]

        tz = timezone(timedelta(seconds=tz_offset))
        sunrise_str = datetime.fromtimestamp(resp["sys"]["sunrise"], tz=tz).strftime("%H:%M")
        sunset_str = datetime.fromtimestamp(resp["sys"]["sunset"], tz=tz).strftime("%H:%M")
        local_now = datetime.now(tz)

        nameday_text = NAMEDAYS.get(local_now.strftime("%m-%d"), "")
        nameday_one_line = " · ".join([n.strip() for n in nameday_text.replace("\\", ",").split(",") if n.strip()][:3])

        img = load_bg(weather_id, is_night)
        img = draw_glass_bar(img, WIDGET_X, WIDGET_Y, WIDGET_WIDTH, WIDGET_HEIGHT)
        draw = ImageDraw.Draw(img)

        c_main, c_dim, c_div = (255, 255, 255, 255), (210, 220, 240, 180), (255, 255, 255, 40)
        f_t, f_d, f_l, f_u, f_s = get_f(FONT_TEMP, True), get_f(FONT_DESC), get_f(FONT_LABEL), get_f(FONT_UPDATE), get_f(FONT_SUN)
        f_fd, f_ft, f_fc, f_n = get_f(FONT_FC_DAY, True), get_f(FONT_FC_TMP, True), get_f(FONT_FC_DSC), get_f(FONT_NAMEDAY)

        mid_y = WIDGET_Y + WIDGET_HEIGHT // 2
        y_top, y_bot = WIDGET_Y + 25, WIDGET_Y + WIDGET_HEIGHT - 25
        curr_x = WIDGET_X + INNER_MARGIN

        # --- MA ---
        draw.text((curr_x, mid_y - 105), "MA", font=f_l, fill=c_dim)
        draw.text((curr_x, mid_y - 90), f"{temp}°C", font=f_t, fill=c_main)
        temp_w = draw.textbbox((0, 0), f"{temp}°C", font=f_t)[2]
        
        weather_txt = f"{get_weather_hu(weather_id)}  |  {feels}°C érzet"
        draw.text((curr_x, mid_y + 25), weather_txt, font=f_d, fill=c_dim)
        
        main_icon = load_icon(get_icon_name(weather_id, is_night))
        if main_icon: img.paste(main_icon, (curr_x + temp_w + 35, mid_y - 95), main_icon)

        curr_x += 500
        draw_divider(draw, curr_x, y_top, y_bot, c_div)
        curr_x += 60

        # --- ADATOK ---
        sr_icon = load_icon("day_clear", SUN_ICON_SIZE)
        ss_icon = load_icon("night_clear", SUN_ICON_SIZE)
        if sr_icon: img.paste(sr_icon, (curr_x, mid_y - 65), sr_icon)
        draw.text((curr_x + 45, mid_y - 68), sunrise_str, font=f_s, fill=c_main)
        if ss_icon: img.paste(ss_icon, (curr_x + 180, mid_y - 65), ss_icon)
        draw.text((curr_x + 225, mid_y - 68), sunset_str, font=f_s, fill=c_main)

        w_icon = load_icon("tornado", WIND_ICON_SIZE)
        h_icon = load_icon("para", HUM_ICON_SIZE)
        if w_icon: img.paste(w_icon, (curr_x, mid_y + 25), w_icon)
        draw.text((curr_x + 40, mid_y + 25), f"{wind} km/h", font=f_d, fill=c_dim)
        if h_icon: img.paste(h_icon, (curr_x + 220, mid_y + 25), h_icon)
        draw.text((curr_x + 260, mid_y + 25), f"{humidity}%", font=f_d, fill=c_dim)

        curr_x += 420
        draw_divider(draw, curr_x, y_top, y_bot, c_div)
        curr_x += 40

        # --- ELŐREJELZÉS ---
        napok, seen, fc_entries = ["H", "K", "SZ", "CS", "P", "SZ", "V"], set(), []
        for entry in f_resp['list']:
            dt = datetime.fromtimestamp(entry['dt'], tz=tz)
            if dt.date() > datetime.now().date() and dt.date() not in seen and dt.hour >= 12:
                fc_entries.append((dt, entry))
                seen.add(dt.date())
            if len(fc_entries) == 4: break

        for dt, entry in fc_entries:
            col_x = curr_x + 75
            draw.text((col_x, y_top + 15), napok[dt.weekday()], font=f_fd, fill=c_main, anchor="mm")
            f_icon = load_icon(get_icon_name(entry['weather'][0]['id'], False), FC_ICON_SIZE)
            if f_icon: img.paste(f_icon, (col_x - FC_ICON_SIZE//2, mid_y - FC_ICON_SIZE//2 - 5), f_icon)
            draw.text((col_x, y_bot - 65), f"{round(entry['main']['temp'])}°", font=f_ft, fill=c_main, anchor="mm")
            draw.text((col_x, y_bot - 25), get_forecast_hu(entry['weather'][0]['id']), font=f_fc, fill=c_dim, anchor="mm")
            curr_x += 150

        curr_x += 40
        draw_divider(draw, curr_x, y_top, y_bot, c_div)
        
        # --- NÉVNAP ---
        nd_cx = curr_x + (WIDGET_X + WIDGET_WIDTH - curr_x) // 2
        draw.text((nd_cx, mid_y - 45), "NÉVNAP", font=f_l, fill=c_dim, anchor="mm")
        draw.text((nd_cx, mid_y + 5), nameday_one_line or "---", font=f_n, fill=c_main, anchor="mm")
        draw.text((nd_cx, y_bot - 20), f"Frissítve: {local_now.strftime('%H:%M')}", font=f_u, fill=c_dim, anchor="mm")

        img.convert("RGB").save("images/current.jpg", "JPEG", quality=95)
        with open("weather.json", "w", encoding="utf-8") as f:
            json.dump([{"location": CITY, "title": f"{temp}°C", "image_url": f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/{BRANCH}/images/current.jpg?v={int(time.time())}"}], f, ensure_ascii=False, indent=2)

    except Exception as e:
        print(f"Hiba: {e}")

if __name__ == "__main__":
    main()
