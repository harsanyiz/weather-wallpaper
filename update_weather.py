import requests
import json
import os
import time
import math
from datetime import datetime, timezone, timedelta
from PIL import Image, ImageDraw, ImageFont

# Konfiguráció
API_KEY = os.environ.get("OWM_API_KEY")
GITHUB_USER = "harsanyiz"
GITHUB_REPO = "weather-wallpaper"
BRANCH = "main"
BASE_URL = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/{BRANCH}/images"

CITY = "Budapest"
# Full HD alapú koordináták
WIDGET_Y = 60
OFFSET_LEFT = 70

def draw_sun(draw, pos, size, color=(255, 255, 0)):
    x, y = pos
    r = size // 3
    draw.ellipse([x-r, y-r, x+r, y+r], fill=color)
    for i in range(8):
        angle = math.radians(i * 45)
        x1, y1 = x + math.cos(angle) * (r + 5), y + math.sin(angle) * (r + 5)
        x2, y2 = x + math.cos(angle) * (r + 15), y + math.sin(angle) * (r + 15)
        draw.line([x1, y1, x2, y2], fill=color, width=3)

def draw_cloud(draw, pos, size, color=(220, 220, 220)):
    x, y = pos
    r = size // 3
    draw.ellipse([x-r, y-int(r*0.4), x, y+int(r*0.4)], fill=color)
    draw.ellipse([x-int(r*0.4), y-r, x+int(r*0.4), y], fill=color)
    draw.ellipse([x, y-int(r*0.4), x+r, y+int(r*0.4)], fill=color)

def draw_rain(draw, pos, size):
    draw_cloud(draw, pos, size)
    x, y = pos
    r = size // 3
    for i in range(3):
        dx = x - r + (i * r)
        draw.line([dx, y+r, dx-3, y+r+10], fill=(100, 150, 255), width=2)

def draw_weather_icon(draw, weather_id, pos, size):
    if weather_id == 800: draw_sun(draw, pos, size)
    elif 801 <= weather_id <= 804: draw_cloud(draw, pos, size)
    elif 500 <= weather_id <= 531: draw_rain(draw, pos, size)
    else: draw_cloud(draw, pos, size)

def get_f(size, bold=False):
    path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    if not os.path.exists(path): path = "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf"
    return ImageFont.truetype(path, size) if os.path.exists(path) else ImageFont.load_default()

def main():
    try:
        resp = requests.get(f"https://api.openweathermap.org/data/2.5/weather?q={CITY}&appid={API_KEY}&units=metric").json()
        f_resp = requests.get(f"https://api.openweathermap.org/data/2.5/forecast?q={CITY}&appid={API_KEY}&units=metric").json()
        temp, weather_id = round(resp["main"]["temp"]), resp["weather"][0]["id"]
        tz_offset = resp.get("timezone", 3600)
        now_dt = datetime.now(timezone(timedelta(seconds=tz_offset)))
        update_time = now_dt.strftime("%H:%M")
        
        is_night = now_dt.timestamp() < resp["sys"]["sunrise"] or now_dt.timestamp() > resp["sys"]["sunset"]
        bg_name = "sunny" if weather_id == 800 else "cloudy"
        suffix = "night" if is_night else "day"
        
        img = Image.open(f"images/{bg_name}_{suffix}.jpg").convert("RGB")
    except: return

    # Átméretezés Full HD-ra a TV/Launcher kedvéért
    img = img.resize((1920, 1080), Image.Resampling.LANCZOS)
    draw = ImageDraw.Draw(img)
    
    mid_y = WIDGET_Y + 50
    curr_x = OFFSET_LEFT + 40

    # Fő ikon és hőmérséklet
    draw_weather_icon(draw, weather_id, (curr_x + 30, mid_y), 60)
    curr_x += 80
    draw.text((curr_x, mid_y - 35), f"{temp}°C", font=get_f(50, True), fill=(255,255,255))
    
    # Előrejelzés (kicsit beljebb tolva)
    curr_x += 180
    draw.line([(curr_x, WIDGET_Y+20), (curr_x, WIDGET_Y+80)], fill=(150,150,150), width=2)
    curr_x += 40
    
    f_list = [e for e in f_resp['list'] if datetime.fromtimestamp(e['dt']).hour >= 12 and datetime.fromtimestamp(e['dt']).date() > now_dt.date()]
    for day in f_list[:2]:
        draw_weather_icon(draw, day['weather'][0]['id'], (curr_x + 20, mid_y), 40)
        draw.text((curr_x + 50, mid_y - 15), f"{round(day['main']['temp'])}°C", font=get_f(24, True), fill=(255,255,255))
        curr_x += 140

    # Frissítve felirat
    draw.text((curr_x + 20, mid_y - 10), f"FRISSÍTVE: {update_time}", font=get_f(16), fill=(200,200,200))

    # Szuper-tömörített JPEG mentés
    img.save("images/current.jpg", "JPEG", quality=80, optimize=True)
    
    v_param = int(time.time())
    with open("weather.json", "w", encoding="utf-8") as f:
        json.dump([{"location": CITY, "title": f"{temp}C", "image_url": f"{BASE_URL}/current.jpg?v={v_param}"}], f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
