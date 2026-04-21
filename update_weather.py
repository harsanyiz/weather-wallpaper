import requests
import json
import os
import time
from datetime import datetime, timezone, timedelta
from PIL import Image, ImageDraw, ImageFont, ImageStat

# --- KONFIG ---
API_KEY = os.environ.get("OWM_API_KEY")
CITY = "Budapest"
WIDGET_Y, OFFSET_LEFT = 80, 135
GITHUB_BASE = "https://raw.githubusercontent.com/harsanyiz/weather-wallpaper/main/images"

def get_f(size, bold=False):
    path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    return ImageFont.truetype(path, size) if os.path.exists(path) else ImageFont.load_default()

def get_icon_name(weather_id, is_night):
    suffix = "night" if is_night else "day"
    if weather_id in range(200, 233): return f"rainy_{suffix}"
    if weather_id in range(300, 532): return f"rainy_{suffix}"
    if weather_id in range(600, 623): return f"snow_{suffix}"
    if weather_id in range(700, 782): return f"foggy_{suffix}"
    if weather_id == 800: return f"sunny_{suffix}"
    return f"cloudy_{suffix}"

def main():
    try:
        # Adatok
        resp = requests.get(f"https://api.openweathermap.org/data/2.5/weather?q={CITY}&appid={API_KEY}&units=metric").json()
        f_resp = requests.get(f"https://api.openweathermap.org/data/2.5/forecast?q={CITY}&appid={API_KEY}&units=metric").json()
        
        temp = round(resp["main"]["temp"])
        weather_id = resp["weather"][0]["id"]
        tz_offset = resp.get("timezone", 3600)
        now_dt = datetime.now(timezone(timedelta(seconds=tz_offset)))
        is_night = now_dt.timestamp() < resp["sys"]["sunrise"] or now_dt.timestamp() > resp["sys"]["sunset"]
        
        # Alapkép betöltése
        bg_name = get_icon_name(weather_id, is_night)
        img = Image.open(f"images/{bg_name}.jpg").convert("RGB").resize((3840, 2160))
        draw = ImageDraw.Draw(img, "RGBA")
        
        # Glass panel
        overlay = Image.new("RGBA", (2200, 220), (0, 0, 15, 120))
        img.paste(overlay, (OFFSET_LEFT, WIDGET_Y), overlay)
        
        mid_y = WIDGET_Y + 110
        curr_x = OFFSET_LEFT + 80
        colors = {"main": (255,255,255), "dim": (200,200,200)}

        # 1. FŐ IKON (Fix elérés az images/ICONS_PNG80 mappából)
        icon_path = f"images/ICONS_PNG80/{bg_name}.png"
        if os.path.exists(icon_path):
            icon = Image.open(icon_path).convert("RGBA")
            img.paste(icon, (curr_x, mid_y - 40), icon)
        
        curr_x += 120
        draw.text((curr_x, mid_y - 65), f"{temp}°C", font=get_f(100, True), fill=colors["main"])
        
        curr_x += 300
        draw.line([(curr_x, WIDGET_Y+40), (curr_x, WIDGET_Y+180)], fill=(255,255,255,60), width=3)
        curr_x += 80

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
            f_id = day['weather'][0]['id']
            f_name = get_icon_name(f_id, False)
            f_icon_path = f"images/ICONS_PNG80/{f_name}.png"
            
            # IKON BEILLESZTÉSE (Ez hiányzott a képedről!)
            if os.path.exists(f_icon_path):
                f_icon = Image.open(f_icon_path).convert("RGBA").resize((70, 70))
                # Pontosan a hőfok fölé pozícionálva
                img.paste(f_icon, (curr_x, mid_y - 85), f_icon)
            
            # HŐFOK
            f_temp = f"{round(day['main']['temp'])}°C"
            draw.text((curr_x, mid_y), f_temp, font=get_f(38, True), fill=colors["main"])
            curr_x += 200

        # Frissítés
        update_txt = f"UPDATE: {now_dt.strftime('%H:%M')}"
        draw.text((curr_x, mid_y - 15), update_txt, font=get_f(24), fill=colors["dim"])

        # Mentés
        img.convert("RGB").save("images/current.jpg", "JPEG", quality=100, subsampling=0)
        
        # JSON
        with open("weather.json", "w") as f:
            json.dump([{"image_url": f"{GITHUB_BASE}/current.jpg?v={int(time.time())}"}], f)

    except Exception as e:
        print(f"HIBA: {e}")

if __name__ == "__main__":
    main()
