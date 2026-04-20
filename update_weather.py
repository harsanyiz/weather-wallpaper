import requests
import json
import os
import time
import math
from datetime import datetime, timezone, timedelta
from PIL import Image, ImageDraw, ImageFont, ImageStat

# Konfiguráció
API_KEY = os.environ.get("OWM_API_KEY")
GITHUB_USER = "harsanyiz"
GITHUB_REPO = "weather-wallpaper"
BRANCH = "main"
BASE_URL = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/{BRANCH}/images"

CITY = "Budapest"
WIDGET_Y = 100
OFFSET_LEFT = 135
INNER_MARGIN = 80

# ============================================================
# GEOMETRIAI IKON RAJZOLÓK
# ============================================================

def draw_sun(draw, pos, size, color=(255, 255, 0)):
    x, y = pos
    r = size // 3
    # Nap korong
    draw.ellipse([x-r, y-r, x+r, y+r], fill=color)
    # Sugarak
    for i in range(8):
        angle = math.radians(i * 45)
        x1, y1 = x + math.cos(angle) * (r + 5), y + math.sin(angle) * (r + 5)
        x2, y2 = x + math.cos(angle) * (r + 15), y + math.sin(angle) * (r + 15)
        draw.line([x1, y1, x2, y2], fill=color, width=3)

def draw_cloud(draw, pos, size, color=(200, 200, 200)):
    x, y = pos
    r = size // 3
    # Három egymásba érő kör alkotja a felhőt
    draw.ellipse([x-r, y-int(r*0.5), x, y+int(r*0.5)], fill=color)
    draw.ellipse([x-int(r*0.5), y-r, x+int(r*0.5), y], fill=color)
    draw.ellipse([x, y-int(r*0.5), x+r, y+int(r*0.5)], fill=color)

def draw_rain(draw, pos, size):
    draw_cloud(draw, pos, size)
    x, y = pos
    r = size // 3
    # Esőcseppek (vonalak)
    for i in range(3):
        drop_x = x - r + (i * r)
        draw.line([drop_x, y+r, drop_x-5, y+r+15], fill=(100, 150, 255), width=2)

def draw_weather_icon(draw, weather_id, pos, size):
    if weather_id == 800:
        draw_sun(draw, pos, size)
    elif 801 <= weather_id <= 804:
        draw_cloud(draw, pos, size)
    elif 500 <= weather_id <= 531:
        draw_rain(draw, pos, size)
    else:
        draw_cloud(draw, pos, size) # Alapértelmezett

# ============================================================

def get_f(size, bold=False):
    path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    if not os.path.exists(path): path = "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf"
    return ImageFont.truetype(path, size) if os.path.exists(path) else ImageFont.load_default()

def main():
    try:
        resp = requests.get(f"https://api.openweathermap.org/data/2.5/weather?q={CITY}&appid={API_KEY}&units=metric").json()
        f_resp = requests.get(f"https://api.openweathermap.org/data/2.5/forecast?q={CITY}&appid={API_KEY}&units=metric").json()

        temp = round(resp["main"]["temp"])
        weather_id = resp["weather"][0]["id"]
        tz_offset = resp.get("timezone", 3600)
        now_dt = datetime.now(timezone(timedelta(seconds=tz_offset)))
        update_time = now_dt.strftime("%H:%M")
        is_night = now_dt.timestamp() < resp["sys"]["sunrise"] or now_dt.timestamp() > resp["sys"]["sunset"]
        
        # Háttérkép kiválasztása (az eredeti logikád szerint)
        bg_type = "sunny" if weather_id == 800 else "cloudy"
        suffix = "night" if is_night else "day"
        img = Image.open(f"images/{bg_type}_{suffix}.jpg").convert("RGB")
    except: return

    if img.size != (3840, 2160):
        img = img.resize((3840, 2160), Image.Resampling.LANCZOS)
    
    draw = ImageDraw.Draw(img)
    colors = {"main": (255,255,255), "dim": (200,200,200), "line": (100,100,100)}
    
    curr_x, mid_y = OFFSET_LEFT + INNER_MARGIN, WIDGET_Y + 100

    # --- 1. SZEKCIÓ: GEOMETRIAI IKON + FOK ---
    draw_weather_icon(draw, weather_id, (curr_x + 50, mid_y), 100)
    curr_x += 150
    
    f_t = get_f(90, True)
    draw.text((curr_x, mid_y - 60), f"{temp}°C", font=f_t, fill=colors["main"])
    
    curr_x += 250
    draw.line([(curr_x, WIDGET_Y+40), (curr_x, WIDGET_Y+160)], fill=colors["line"], width=3)
    curr_x += 80

    # --- 2. SZEKCIÓ: ELŐREJELZÉS GEOMETRIÁVAL ---
    f_list = [e for e in f_resp['list'] if datetime.fromtimestamp(e['dt']).hour >= 12 and datetime.fromtimestamp(e['dt']).date() > now_dt.date()]
    f_v = get_f(36, True)
    
    for day in f_list[:3]:
        day_temp = f"{round(day['main']['temp'])}°C"
        f_id = day['weather'][0]['id']
        
        draw_weather_icon(draw, f_id, (curr_x + 30, mid_y), 60)
        draw.text((curr_x + 80, mid_y - 20), day_temp, font=f_v, fill=colors["main"])
        curr_x += 220

    # FRISSÍTVE tag
    draw.text((curr_x, mid_y - 10), f"FRISSÍTVE: {update_time}", font=get_f(22), fill=colors["dim"])

    # Mentés
    img.save("images/current.jpg", "JPEG", quality=95)
    
    # JSON
    v_param = int(time.time())
    weather_json = [{"location": CITY, "title": f"Weather {temp}C", "image_url": f"{BASE_URL}/current.jpg?v={v_param}"}]
    with open("weather.json", "w", encoding="utf-8") as f:
        json.dump(weather_json, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
