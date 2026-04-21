import requests
import json
import os
import time
import math
from datetime import datetime, timezone, timedelta
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageStat

API_KEY = os.environ.get("OWM_API_KEY")
GITHUB_USER = "harsanyiz"
GITHUB_REPO = "weather-wallpaper"
BRANCH = "main"
BASE_URL = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/{BRANCH}/images"

# ============================================================
# KONFIGURÁCIÓ - FINOMHANGOLT ÉRTÉKEK
# ============================================================
CITY = "Budapest"
WIDGET_WIDTH = 2400  # Kissé szélesebb
WIDGET_HEIGHT = 240  # Kissé magasabb
WIDGET_Y = 70
OFFSET_LEFT = 120
INNER_MARGIN = 70

# Betűméretek - optimalizált olvashatóságra
FONT_TEMP   = 96   # Hőmérséklet nagyob
FONT_DESC   = 34   # Leírás
FONT_LABEL  = 30   # Címkék
FONT_VALUE  = 38   # Értékek
FONT_UPDATE = 26   # Frissítés
FONT_SUN    = 24   # Napkelte/nyugta

# Színek - jobb kontraszt
COLORS = {
    "dark": {
        "main": (255, 255, 255, 255),
        "dim": (255, 255, 255, 200),
        "line": (255, 255, 255, 80),
        "bg": (0, 0, 0, 120)
    },
    "light": {
        "main": (0, 0, 0, 230),
        "dim": (0, 0, 0, 180),
        "line": (0, 0, 0, 60),
        "bg": (255, 255, 255, 100)
    }
}
# ============================================================

def find_font(bold=False):
    """Betűtípus keresés"""
    paths = [
        "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/System/Library/Fonts/Helvetica.ttc",  # macOS
        "C:/Windows/Fonts/arial.ttf"  # Windows
    ]
    for p in paths:
        if os.path.exists(p): 
            return p
    return None

def get_f(size, bold=False):
    """Betűtípus betöltés"""
    path = find_font(bold)
    if path: 
        return ImageFont.truetype(path, size)
    return ImageFont.load_default()

def get_image_name(weather_id, is_night):
    """Háttérkép kiválasztás"""
    suffix = "night" if is_night else "day"
    if weather_id in [611, 612, 613, 615, 616]: 
        return f"sleet_{suffix}"
    elif weather_id in [620, 621, 622, 600, 601, 602]: 
        return f"snow_{suffix}"
    elif weather_id == 800: 
        return f"sunny_{suffix}"
    else: 
        return f"cloudy_{suffix}"

def get_weather_hu(weather_id):
    """Időjárás magyar neve"""
    mapping = {
        800: "DERULT",
        801: "PARTLY CLOUDY",
        802: "MOSTLY CLOUDY",
        803: "CLOUDY",
        804: "OVERCAST",
        511: "FREEZING RAIN",
        500: "LIGHT RAIN",
        501: "MODERATE RAIN",
        502: "HEAVY RAIN",
        600: "LIGHT SNOW",
        601: "SNOW",
        602: "HEAVY SNOW",
        200: "THUNDERSTORM",
        300: "DRIZZLE"
    }
    return mapping.get(weather_id, "VARIABLE")

def get_forecast_hu(weather_id):
    """Előrejelzés rövid neve"""
    if weather_id == 800: 
        return "SUNNY"
    elif weather_id in [801, 802]: 
        return "CLOUDY"
    elif weather_id in [803, 804]: 
        return "OVERCAST"
    elif weather_id in range(500, 532): 
        return "RAIN"
    elif weather_id in range(300, 322): 
        return "DRIZZLE"
    elif weather_id in range(600, 623): 
        return "SNOW"
    elif weather_id in range(200, 233): 
        return "STORM"
    return "MIXED"

def get_day_hu(date_obj):
    """Nap neve magyarul"""
    napok = ["HETFO", "KEDD", "SZERDA", "CSUTORTOK", "PENTEK", "SZOMBAT", "VASARNAP"]
    return napok[date_obj.weekday()]

def get_text_colors(brightness):
    """Színválasztás a háttér fényereje alapján"""
    if brightness > 145:
        return COLORS["light"]
    return COLORS["dark"]

