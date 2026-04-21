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
# KONFIGURÁCIÓ
# ============================================================
CITY = "Budapest"
WIDGET_WIDTH  = 2400
WIDGET_HEIGHT = 260
WIDGET_Y      = 70
OFFSET_LEFT   = 120
INNER_MARGIN  = 70
ICON_SIZE     = 80
FC_ICON_SIZE  = 48
FC_COL_WIDTH  = 140

FONT_TEMP   = 96
FONT_DESC   = 34
FONT_LABEL  = 30
FONT_VALUE  = 38
FONT_UPDATE = 26
FONT_SUN    = 28
FONT_FC_DAY = 28
FONT_FC_TMP = 32
FONT_FC_DSC = 22
# ============================================================

# ---- Háttérkép mapping ----
BG_MAP = {
    "sunny_day":   "images/sunny_day.jpg",
    "sunny_night": "images/sunny_night.jpg",
    "cloudy_day":  "images/cloudy_day.jpg",
    "cloudy_night":"images/cloudy_night.jpg",
    "rainy_day":   "images/rainy_day.jpg",
    "rainy_night": "images/rainy_night.jpg",
    "snow_day":    "images/snow_day.jpg",
    "snow_night":  "images/snow_night.jpg",
    "foggy_day":   "images/foggy_day.jpg",
    "foggy_night": "images/foggy_night.jpg",
    "sleet_day":   "images/sleet_day.jpg",
    "sleet_night": "images/sleet_night.jpg",
    "hail_day":    "images/hail_day.jpg",
    "hail_night":  "images/hail_night.jpg",
}

def get_bg_key(weather_id, is_night):
    suffix = "night" if is_night else "day"
    if weather_id == 800: return f"sunny_{suffix}"
    if weather_id in [801, 802, 803, 804]: return f"cloudy_{suffix}"
    if weather_id in range(500, 599): return f"rainy_{suffix}"
    if weather_id == 511: return f"sleet_{suffix}"
    if weather_id in range(600, 699): return f"snow_{suffix}"
    if weather_id in range(700, 799): return f"foggy_{suffix}"
    if weather_id in range(200, 299): return f"hail_{suffix}"
    return f"cloudy_{suffix}"

def load_bg(weather_id, is_night):
    key = get_bg_key(weather_id, is_night)
    path = BG_MAP.get(key)
    if path and os.path.exists(path):
        img = Image.open(path).convert("RGBA")
        if img.size != (3840, 2160):
            img = img.resize((3840, 2160), Image.Resampling.LANCZOS)
        return img
    return Image.new("RGBA", (3840, 2160), (5, 5, 15, 255))

def find_font(bold=False):
    paths = [
        "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
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
    if weather_id == 800: return "DERULT"
    if weather_id == 801: return "PAR FELHO"
    if weather_id == 802: return "FELHOS"
    if weather_id == 803: return "FELHOS"
    if weather_id == 804: return "BORULT"
    if weather_id == 511: return "ONOS ESO"
    if weather_id in range(500, 599): return "ESOS"
    if weather_id in range(600, 699): return "HAVAS"
    if weather_id in range(700, 799): return "KODOS"
    if weather_id in range(200, 299): return "ZIVATAR"
    return "VALTOZEKONY"

def get_forecast_hu(weather_id):
    if weather_id == 800: return "NAP"
    if weather_id in [801, 802, 803]: return "FELHO"
    if weather_id == 804: return "BORU"
    if weather_id in range(500, 599): return "ESO"
    if weather_id in range(600, 699): return "HO"
    if weather_id in range(200, 299): return "ZIVA"
    return "FELHO"

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

def draw_glass_bar(img, bx, by, bw, bh):
    region = img.crop((bx, by, bx + bw, by + bh)).convert("RGBA")
    blurred = region.filter(ImageFilter.GaussianBlur(35))
    mask = Image.new("L", (bw, bh), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, bw - 1, bh - 1), radius=35, fill=200)
    overlay = Image.new("RGBA", (bw, bh), (0, 0, 10, 100))
    blurred.putalpha(mask)
    result = Image.alpha_composite(blurred, overlay)
    img.paste(result, (bx, by), result)
    return img

def draw_divider(draw, x, y_top, y_bot, color):
    draw.line([(x, y_top), (x, y_bot)], fill=color, width=2)
    draw.line([(x + 4, y_top), (x + 4, y_bot)], fill=color, width=1)

