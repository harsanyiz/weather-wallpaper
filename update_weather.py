import requests
import json
from io import BytesIO
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
# KONFIGURÁCIÓ
# ============================================================
CITY = "Budapest"
WIDGET_WIDTH = 2400
WIDGET_HEIGHT = 240
WIDGET_Y = 70
OFFSET_LEFT = 120
INNER_MARGIN = 70

FONT_TEMP   = 96
FONT_DESC   = 34
FONT_LABEL  = 30
FONT_VALUE  = 38
FONT_UPDATE = 26
FONT_SUN    = 24
FONT_TIMESTAMP = 32
ICON_SIZE   = 80
# ============================================================

# Ikon cache (hogy ne töltögessük feleslegesen)
icon_cache = {}

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

def get_image_name(weather_id, is_night):
    suffix = "night" if is_night else "day"
    if weather_id in [611, 612, 613, 615, 616]: return f"sleet_{suffix}"
    elif weather_id in [620, 621, 622, 600, 601, 602]: return f"snow_{suffix}"
    elif weather_id == 800: return f"sunny_{suffix}"
    else: return f"cloudy_{suffix}"

def get_icon_name(weather_id, is_night):
    """OWM weather_id → ICONS_PNG80 fájlnév mapping"""
    # Zivatar
    if weather_id in range(200, 233):
        return "night_rain_thunder" if is_night else "day_rain_thunder"
    # Szitálás
    if weather_id in range(300, 322):
        return "night_rain" if is_night else "day_rain"
    # Ónos eső / vegyes
    if weather_id in [511, 611, 612, 613, 615, 616]:
        return "night_sleet" if is_night else "day_sleet"
    # Eső
    if weather_id in range(500, 532):
        return "night_rain" if is_night else "day_rain"
    # Hó
    if weather_id in range(600, 623):
        return "night_snow" if is_night else "day_snow"
    # Köd / pára
    if weather_id in [701, 711, 721, 741]:
        return "mist"
    if weather_id in [731, 751, 761, 762]:
        return "fog"
    # Tornádó / szél
    if weather_id == 771: return "wind"
    if weather_id == 781: return "tornado"
    # Derült
    if weather_id == 800:
        return "night_clear" if is_night else "day_clear"
    # Pár felhő
    if weather_id == 801:
        return "night_partial_cloud" if is_night else "day_partial_cloud"
    # Felhős
    if weather_id in [802, 803]:
        return "night_partial_cloud" if is_night else "day_partial_cloud"
    # Borult
    if weather_id == 804:
        return "overcast"
    return "cloudy"

def load_icon(name):
    """PNG ikon betöltése cache-el"""
    if name in icon_cache and icon_cache[name] is not None:
        return icon_cache[name]
    
    url = f"{BASE_URL}/ICONS_PNG80/{name}.png"
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        icon = Image.open(BytesIO(r.content)).convert("RGBA")
        icon_cache[name] = icon
        return icon
    except Exception as e:
        print(f"Ikon hiba ({name}): {e}")
        # Fallback: próbálkozz egy alap ikonnal
        if name != "cloudy":
            return load_icon("cloudy")
        icon_cache[name] = None
        return None

