import requests
import json
import os
import time
from datetime import datetime, timezone, timedelta
from PIL import Image, ImageDraw, ImageFont, ImageStat

# API kulcs és adatok
API_KEY = os.environ.get("OWM_API_KEY")
GITHUB_USER = "harsanyiz"
GITHUB_REPO = "weather-wallpaper"
BRANCH = "main"
BASE_URL = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/{BRANCH}/images"

# ============================================================
# 4K KONFIGURÁCIÓ - PNG IKONOS DESIGN
# ============================================================
CITY = "Budapest"
WIDGET_Y = 100        
OFFSET_LEFT = 135     # Media ikonhoz igazítva
INNER_MARGIN = 60     

# Betűméretek 4K-hoz
FONT_TEMP = 95        
FONT_DESC = 32        
FONT_LABEL = 28       
FONT_VALUE = 36       
FONT_UPDATE = 22      
# ============================================================

def get_f(size, bold=False):
    # Betűtípus keresése (Linux/GitHub Actions barát módon)
    paths = [
        "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    ]
    for p in paths:
        if os.path.exists(p): return ImageFont.truetype(p, size)
    return ImageFont.load_default()

def get_icon_name(weather_id, is_night):
    """Leképezi az OpenWeather ID-t a te PNG fájlneveidre"""
    suffix = "night" if is_night else "day"
    if weather_id == 800: return f"{suffix}_clear"
    elif weather_id in [801, 802]: return f"{suffix}_partial_cloud"
    elif weather_id in [803, 804]: return "overcast"
    elif 500 <= weather_id <= 531: return f"{suffix}_rain"
    elif 600 <= weather_id <= 622: return f"{suffix}_snow"
    elif 701 <= weather_id <= 741: return "fog"
    elif weather_id >= 200 and weather_id <= 232: return "thunder"
    return "cloudy"

def main():
    try:
        # Adatok lekérése
        curr_r = requests.get(f"https://api.openweathermap.org/data/2.5/weather?q={CITY}&appid={API_KEY}&units=metric").json()
        fore_r = requests.get(f"https://api.openweathermap.org/data/2.5/forecast?q={CITY}&appid={API_KEY}&units=metric").json()

        temp = round(curr_r["main"]["temp"])
        weather_id = curr_r["weather"][0]["id"]
        tz = timezone(timedelta(seconds=curr_r.get("timezone", 3600)))
        now_dt = datetime.now(tz)
        update_time = now_dt.strftime("%H:%M")
        is_night = now_dt.timestamp() < curr_r["sys"]["sunrise"] or now_dt.timestamp() > curr_r["sys"]["sunset"]
        
        icon_name = get_icon_name(weather_id, is_night)
        weather_hu = {800: "Derült", 801: "Pár felhő", 802: "Részben felhős", 803: "Felhős", 804: "Borult"}.get(weather_id, "Változékony")
    except Exception as e:
        print(f"Hiba: {e}"); return

    # Háttérkép betöltése (4K)
    bg_img = "night_clear" if is_night else "day_clear"
    img = Image.open(f"images/{bg_img}.jpg").convert("RGB")
    img = img.resize((3840, 2160), Image.Resampling.LANCZOS).convert("RGBA")
    draw = ImageDraw.Draw(img)

    # Színek és fontok
    colors = {"main": (255,255,255,255), "dim": (255,255,255,180), "line": (255,255,255,60)}
    f_t, f_d, f_l, f_v, f_u = get_f(FONT_TEMP, True), get_f(FONT_DESC), get_f(FONT_LABEL), get_f(FONT_VALUE, True), get_f(FONT_UPDATE)
    
    mid_y = WIDGET_Y + 100
    curr_x = OFFSET_LEFT + INNER_MARGIN

    # --- 1. SZEKCIÓ: NAGY PNG IKON + HŐFOK ---
    icon_path = f"PNG/{icon_name}.png"
    if os.path.exists(icon_path):
        m_icon = Image.open(icon_path).convert("RGBA")
        # 4K-n a 160x160-as méret szép és arányos
        m_icon = m_icon.resize((160, 160), Image.Resampling.LANCZOS)
        img.paste(m_icon, (int(curr_x), int(mid_y - 80)), m_icon)
        curr_x += 190

    day_name = ["Hétfő", "Kedd", "Szerda", "Csütörtök", "Péntek", "Szombat", "Vasárnap"][now_dt.weekday()].upper()
    
    # Nap, Hőfok, Leírás egymás alá, az ikon mellé
    draw.text((int(curr_x), int(mid_y - 90)), day_name, font=f_l, fill=colors["dim"])
    draw.text((int(curr_x), int(mid_y - 65)), f"{temp}°C", font=f_t, fill=colors["main"])
    draw.text((int(curr_x), int(mid_y + 40)), weather_hu.upper(), font=f_d, fill=colors["dim"])
    
    curr_x += draw.textbbox((0,0), f"{temp}°C", font=f_t)[2] + 80
    draw.line([(curr_x, WIDGET_Y+40), (curr_x, WIDGET_Y+160)], fill=colors["line"], width=3)
    curr_x += 80

    # --- 2. SZEKCIÓ: RÉSZLETEK (ÉRZET, SZÉL, PÁRA) ---
    details = [
        ("Érzet", f"{round(curr_r['main']['feels_like'])}°C"),
        ("Szél", f"{round(curr_r['wind']['speed']*3.6)} km/h"),
        ("Pára", f"{curr_r['main']['humidity']}%")
    ]
    for label, val in details:
        draw.text((int(curr_x), int(mid_y - 50)), label.upper(), font=f_l, fill=colors["dim"])
        draw.text((int(curr_x), int(mid_y)), val, font=f_v, fill=colors["main"])
        curr_x += max(draw.textbbox((0,0), label.upper(), font=f_l)[2], draw.textbbox((0,0), val, font=f_v)[2]) + 90

    # --- 3. SZEKCIÓ: ELŐREJELZÉS ---
    draw.line([(curr_x, WIDGET_Y+40), (curr_x, WIDGET_Y+160)], fill=colors["line"], width=3)
    curr_x += 80
    
    forecast_list = []
    seen_days = set()
    for entry in fore_r['list']:
        d_obj = datetime.fromtimestamp(entry['dt'], tz=tz)
        if d_obj.date() > now_dt.date() and d_obj.date() not in seen_days and d_obj.hour >= 12:
            forecast_list.append(entry)
            seen_days.add(d_obj.date())
        if len(forecast_list) == 3: break

    for day in forecast_list:
        d_name = ["Hét", "Ked", "Sze", "Csü", "Pén", "Szo", "Vas"][datetime.fromtimestamp(day['dt']).weekday()].upper()
        draw.text((int(curr_x), int(mid_y - 50)), d_name, font=f_l, fill=colors["dim"])
        draw.text((int(curr_x), int(mid_y)), f"{round(day['main']['temp'])}°C", font=f_v, fill=colors["main"])
        curr_x += 160

    # --- 4. FRISSÍTÉS ---
    draw.text((int(curr_x + 20), int(mid_y - 15)), f"FRISSÍTVE: {update_time}", font=f_u, fill=colors["dim"])

    # Mentés tűéles JPEG-ként
    img.convert("RGB").save("images/current.jpg", "JPEG", quality=100, subsampling=0)
    
    # JSON frissítése a webes részhez
    v_param = int(time.time())
    image_url = f"{BASE_URL}/current.jpg?v={v_param}"
    with open("weather.json", "w", encoding="utf-8") as f:
        json.dump([{"location": CITY, "title": f"{weather_hu} {temp}C", "image_url": image_url}], f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
