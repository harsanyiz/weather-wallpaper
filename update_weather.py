import requests
import json
import os
import time
from datetime import datetime, timezone, timedelta
from PIL import Image, ImageDraw, ImageFont

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

# Visszatérünk a 4K-hoz, mert a karakterekkel már bírnia kell!
FONT_TEMP = 95        
FONT_ICON = 80   # Külön méret a Unicode ikonnak
FONT_DESC = 32        
FONT_LABEL = 28       
FONT_VALUE = 36       
FONT_UPDATE = 22      

def get_f(size, bold=False):
    # A DejaVuSans-ban benne vannak a különleges időjárás karakterek
    paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf"
    ]
    for p in paths:
        if os.path.exists(p): return ImageFont.truetype(p, size)
    return ImageFont.load_default()

def get_unicode_icon(weather_id):
    if weather_id == 800: return "☀" # Nap
    elif 801 <= weather_id <= 804: return "☁" # Felhő
    elif 500 <= weather_id <= 531: return "☂" # Eső
    elif 600 <= weather_id <= 622: return "❄" # Hó
    elif 200 <= weather_id <= 232: return "⚡" # Villám
    elif 701 <= weather_id <= 741: return "≈" # Köd
    return "☁"

def main():
    try:
        resp = requests.get(f"https://api.openweathermap.org/data/2.5/weather?q={CITY}&appid={API_KEY}&units=metric").json()
        f_resp = requests.get(f"https://api.openweathermap.org/data/2.5/forecast?q={CITY}&appid={API_KEY}&units=metric").json()

        temp, weather_id = round(resp["main"]["temp"]), resp["weather"][0]["id"]
        tz_offset = resp.get("timezone", 3600)
        now_dt = datetime.now(timezone(timedelta(seconds=tz_offset)))
        update_time = now_dt.strftime("%H:%M")
        
        # Háttér választás (marad a JPG, mert az stabil)
        is_night = now_dt.timestamp() < resp["sys"]["sunrise"] or now_dt.timestamp() > resp["sys"]["sunset"]
        bg_name = "sunny_day" if weather_id == 800 and not is_night else "cloudy_day"
        if is_night: bg_name = bg_name.replace("day", "night")
        
        weather_hu = {800: "Derült", 801: "Pár felhő", 802: "Részben felhős", 803: "Felhős", 804: "Borult"}.get(weather_id, "Változékony")
    except: return

    # Alap kép
    img = Image.open(f"images/{bg_name}.jpg" if os.path.exists(f"images/{bg_name}.jpg") else "images/sunny_day.jpg").convert("RGB")
    img = img.resize((3840, 2160), Image.Resampling.LANCZOS)
    draw = ImageDraw.Draw(img)
    
    colors = {"main": (255,255,255,255), "dim": (255,255,255,180), "line": (255,255,255,40)}
    f_t, f_i, f_d, f_l, f_v, f_u = get_f(FONT_TEMP, True), get_f(FONT_ICON), get_f(FONT_DESC), get_f(FONT_LABEL), get_f(FONT_VALUE, True), get_f(FONT_UPDATE)
    
    curr_x, mid_y = OFFSET_LEFT + INNER_MARGIN, WIDGET_Y + 100

    # 1. Szekció: UNICODE IKON + Celsius
    u_icon = get_unicode_icon(weather_id)
    draw.text((curr_x, mid_y - 60), u_icon, font=f_i, fill=(255, 255, 0)) # Sárga ikon a látvány kedvéért
    curr_x += 100

    draw.text((curr_x, mid_y - 65), f"{temp}°C", font=f_t, fill=colors["main"])
    draw.text((curr_x, mid_y + 40), weather_hu.upper(), font=f_d, fill=colors["dim"])
    
    curr_x += draw.textbbox((0,0), f"{temp}°C", font=f_t)[2] + 80
    draw.line([(curr_x, WIDGET_Y+40), (curr_x, WIDGET_Y+160)], fill=colors["line"], width=3)
    curr_x += 80

    # 2. Szekció: Előrejelzés Unicode jelekkel
    f_list = [e for e in f_resp['list'] if datetime.fromtimestamp(e['dt']).hour >= 12 and datetime.fromtimestamp(e['dt']).date() > now_dt.date()]
    for day in f_list[:3]:
        dn = (["Hét", "Ked", "Sze", "Csü", "Pén", "Szo", "Vas"][datetime.fromtimestamp(day['dt']).weekday()]).upper()
        f_icon = get_unicode_icon(day['weather'][0]['id'])
        
        draw.text((curr_x, mid_y - 50), dn, font=f_l, fill=colors["dim"])
        draw.text((curr_x, mid_y), f"{f_icon} {round(day['main']['temp'])}°C", font=f_v, fill=colors["main"])
        curr_x += 200

    # FRISSÍTVE TAG - Jól látható helyen
    draw.text((curr_x, mid_y - 12), f"FRISSÍTVE: {update_time}", font=f_u, fill=colors["dim"])

    # Mentés (Tiszta RGB JPEG)
    img.save("images/current.jpg", "JPEG", quality=95)
    
    # JSON frissítése
    v_param = int(time.time())
    with open("weather.json", "w", encoding="utf-8") as f:
        json.dump([{"location": CITY, "title": f"{u_icon} {temp}C", "image_url": f"{BASE_URL}/current.jpg?v={v_param}"}], f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