def paste_icon(img, icon, cx, cy):
    """Ikon beillesztése – cx/cy a középpont."""
    if icon is None: return
    img.paste(icon, (cx - ICON_SIZE//2, cy - ICON_SIZE//2), icon)

def get_weather_hu(weather_id):
    mapping = {800: "DERULT", 801: "PARTS CLOUDY", 802: "MOSTLY CLOUDY",
               803: "CLOUDY", 804: "OVERCAST", 511: "FREEZING RAIN"}
    return mapping.get(weather_id, "VARIABLE")

def get_forecast_hu(weather_id):
    if weather_id == 800: return "SUN"
    elif weather_id in [801, 802]: return "CLOUD"
    elif weather_id in [803, 804]: return "OVER"
    elif weather_id in range(500, 532): return "RAIN"
    elif weather_id in range(300, 322): return "DRIZZLE"
    elif weather_id in range(600, 623): return "SNOW"
    elif weather_id in range(200, 233): return "STORM"
    return "MIXED"

def get_day_hu(date_obj):
    napok = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]
    return napok[date_obj.weekday()]

def get_text_colors(brightness):
    if brightness > 145:
        return {"main": (0,0,0,230), "dim": (0,0,0,160), "line": (0,0,0,80), "timestamp": (200,100,0,255)}
    return {"main": (255,255,255,255), "dim": (255,255,255,180), "line": (255,255,255,60), "timestamp": (255,255,100,255)}

def draw_vertical_divider(draw, x, y_start, y_end, colors):
    """Egyszerű függőleges elválasztó (gyorsabb)"""
    draw.line([(x, y_start), (x, y_end)], fill=colors["line"], width=2)
    draw.line([(x+3, y_start), (x+3, y_end)], fill=colors["line"], width=1)

def draw_glass_bar(img, bx, by, bw, bh):
    """Átlátszó blur sáv a widget mögött"""
    region = img.crop((bx, by, bx + bw, by + bh))
    blurred = region.filter(ImageFilter.GaussianBlur(35))
    mask = Image.new("L", (bw, bh), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle((0, 0, bw, bh), radius=40, fill=200)
    overlay = Image.new("RGBA", (bw, bh), (0, 0, 10, 100))
    blurred = blurred.convert("RGBA")
    blurred.putalpha(mask)
    result = Image.alpha_composite(blurred, overlay)
    img.paste(result, (bx, by), result)
    return img

def format_sun_time(ts, tz_offset):
    dt = datetime.fromtimestamp(ts, tz=timezone(timedelta(seconds=tz_offset)))
    return dt.strftime("%H:%M")

def main():
    try:
        print("Időjárás adatok lekérése...")
        resp = requests.get(f"https://api.openweathermap.org/data/2.5/weather?q={CITY}&appid={API_KEY}&units=metric")
        resp.raise_for_status()
        resp = resp.json()
        
        f_resp = requests.get(f"https://api.openweathermap.org/data/2.5/forecast?q={CITY}&appid={API_KEY}&units=metric")
        f_resp.raise_for_status()
        f_resp = f_resp.json()

        temp = round(resp["main"]["temp"])
        feels = round(resp["main"]["feels_like"])
        humidity = resp["main"]["humidity"]
        wind = round(resp["wind"]["speed"] * 3.6)
        weather_id = resp["weather"][0]["id"]
        tz_offset = resp.get("timezone", 3600)
        now_dt = datetime.now(timezone(timedelta(seconds=tz_offset)))
        update_time = now_dt.strftime("%H:%M")
        full_timestamp = now_dt.strftime("%Y-%m-%d %H:%M:%S")
        is_night = now_dt.timestamp() < resp["sys"]["sunrise"] or now_dt.timestamp() > resp["sys"]["sunset"]
        
        image_name = get_image_name(weather_id, is_night)
        icon_name = get_icon_name(weather_id, is_night)
        weather_hu = get_weather_hu(weather_id)
        sunrise_str = format_sun_time(resp["sys"]["sunrise"], tz_offset)
        sunset_str = format_sun_time(resp["sys"]["sunset"], tz_offset)

        forecast_list = []
        seen_days = set()
        today = now_dt.date()
        for entry in f_resp['list']:
            dt_obj = datetime.fromtimestamp(entry['dt'], tz=timezone(timedelta(seconds=tz_offset)))
            if dt_obj.date() > today and dt_obj.date() not in seen_days and dt_obj.hour >= 12:
                forecast_list.append(entry)
                seen_days.add(dt_obj.date())
            if len(forecast_list) == 3: break
                
        print(f"Háttérkép: {image_name}.jpg")
        print(f"Ikon: {icon_name}.png")
        
    except Exception as e:
        print(f"Hiba az API hívásnál: {e}")
        return

    src = f"images/{image_name}.jpg"
    dst = "images/current.jpg"
    
    try:
        img = Image.open(src).convert("RGB")
        if img.size != (3840, 2160):
            img = img.resize((3840, 2160), Image.Resampling.LANCZOS)
    except Exception as e:
        print(f"Hiba a kép betöltésénél: {e}")
        return

    W, H = img.size
    bx = OFFSET_LEFT
    by = WIDGET_Y
    bw = WIDGET_WIDTH
    bh = WIDGET_HEIGHT

    # Ikon betöltése
    weather_icon = load_icon(icon_name)

    img = img.convert("RGBA")
    img = draw_glass_bar(img, bx, by, bw, bh)

    region = img.crop((bx, by, bx + bw, by + bh)).convert("L")
    avg_brightness = ImageStat.Stat(region).mean[0]
    colors = get_text_colors(avg_brightness)

    draw = ImageDraw.Draw(img)

    f_temp = get_f(FONT_TEMP, True)
    f_desc = get_f(FONT_DESC)
    f_label = get_f(FONT_LABEL)
    f_value = get_f(FONT_VALUE, True)
    f_update = get_f(FONT_UPDATE)
    f_sun = get_f(FONT_SUN)
    f_timestamp = get_f(FONT_TIMESTAMP, True)

    curr_x = int(bx + INNER_MARGIN)
    mid_y = int(by + bh // 2)

    # ============================================================
    # 1. SZEKCIÓ: NAP + HŐMÉRSÉKLET + LEÍRÁS + IKON
    # ============================================================
    day_txt = get_day_hu(now_dt)
    temp_txt = f"{temp}C"
    desc_txt = weather_hu

    day_w = draw.textbbox((0,0), day_txt, font=f_label)[2]
    temp_w = draw.textbbox((0,0), temp_txt, font=f_temp)[2]
    desc_w = draw.textbbox((0,0), desc_txt, font=f_desc)[2]
    max_w = max(day_w, temp_w, desc_w)

    draw.text((int(curr_x + (max_w - day_w) / 2), int(mid_y - 85)), 
              day_txt, font=f_label, fill=colors["dim"])
    draw.text((int(curr_x + (max_w - temp_w) / 2), int(mid_y - 55)), 
              temp_txt, font=f_temp, fill=colors["main"])
    draw.text((int(curr_x + (max_w - desc_w) / 2), int(mid_y + 45)), 
              desc_txt, font=f_desc, fill=colors["dim"])

    # Ikon a hőfok jobb oldalán
    paste_icon(img, weather_icon, int(curr_x + max_w + 40 + ICON_SIZE//2), mid_y)
    curr_x += max_w + 40 + ICON_SIZE + 30

    draw_vertical_divider(draw, curr_x, by+35, by+bh-35, colors)
    curr_x += 35

    # ============================================================
    # 2. SZEKCIÓ: ADATOK
    # ============================================================
    fields = [
        ("FEELS", f"{feels}C"),
        ("WIND", f"{wind} KM/H"),
        ("HUMID", f"{humidity}%"),
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

    draw_vertical_divider(draw, curr_x, by+35, by+bh-35, colors)
    curr_x += 35

    # ============================================================
    # 3. SZEKCIÓ: NAPKELTE / NAPNYUGTA
    # ============================================================
    sun_label = "SUNRISE / SUNSET"
    sun_val = f"{sunrise_str} - {sunset_str}"
    
    slw = draw.textbbox((0,0), sun_label, font=f_sun)[2]
    svw = draw.textbbox((0,0), sun_val, font=f_value)[2]
    col_w = max(slw, svw)
    
    draw.text((int(curr_x + (col_w - slw)/2), int(mid_y - 48)), 
              sun_label, font=f_sun, fill=colors["dim"])
    draw.text((int(curr_x + (col_w - svw)/2), int(mid_y + 5)), 
              sun_val, font=f_value, fill=colors["main"])
    
    curr_x += col_w + 75
    draw_vertical_divider(draw, curr_x, by+35, by+bh-35, colors)
    curr_x += 35

    # ============================================================
    # 4. SZEKCIÓ: 3 NAPOS ELŐREJELZÉS (JAVÍTOTT POZÍCIÓKKAL)
    # ============================================================
    for i, day in enumerate(forecast_list):
        dt_obj = datetime.fromtimestamp(day['dt'], tz=timezone(timedelta(seconds=tz_offset)))
        day_name = get_day_hu(dt_obj)
        temp_val = f"{round(day['main']['temp'])}C"
        weather_desc = get_forecast_hu(day['weather'][0]['id'])
        
        nw = draw.textbbox((0,0), day_name, font=f_label)[2]
        vw = draw.textbbox((0,0), temp_val, font=f_value)[2]
        dw = draw.textbbox((0,0), weather_desc, font=f_sun)[2]
        col_w = max(nw, vw, dw)
        
        # JAVÍTVA: egységes pozíciók a többi szekcióval
        draw.text((int(curr_x + (col_w - nw)/2), int(mid_y - 48)), 
                  day_name, font=f_label, fill=colors["dim"])
        draw.text((int(curr_x + (col_w - vw)/2), int(mid_y + 5)), 
                  temp_val, font=f_value, fill=colors["main"])
        draw.text((int(curr_x + (col_w - dw)/2), int(mid_y + 50)), 
                  weather_desc, font=f_sun, fill=colors["dim"])
        
        curr_x += col_w + 50
        
        if i < len(forecast_list) - 1:
            draw.line([(curr_x - 20, mid_y - 40), (curr_x - 20, mid_y + 40)], 
                     fill=colors["line"], width=1)

    draw_vertical_divider(draw, curr_x, by+35, by+bh-35, colors)
    curr_x += 35

    # ============================================================
    # 5. FRISSÍTÉS
    # ============================================================
    update_text = f"UPDATED\n{update_time}"
    draw.text((curr_x + 15, int(mid_y - 30)), 
              update_text, font=f_update, fill=colors["dim"])

    # ============================================================
    # 6. NAGY IDŐBÉLYEG A KÉP ALJÁN
    # ============================================================
    timestamp_y = H - 70
    
    # Háttérsáv az időbélyegnek
    timestamp_bg = Image.new('RGBA', (W, 60), (0, 0, 0, 160))
    img.paste(timestamp_bg, (0, timestamp_y - 5), timestamp_bg)
    
    # Időbélyeg szöveg középre igazítva
    timestamp_text = f"LAST UPDATE: {full_timestamp} UTC"
    timestamp_w = draw.textbbox((0,0), timestamp_text, font=f_timestamp)[2]
    draw.text((int((W - timestamp_w) / 2), timestamp_y), 
              timestamp_text, font=f_timestamp, fill=colors["timestamp"])

    # Mentés
    img.convert("RGB").save(dst, "JPEG", quality=92)
    print(f"Kép mentve: {dst} - {full_timestamp}")

    # JSON generálás
    v_param = int(time.time())
    image_url = f"{BASE_URL}/current.jpg?v={v_param}"
    weather_json = [{
        "location": CITY, 
        "title": f"{weather_hu} {temp}C",
        "author": "OpenWeatherMap", 
        "image_url": image_url, 
        "url_img": image_url
    }]
    
    with open("weather.json", "w", encoding="utf-8") as f:
        json.dump(weather_json, f, ensure_ascii=False, indent=2)
    
    print("Kész!")

if __name__ == "__main__":
    main()
