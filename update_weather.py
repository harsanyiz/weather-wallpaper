import requests
import json
from io import BytesIO
import os
import time
import math
from datetime import datetime, timezone, timedelta
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageStat

# Konfiguráció és API kulcsok
API_KEY = os.environ.get("OWM_API_KEY")
GITHUB_USER = "harsanyiz"
GITHUB_REPO = "weather-wallpaper"
BRANCH = "main"
BASE_URL = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/{BRANCH}/images"

# ============================================================
# 4K-S HORIZONTÁLIS DESIGN KONFIGURÁCIÓ
# ============================================================
CITY = "Budapest"
WIDGET_WIDTH = 2200   
WIDGET_HEIGHT = 200   
WIDGET_Y = 100        
OFFSET_LEFT = 135     
INNER_MARGIN = 80     

# 4K-s betűméretek
FONT_TEMP = 90        
FONT_DESC = 32        
FONT_LABEL = 28       
FONT_VALUE = 36       
FONT_UPDATE = 24      
ICON_SIZE = 80        # A te általad javasolt stabil méret
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
    """OWM weather_id → ICONS_PNG80 fájlnév mapping"""
    suffix = "night" if is_night else "day"
    if weather_id in range(200, 233): return f"rainy_{suffix}" # Zivatar -> Eső ikon
    if weather_id in range(300, 322): return f"rainy_{suffix}" # Szitálás
    if weather_id in [511, 611, 612, 613, 615, 616]: return f"sleet_{suffix}" # Ónos eső
    if weather_id in range(500, 532): return f"rainy_{suffix}" # Eső
    if weather_id in range(600, 623): return f"snow_{suffix}" # Hó
    if weather_id in range(700, 782): return f"foggy_{suffix}" # Köd/Pára
    if weather_id == 800: return f"sunny_{suffix}" # Derült
    return f"cloudy_{suffix}" # Felhős (alapértelmezett)

def load_icon(name):
    """PNG ikon betöltése a repóból"""
    url = f"{BASE_URL}/ICONS_PNG80/{name}.png"
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        return Image.open(BytesIO(r.content)).convert("RGBA")
    except:
        return None

def main():
    try:
        resp = requests.get(f"https://api.openweathermap.org/data/2.5/weather?q={CITY}&appid={API_KEY}&units=metric").json()
        f_resp = requests.get(f"https://api.openweathermap.org/data/2.5/forecast?q={CITY}&appid={API_KEY}&units=metric").json()

        temp, weather_id = round(resp["main"]["temp"]), resp["weather"][0]["id"]
        tz_offset = resp.get("timezone", 3600)
        now_dt = datetime.now(timezone(timedelta(seconds=tz_offset)))
        update_time = now_dt.strftime("%H:%M")
        is_night = now_dt.timestamp() < resp["sys"]["sunrise"] or now_dt.timestamp() > resp["sys"]["sunset"]
        
        # Háttérkép és Ikon neve
        image_name = get_icon_name(weather_id, is_night) # A háttérkép neve megegyezik az ikonéval alapból
        icon_img = load_icon(image_name)
    except: return

    # Háttérkép betöltése és 4K-ra méretezése
    img = Image.open(f"images/{image_name}.jpg").convert("RGB")
    img = img.resize((3840, 2160), Image.Resampling.LANCZOS)
    
    draw = ImageDraw.Draw(img, "RGBA")
    bx, by, bw, bh = OFFSET_LEFT, WIDGET_Y, WIDGET_WIDTH, WIDGET_HEIGHT
    
    # Dinamikus színválasztás a háttér alapján
    region = img.crop((bx, by, bx + bw, by + bh)).convert("L")
    avg_brightness = ImageStat.Stat(region).mean[0]
    colors = {"main": (255,255,255), "dim": (200,200,200), "line": (255,255,255,40)} if avg_brightness < 145 else {"main": (0,0,0), "dim": (50,50,50), "line": (0,0,0,40)}

    f_t, f_l, f_v = get_f(FONT_TEMP, True), get_f(FONT_LABEL), get_f(FONT_VALUE, True)
    curr_x, mid_y = int(bx + INNER_MARGIN), int(by + bh // 2)

    # --- 1. SZEKCIÓ: IKON + HŐFOK ---
    if icon_img:
        img.paste(icon_img, (curr_x, mid_y - 40), icon_img)
    
    curr_x += 100
    draw.text((curr_x, mid_y - 60), f"{temp}°C", font=f_t, fill=colors["main"])
    
    curr_x += 250
    draw.line([(curr_x, by+40), (curr_x, by+bh-40)], fill=colors["line"], width=3)
    curr_x += 80

    # --- 2. SZEKCIÓ: ADATOK (ÉRZET, SZÉL) ---
    fields = [("Érzet", f"{round(resp['main']['feels_like'])}°C"), ("Szél", f"{round(resp['wind']['speed']*3.6)} km/h")]
    for label, val in fields:
        draw.text((curr_x, mid_y - 45), label.upper(), font=f_l, fill=colors["dim"])
        draw.text((curr_x, mid_y), val, font=f_v, fill=colors["main"])
        curr_x += 200

    # --- 3. SZEKCIÓ: FRISSÍTÉS ---
    draw.text((curr_x, mid_y - 12), f"FRISSÍTVE: {update_time}", font=get_f(FONT_UPDATE), fill=colors["dim"])

    # Mentés és JSON
    img.save("images/current.jpg", "JPEG", quality=100, subsampling=0)
    v_param = int(time.time())
    with open("weather.json", "w", encoding="utf-8") as f:
        json.dump([{"location": CITY, "title": f"{temp}C", "image_url": f"{BASE_URL}/current.jpg?v={v_param}"}], f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
