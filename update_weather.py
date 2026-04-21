import requests
import json
import os
import time
from datetime import datetime, timezone, timedelta
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageStat

# Konfiguráció
API_KEY = os.environ.get("OWM_API_KEY")
CITY = "Budapest"
WIDGET_Y, OFFSET_LEFT, INNER_MARGIN = 100, 135, 80
ICON_SIZE = 80 

def get_f(size, bold=False):
    path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    return ImageFont.truetype(path, size) if os.path.exists(path) else ImageFont.load_default()

def get_icon_name(weather_id, is_night):
    suffix = "night" if is_night else "day"
    if weather_id in range(200, 233): return f"rainy_{suffix}"
    if weather_id in range(300, 532): return f"rainy_{suffix}"
    if weather_id in [511, 611, 612, 613, 615, 616]: return f"sleet_{suffix}"
    if weather_id in range(600, 623): return f"snow_{suffix}"
    if weather_id in range(700, 782): return f"foggy_{suffix}"
    if weather_id == 800: return f"sunny_{suffix}"
    return f"cloudy_{suffix}"

def load_local_icon(name):
    """A hálózati letöltés helyett a helyi mappából olvassa be a 80x80-as PNG-t"""
    path = f"images/ICONS_PNG80/{name}.png"
    try:
        if os.path.exists(path):
            return Image.open(path).convert("RGBA")
        else:
            print(f"Hiba: Az ikon nem található: {path}")
            return None
    except Exception as e:
        print(f"Hiba az ikon betöltésekor: {e}")
        return None

def main():
    try:
        resp = requests.get(f"https://api.openweathermap.org/data/2.5/weather?q={CITY}&appid={API_KEY}&units=metric").json()
        f_resp = requests.get(f"https://api.openweathermap.org/data/2.5/forecast?q={CITY}&appid={API_KEY}&units=metric").json()
        
        temp, weather_id = round(resp["main"]["temp"]), resp["weather"][0]["id"]
        tz_offset = resp.get("timezone", 3600)
        now_dt = datetime.now(timezone(timedelta(seconds=tz_offset)))
        is_night = now_dt.timestamp() < resp["sys"]["sunrise"] or now_dt.timestamp() > resp["sys"]["sunset"]
        
        # Háttérkép betöltése
        bg_name = get_icon_name(weather_id, is_night)
        img = Image.open(f"images/{bg_name}.jpg").convert("RGB").resize((3840, 2160))
        draw = ImageDraw.Draw(img, "RGBA")
        
        mid_y, curr_x = WIDGET_Y + 100, OFFSET_LEFT + INNER_MARGIN
        colors = {"main": (255,255,255), "dim": (200,200,200), "line": (255,255,255,40)}

        # 1. FŐ IKON BEILLESZTÉSE (HELYI FÁJL!)
        main_icon = load_local_icon(bg_name)
        if main_icon:
            img.paste(main_icon, (curr_x, mid_y - 40), main_icon)
        
        curr_x += 100
        draw.text((curr_x, mid_y - 60), f"{temp}°C", font=get_f(90, True), fill=colors["main"])
        
        # Elválasztó és adatok
        curr_x += 250
        draw.line([(curr_x, WIDGET_Y + 40), (curr_x, WIDGET_Y + 160)], fill=colors["line"], width=3)
        curr_x += 60

        # 2. ELŐREJELZÉS IKONOKKAL
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
                # Kicsit kisebb ikon az előrejelzéshez
                f_icon_small = f_icon.resize((60, 60), Image.Resampling.LANCZOS)
                img.paste(f_icon_small, (curr_x, mid_y - 70), f_icon_small)
            
            draw.text((curr_x, mid_y), f"{round(day['main']['temp'])}°C", font=get_f(30, True), fill=colors["main"])
            curr_x += 160

        # Mentés
        img.convert("RGB").save("images/current.jpg", "JPEG", quality=100, subsampling=0)
        
        # JSON frissítés a cache miatt
        with open("weather.json", "w") as f:
            json.dump([{"image_url": f"https://raw.githubusercontent.com/harsanyiz/weather-wallpaper/main/images/current.jpg?v={int(time.time())}"}], f)

    except Exception as e:
        print(f"Hiba: {e}")

if __name__ == "__main__":
    main()