def main():
    try:
        resp = requests.get(f"https://api.openweathermap.org/data/2.5/weather?q={CITY}&appid={API_KEY}&units=metric").json()
        f_resp = requests.get(f"https://api.openweathermap.org/data/2.5/forecast?q={CITY}&appid={API_KEY}&units=metric").json()

        temp = round(resp["main"]["temp"])
        feels = round(resp["main"]["feels_like"])
        humidity = resp["main"]["humidity"]
        wind = round(resp["wind"]["speed"] * 3.6)
        weather_id = resp["weather"][0]["id"]
        tz_offset = resp.get("timezone", 3600)
        tz = timezone(timedelta(seconds=tz_offset))
        now_dt = datetime.now(tz)
        is_night = now_dt.timestamp() < resp["sys"]["sunrise"] or now_dt.timestamp() > resp["sys"]["sunset"]
        
        icon_name = get_icon_name(weather_id, is_night)
        weather_hu = get_weather_hu(weather_id)
        sunrise_str = datetime.fromtimestamp(resp["sys"]["sunrise"], tz=tz).strftime("%H:%M")
        sunset_str = datetime.fromtimestamp(resp["sys"]["sunset"], tz=tz).strftime("%H:%M")

        # Előrejelzés - 4 nap
        forecast_list = []
        seen_days = set()
        today = now_dt.date()
        for entry in f_resp['list']:
            dt_obj = datetime.fromtimestamp(entry['dt'], tz=tz)
            if dt_obj.date() > today and dt_obj.date() not in seen_days:
                forecast_list.append(entry)
                seen_days.add(dt_obj.date())
            if len(forecast_list) == 4:
                break
    except Exception as e:
        print(f"Hiba: {e}")
        return

    # Háttérkép betöltés
    img = load_bg(weather_id, is_night)

    # Widget pozíciók
    bx = OFFSET_LEFT
    by = WIDGET_Y
    bw = WIDGET_WIDTH
    bh = WIDGET_HEIGHT

    img = draw_glass_bar(img, bx, by, bw, bh)
    draw = ImageDraw.Draw(img)

    # Betűtípusok
    f_temp = get_f(FONT_TEMP, True)
    f_desc = get_f(FONT_DESC)
    f_label = get_f(FONT_LABEL)
    f_value = get_f(FONT_VALUE, True)
    f_update = get_f(FONT_UPDATE)
    f_sun = get_f(FONT_SUN)
    f_fc_day = get_f(FONT_FC_DAY, True)
    f_fc_tmp = get_f(FONT_FC_TMP, True)
    f_fc_desc = get_f(FONT_FC_DSC)

    # Színek
    c_main = (255, 255, 255, 255)
    c_dim = (200, 200, 200, 180)
    c_div = (255, 255, 255, 60)

    # Középpontok
    mid_y = by + bh // 2
    y_top = by + 35
    y_bot = by + bh - 35

    x = bx + INNER_MARGIN

    # ==================== 1. MA ====================
    day_names = ["HETFO", "KEDD", "SZERDA", "CSUTORTOK", "PENTEK", "SZOMBAT", "VASARNAP"]
    day_txt = day_names[now_dt.weekday()]
    
    draw.text((x, mid_y - 100), "MA", font=f_label, fill=c_dim)
    draw.text((x + 50, mid_y - 100), day_txt, font=f_label, fill=c_dim)
    
    temp_txt = f"{temp}C"
    draw.text((x, mid_y - 70), temp_txt, font=f_temp, fill=c_main)
    
    temp_w = draw.textbbox((0,0), temp_txt, font=f_temp)[2]
    
    # Ikon betöltés
    weather_icon = load_icon(icon_name)
    if weather_icon:
        img.paste(weather_icon, (x + temp_w + 15, mid_y - 85), weather_icon)
        icon_end = x + temp_w + 15 + ICON_SIZE
    else:
        icon_end = x + temp_w + 15
    
    draw.text((x, mid_y + 20), weather_hu, font=f_desc, fill=c_dim)
    
    # Első blokk szélessége
    block1_w = max(icon_end, x + 200) - x
    x += block1_w + 40
    draw_divider(draw, x, y_top, y_bot, c_div)
    x += 30

    # ==================== 2. Napkelte/Napnyugta ====================
    # Ikonok betöltése
    sun_icon = load_icon("day_clear", size=36)
    moon_icon = load_icon("night_clear", size=36)
    
    # Napkelte sor
    if sun_icon:
        img.paste(sun_icon, (x, mid_y - 45), sun_icon)
        sun_x = x + 40
    else:
        sun_x = x
    
    draw.text((sun_x, mid_y - 42), sunrise_str, font=f_value, fill=c_main)
    sun_end = sun_x + draw.textbbox((0,0), sunrise_str, font=f_value)[2]
    
    # Kötőjel
    draw.text((sun_end + 15, mid_y - 42), "•", font=f_value, fill=c_dim)
    
    # Napnyugta sor
    if moon_icon:
        img.paste(moon_icon, (sun_end + 35, mid_y - 45), moon_icon)
        moon_x = sun_end + 75
    else:
        moon_x = sun_end + 35
    
    draw.text((moon_x, mid_y - 42), sunset_str, font=f_value, fill=c_main)
    
    block2_w = (moon_x + draw.textbbox((0,0), sunset_str, font=f_value)[2]) - x
    x += block2_w + 40
    draw_divider(draw, x, y_top, y_bot, c_div)
    x += 30

    # ==================== 3. Adatok (Érzet, Szél, Pára) ====================
    # Ikonok betöltése
    feel_icon = load_icon("feel", size=36) if load_icon("feel", size=36) else None
    wind_icon = load_icon("wind", size=36)
    humid_icon = load_icon("para", size=36) if load_icon("para", size=36) else None
    
    # Érzet
    if feel_icon:
        img.paste(feel_icon, (x, mid_y - 45), feel_icon)
        feel_x = x + 40
    else:
        feel_x = x
    draw.text((feel_x, mid_y - 42), f"{feels}C", font=f_value, fill=c_main)
    feel_end = feel_x + draw.textbbox((0,0), f"{feels}C", font=f_value)[2]
    
    # Szél
    x = feel_end + 50
    if wind_icon:
        img.paste(wind_icon, (x, mid_y - 45), wind_icon)
        wind_x = x + 40
    else:
        wind_x = x
    draw.text((wind_x, mid_y - 42), f"{wind}KM/H", font=f_value, fill=c_main)
    wind_end = wind_x + draw.textbbox((0,0), f"{wind}KM/H", font=f_value)[2]
    
    # Pára
    x = wind_end + 50
    if humid_icon:
        img.paste(humid_icon, (x, mid_y - 45), humid_icon)
        humid_x = x + 40
    else:
        humid_x = x
    draw.text((humid_x, mid_y - 42), f"{humidity}%", font=f_value, fill=c_main)
    
    block3_w = (humid_x + draw.textbbox((0,0), f"{humidity}%", font=f_value)[2]) - (x - 100)
    x += block3_w + 40
    draw_divider(draw, x, y_top, y_bot, c_div)
    x += 30

    # ==================== 4. Előrejelzés ====================
    napok = ["HE", "KE", "SZE", "CS", "PE", "SZO", "VA"]
    for entry in forecast_list[:4]:
        dt_obj = datetime.fromtimestamp(entry['dt'], tz=tz)
        day_name = napok[dt_obj.weekday()]
        f_wid = entry['weather'][0]['id']
        f_temp_val = f"{round(entry['main']['temp'])}C"
        f_desc = get_forecast_hu(f_wid)
        
        # Nap neve
        draw.text((x + 20, mid_y - 60), day_name, font=f_fc_day, fill=c_main)
        
        # Ikon
        f_icon = load_icon(get_icon_name(f_wid, False), size=FC_ICON_SIZE)
        if f_icon:
            img.paste(f_icon, (x + 25, mid_y - 30), f_icon)
        
        # Hőmérséklet
        draw.text((x + 20, mid_y + 20), f_temp_val, font=f_fc_tmp, fill=c_main)
        
        # Leírás
        draw.text((x + 20, mid_y + 50), f_desc, font=f_fc_desc, fill=c_dim)
        
        x += FC_COL_WIDTH

    # ==================== 5. Frissítés ====================
    update_time = now_dt.strftime("%H:%M")
    update_x = bx + bw - INNER_MARGIN - 60
    
    draw_divider(draw, update_x - 30, y_top, y_bot, c_div)
    draw.text((update_x, mid_y - 25), "FRISSITVE", font=f_update, fill=c_dim)
    draw.text((update_x + 10, mid_y + 5), update_time, font=f_update, fill=c_main)

    # Mentés
    os.makedirs("images", exist_ok=True)
    img.convert("RGB").save("images/current.jpg", "JPEG", quality=95)
    print(f"Kép mentve: images/current.jpg - {update_time}")

    # JSON
    v_param = int(time.time())
    image_url = f"{BASE_URL}/images/current.jpg?v={v_param}"
    weather_json = [{
        "location": CITY,
        "title": f"{weather_hu} {temp}C",
        "author": "OpenWeatherMap",
        "image_url": image_url,
        "url_img": image_url
    }]
    with open("weather.json", "w", encoding="utf-8") as f:
        json.dump(weather_json, f, ensure_ascii=False, indent=2)
    print("Kesz!")

if __name__ == "__main__":
    main()
