import requests
import json
import os
import time
import math
from datetime import datetime, timezone, timedelta
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageStat

# Konfiguráció
API_KEY = os.environ.get("OWM_API_KEY")
GITHUB_USER = "harsanyiz"
GITHUB_REPO = "weather-wallpaper"
BRANCH = "main"
BASE_URL = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/{BRANCH}/images"

CITY = "Budapest"
WIDGET_WIDTH, WIDGET_HEIGHT = 2200, 220
WIDGET_Y, OFFSET_LEFT, INNER_MARGIN = 80, 135, 80
ICON_SIZE = 80

def get_f(size, bold=False):
    path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    return ImageFont.truetype(path, size) if os.path.exists(path) else ImageFont.load_default()

def get_icon_name(weather_id, is_night):
    """PONTOS mapping a te images/ICONS_PNG80/ mappádhoz"""
    suffix = "night" if is_night else "day"
    if weather_id in range(200, 233): return f"rainy_{suffix}" # Zivatar
    if weather_id in range(300, 500): return f"rainy_{suffix}" # Szitálás
    if weather_id in [511, 611, 612, 613, 615, 616]: return f"sleet_{suffix}" # Ónos/Havas eső
    if weather_id in range(500, 532): return f"rainy_{suffix}" # Eső
    if weather_id in range(600, 623): return f"snow_{suffix}" # Hó
    if weather_id in range(700, 782): return f"foggy_{suffix}" # Köd/Pára
    if weather_id == 800: return f"sunny_{suffix}" # Derült
    if weather_id == 801: return f"cloudy_{suffix}" # Pár felhő
    return f"cloudy_{suffix}" # Felhős/Borult

def load_local_icon(name):
    """Közvetlen elérés a helyi mappából, nincs requests!"""
    path = f"images/ICONS_PNG80/{name}.png"
    try:
        if os.path.exists(path):
            return Image.open(path).convert("RGBA")
        return None
    except: return None

def main():
    try:
        # Adatok lekérése
        resp = requests.get(f"https://api.openweathermap.org/data/2.5/weather?q={CITY}&appid={API_KEY}&units=metric").json()
        f_resp = requests.get(f"https://api.openweathermap.org/data/2.5/forecast?q={CITY}&appid={API_KEY}&units=metric").json()
        
        temp, weather_id = round(resp["main"]["temp"]), resp["weather"][0]["id"]
        tz_offset = resp.get("timezone", 3600)
        now_dt = datetime.now(timezone(timedelta(seconds=tz_offset)))
        update_time = now_dt.strftime("%H:%M")
        is_night = now_dt.timestamp() < resp["sys"]["sunrise"] or now_dt.timestamp() > resp["sys"]["sunset"]
        
        # 1. HÁTTÉRKÉP ÉS ALAPOK
        bg_type = get_icon_name(weather_id, is_night)
        img = Image.open(f"images/{bg_type}.jpg").convert("RGB").resize((3840, 2160))
        
        # Glass bar (a te kódodból)
        overlay = Image.new("RGBA", (WIDGET_WIDTH, WIDGET_HEIGHT), (0, 0, 10, 100))
        img.paste(overlay, (OFFSET_LEFT, WIDGET_Y), overlay)
        
        draw = ImageDraw.Draw(img, "RGBA")
        mid_y, curr_x = WIDGET_Y + (WIDGET_HEIGHT // 2), OFFSET_LEFT + INNER_MARGIN
        colors = {"main": (255,255,255), "dim": (200,200,200,180), "line": (255,255,255,60)}

        # 2. FŐ SZEKCIÓ: IKON + HŐFOK (JAVÍTVA)
        main_icon = load_local_icon(bg_type)
        if main_icon:
            # A te 80x80-as ikonod beillesztése
            img.paste(main_icon, (curr_x, mid_y - 40), main_icon)
        
        curr_x += 100
        draw.text((curr_x, mid_y - 65), f"{temp}°C", font=get_f(90, True), fill=colors["main"])
        
        curr_x += 280
        draw.line([(curr_x, WIDGET_Y + 40), (curr_x, WIDGET_Y + 180)], fill=colors["line"], width=3)
        curr_x += 60

        # 3. ELŐREJELZÉS (3 NAP)
        forecast_list = []
        seen_days = set()
        for entry in f_resp['list']:
            d = datetime.fromtimestamp(entry['dt']).date()
            if d > now_dt.date() and d not in seen_days and datetime.fromtimestamp(entry['dt']).hour >= 12:
                forecast_list.append(entry)
                seen_days.add(d)
            if len(forecast_list) == 3: break

        for day in forecast_list:
            f_icon_name = get_icon_name(day['weather'][0]['id'], False)
            f_icon = load_local_icon(f_icon_name)
            if f_icon:
                # Kicsit kisebb ikon az előrejelzéshez a zsúfoltság ellen
                f_icon_s = f_icon.resize((65, 65), Image.Resampling.LANCZOS)
                img.paste(f_icon_s, (curr_x, mid_y - 75), f_icon_s)
            
            f_temp = f"{round(day['main']['temp'])}°C"
            draw.text((curr_x, mid_y), f_temp, font=get_f(34, True), fill=colors["main"])
            curr_x += 180

        # 4. FRISSÍTÉS IDŐ
        draw.text((curr_x + 50, mid_y - 15), f"UPDATE: {update_time}", font=get_f(24), fill=colors["dim"])

        # MENTÉS ÉS JSON
        img.convert("RGB").save("images/current.jpg", "JPEG", quality=100, subsampling=0)
        v = int(time.time())
        with open("weather.json", "w") as f:
            json.dump([{"image_url": f"{BASE_URL}/current.jpg?v={v}"}], f)

    except Exception as e: print(f"Hiba történt: {e}")

if __name__ == "__main__":
    main()