def draw_glass_bar(img, bx, by, bw, bh, colors):
    """Átlátszó háttérsáv"""
    # Homályosított rész
    region = img.crop((bx, by, bx + bw, by + bh))
    blurred = region.filter(ImageFilter.GaussianBlur(35))
    
    # Átlátszósági maszk
    mask = Image.new("L", (bw, bh), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle((0, 0, bw, bh), radius=40, fill=200)
    
    # Háttér szín
    overlay = Image.new("RGBA", (bw, bh), colors["bg"])
    blurred = blurred.convert("RGBA")
    blurred.putalpha(mask)
    
    # Összemosás
    result = Image.alpha_composite(blurred, overlay)
    img.paste(result, (bx, by), result)
    return img

def format_sun_time(ts, tz_offset):
    """Idő formázás"""
    dt = datetime.fromtimestamp(ts, tz=timezone(timedelta(seconds=tz_offset)))
    return dt.strftime("%H:%M")

def draw_vertical_divider(draw, x, y_start, y_end, colors):
    """Elegáns függőleges elválasztó"""
    draw.line([(x, y_start), (x, y_end)], fill=colors["line"], width=2)
    draw.line([(x+3, y_start), (x+3, y_end)], fill=colors["line"], width=1)

def main():
    try:
        # API hívások
        print("Időjárás adatok lekérése...")
        resp = requests.get(f"https://api.openweathermap.org/data/2.5/weather?q={CITY}&appid={API_KEY}&units=metric")
        resp.raise_for_status()
        resp = resp.json()
        
        f_resp = requests.get(f"https://api.openweathermap.org/data/2.5/forecast?q={CITY}&appid={API_KEY}&units=metric")
        f_resp.raise_for_status()
        f_resp = f_resp.json()

        # Alap adatok
        temp = round(resp["main"]["temp"])
        feels = round(resp["main"]["feels_like"])
        humidity = resp["main"]["humidity"]
        wind = round(resp["wind"]["speed"] * 3.6)
        weather_id = resp["weather"][0]["id"]
        tz_offset = resp.get("timezone", 3600)
        now_dt = datetime.now(timezone(timedelta(seconds=tz_offset)))
        update_time = now_dt.strftime("%H:%M")
        is_night = now_dt.timestamp() < resp["sys"]["sunrise"] or now_dt.timestamp() > resp["sys"]["sunset"]
        
        image_name = get_image_name(weather_id, is_night)
        weather_hu = get_weather_hu(weather_id)
        sunrise_str = format_sun_time(resp["sys"]["sunrise"], tz_offset)
        sunset_str = format_sun_time(resp["sys"]["sunset"], tz_offset)

        # 3 napos előrejelzés
        forecast_list = []
        seen_days = set()
        today = now_dt.date()
        for entry in f_resp['list']:
            dt_obj = datetime.fromtimestamp(entry['dt'], tz=timezone(timedelta(seconds=tz_offset)))
            if dt_obj.date() > today and dt_obj.date() not in seen_days and dt_obj.hour >= 12:
                forecast_list.append(entry)
                seen_days.add(dt_obj.date())
            if len(forecast_list) == 3: 
                break
                
        print(f"Háttérkép: {image_name}.jpg")
        
    except Exception as e:
        print(f"Hiba az API hívásnál: {e}")
        return

    # Háttérkép betöltés
    src = f"images/{image_name}.jpg"
    dst = "images/current.jpg"
    
    try:
        img = Image.open(src).convert("RGB")
        if img.size != (3840, 2160):
            img = img.resize((3840, 2160), Image.Resampling.LANCZOS)
    except Exception as e:
        print(f"Hiba a kép betöltésénél: {e}")
        return

    # Widget pozíció
    W, H = img.size
    bx = OFFSET_LEFT
    by = WIDGET_Y
    bw = WIDGET_WIDTH
    bh = WIDGET_HEIGHT

    # RGBA konverzió
    img = img.convert("RGBA")
    
    # Háttér fényerő meghatározás
    region = img.crop((bx, by, bx + bw, by + bh)).convert("L")
    avg_brightness = ImageStat.Stat(region).mean[0]
    colors = get_text_colors(avg_brightness)
    
    # Átlátszó sáv
    img = draw_glass_bar(img, bx, by, bw, bh, colors)
    draw = ImageDraw.Draw(img)

    # Betűtípusok
    f_temp = get_f(FONT_TEMP, True)
    f_desc = get_f(FONT_DESC)
    f_label = get_f(FONT_LABEL)
    f_value = get_f(FONT_VALUE, True)
    f_update = get_f(FONT_UPDATE)
    f_sun = get_f(FONT_SUN)

    curr_x = int(bx + INNER_MARGIN)
    mid_y = int(by + bh // 2)

    # ============================================================
    # 1. BAL OLDAL: NAP + HŐMÉRSÉKLET + LEÍRÁS
    # ============================================================
    day_txt = get_day_hu(now_dt)
    temp_txt = f"{temp}°C"
    desc_txt = weather_hu

    # Méretek számítás
    day_w = draw.textbbox((0,0), day_txt, font=f_label)[2]
    temp_w = draw.textbbox((0,0), temp_txt, font=f_temp)[2]
    desc_w = draw.textbbox((0,0), desc_txt, font=f_desc)[2]
    max_w = max(day_w, temp_w, desc_w)

    # Középre igazítás
    draw.text((int(curr_x + (max_w - day_w) / 2), int(mid_y - 85)), 
              day_txt, font=f_label, fill=colors["dim"])
    draw.text((int(curr_x + (max_w - temp_w) / 2), int(mid_y - 55)), 
              temp_txt, font=f_temp, fill=colors["main"])
    draw.text((int(curr_x + (max_w - desc_w) / 2), int(mid_y + 45)), 
              desc_txt, font=f_desc, fill=colors["dim"])

    curr_x += max_w + 75

    # Elválasztó
    draw_vertical_divider(draw, curr_x, by+40, by+bh-40, colors)
    curr_x += 35

    # ============================================================
    # 2. IDŐJÁRÁSI ADATOK
    # ============================================================
    fields = [
        ("FEELS LIKE", f"{feels}°C"),
        ("WIND", f"{wind} km/h"),
        ("HUMIDITY", f"{humidity}%"),
    ]
    
    for label, val in fields:
        lw = draw.textbbox((0,0), label, font=f_label)[2]
        vw = draw.textbbox((0,0), val, font=f_value)[2]
        col_w = max(lw, vw)
        
        draw.text((int(curr_x + (col_w - lw)/2), int(mid_y - 48)), 
                  label, font=f_label, fill=colors["dim"])
        draw.text((int(curr_x + (col_w - vw)/2), int(mid_y + 5)), 
                  val, font=f_value, fill=colors["main"])
        
        curr_x += col_w + 65

    # Elválasztó
    draw_vertical_divider(draw, curr_x, by+40, by+bh-40, colors)
    curr_x += 35

    # ============================================================
    # 3. NAPKELTE / NAPNYUGTA
    # ============================================================
    sun_label = "SUNRISE / SUNSET"
    sun_val = f"{sunrise_str}  •  {sunset_str}"
    
    slw = draw.textbbox((0,0), sun_label, font=f_sun)[2]
    svw = draw.textbbox((0,0), sun_val, font=f_value)[2]
    col_w = max(slw, svw)
    
    draw.text((int(curr_x + (col_w - slw)/2), int(mid_y - 48)), 
              sun_label, font=f_sun, fill=colors["dim"])
    draw.text((int(curr_x + (col_w - svw)/2), int(mid_y + 5)), 
              sun_val, font=f_value, fill=colors["main"])
    
    curr_x += col_w + 75

    # Elválasztó
    draw_vertical_divider(draw, curr_x, by+40, by+bh-40, colors)
    curr_x += 35

    # ============================================================
    # 4. 3 NAPOS ELŐREJELZÉS
    # ============================================================
    for i, day in enumerate(forecast_list):
        dt_obj = datetime.fromtimestamp(day['dt'], tz=timezone(timedelta(seconds=tz_offset)))
        day_name = get_day_hu(dt_obj)[:3]  # Első 3 betű
        temp_val = f"{round(day['main']['temp'])}°C"
        weather_desc = get_forecast_hu(day['weather'][0]['id'])
        
        # Méretek
        nw = draw.textbbox((0,0), day_name, font=f_label)[2]
        vw = draw.textbbox((0,0), temp_val, font=f_value)[2]
        dw = draw.textbbox((0,0), weather_desc, font=f_sun)[2]
        col_w = max(nw, vw, dw)
        
        # Rajzolás
        draw.text((int(curr_x + (col_w - nw)/2), int(mid_y - 85)), 
                  day_name, font=f_label, fill=colors["dim"])
        draw.text((int(curr_x + (col_w - vw)/2), int(mid_y - 50)), 
                  temp_val, font=f_value, fill=colors["main"])
        draw.text((int(curr_x + (col_w - dw)/2), int(mid_y)), 
                  weather_desc, font=f_sun, fill=colors["dim"])
        
        curr_x += col_w + 50
        
        # Kis elválasztó az utolsó előtti elem után
        if i < len(forecast_list) - 1:
            draw.line([(curr_x - 20, mid_y - 60), (curr_x - 20, mid_y + 30)], 
                     fill=colors["line"], width=1)

    # Utolsó elválasztó
    draw_vertical_divider(draw, curr_x, by+40, by+bh-40, colors)
    curr_x += 35

    # ============================================================
    # 5. FRISSÍTÉS INFORMÁCIÓ
    # ============================================================
    update_text = f"UPDATED\n{update_time}"
    draw.text((curr_x + 15, int(mid_y - 30)), 
              update_text, font=f_update, fill=colors["dim"])

    # Kép mentés
    img.convert("RGB").save(dst, "JPEG", quality=95, subsampling=0)
    print(f"Kép mentve: {dst}")

    # JSON generálás
    timestamp = int(time.time())
    image_url = f"{BASE_URL}/current.jpg?v={timestamp}"
    weather_json = [{
        "location": CITY, 
        "title": f"{weather_hu} {temp}°C",
        "author": "OpenWeatherMap", 
        "image_url": image_url, 
        "url_img": image_url
    }]
    
    with open("weather.json", "w", encoding="utf-8") as f:
        json.dump(weather_json, f, ensure_ascii=False, indent=2)
    
    print("Kész! Minden sikeresen frissítve.")

if __name__ == "__main__":
    main()
