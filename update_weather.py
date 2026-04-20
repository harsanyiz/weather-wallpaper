import requests
import json
import os
import time
from datetime import datetime, timezone, timedelta
from PIL import Image, ImageDraw, ImageFont

# API és GitHub adatok
API_KEY = os.environ.get("OWM_API_KEY")
GITHUB_USER = "harsanyiz"
GITHUB_REPO = "weather-wallpaper"
BRANCH = "main"
BASE_URL = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/{BRANCH}/images"

# ============================================================
# 4K KONFIGURÁCIÓ - JAVÍTOTT, KISEBB FŐ IKON
# ============================================================
CITY = "Budapest"
WIDGET_Y = 100        
OFFSET_LEFT = 135     
INNER_MARGIN = 60     

FONT_TEMP = 95        
FONT_DESC = 32        
FONT_LABEL = 28       
FONT_VALUE = 36       
FONT_UPDATE = 22      
# ============================================================

def get_f(size, bold=False):
    paths = [
        "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    ]
    for p in paths:
        if os.path.exists(p): return ImageFont.truetype(p, size)
    return ImageFont.load_default()

def get_bg_name(weather_id, is_night):
    suffix = "night" if is_night else "day"
    if weather_id in [611, 612, 613, 615, 616]: return f"sleet_{suffix}"
    elif weather_id in [620, 621, 622, 600, 601, 602]: return f"snow_{suffix}"
    elif weather_id == 800: return f"sunny_{suffix}"
    else: return f"cloudy_{suffix}"

def get_icon_name(weather_id, is_night):
    suffix = "night" if is_night else "day"
    if weather_id == 800: return f"{suffix}_clear"
    elif weather_id in [801, 802]: return f"{suffix}_partial_cloud"
    elif weather_id in [803, 804]: return "overcast"
    elif 500 <= weather_id <= 531: return f"{suffix}_rain"
    elif 600 <= weather_id <= 622: return f"{suffix}_snow"
    elif 701 <= weather_id <= 741: return "fog"
    elif 200 <= weather_id <= 232: return f"{suffix}_rain_thunder"
    return "cloudy"

def main():
    try:
        curr_r = requests.get(f"https://api.openweathermap.org/data/2.5/weather?q={CITY}&appid={API_KEY}&units=metric").json()
        fore_r = requests.get(f"https://api.openweathermap.org/data/2.5/forecast?q={CITY}&appid={API_KEY}&units=metric").json()

        temp = round(curr_r["main"]["temp"])
        weather_id = curr_r["weather"][0]["id"]
        tz = timezone(timedelta(seconds=curr_r.get("timezone", 3600)))
        now_dt = datetime.now(tz)
        update_time = now_dt.strftime("%H:%M")
        is_night = now_dt.timestamp() < curr_r["sys"]["sunrise"] or now_dt.timestamp() > curr_r["sys"]["sunset"]
        
        bg_file = get_bg_name(weather_id, is_night)
        icon_file = get_icon_name(weather_id, is_night)
        weather_hu = {800: "Derült", 801: "Pár felhő", 802: "Részben felhős", 803: "Felhős", 804: "Borult"}.get(weather_id, "Változékony")
    except Exception as e:
        print(f"Hiba: {e}"); return

    # Háttérkép betöltése
    src = f"images/{bg_file}.jpg"
    img = Image.open(src if os.path.exists(src) else "images/sunny_day.jpg").convert("RGB")
    img = img.resize((3840, 2160), Image.Resampling.LANCZOS).convert("RGBA")
    draw = ImageDraw.Draw(img)

    colors = {"main": (255,255,255,255), "dim": (255,255,255,180), "line": (255,255,255,60)}
    f_t, f_d, f_l, f_v, f_u = get_f(FONT_TEMP, True), get_f(FONT_DESC), get_f(FONT_LABEL), get_f(FONT_VALUE, True), get_f(FONT_UPDATE)
    
    mid_y = WIDGET_Y + 100
    curr_x = OFFSET_LEFT + INNER_MARGIN

    # --- 1. SZEKCIÓ: FŐ IKON (JAVÍTOTT MÉRET) + HŐFOK + ÁLLAPOT AZ IKON ALATT ---
    icon_path = f"images/PNG/{icon_file}.png"
    if os.path.exists(icon_path):
        icon_img = Image.open(icon_path).convert("RGBA")
        # JAVÍTÁS: A fő ikont kisebbre és vékonyabbra vesszük (120x120), hogy harmóniában legyen a szöveggel
        icon_img = icon_img.resize((120, 120), Image.Resampling.LANCZOS)
        img.paste(icon_img, (int(curr_x), int(mid_y - 80)), icon_img)
        
        # Állapot felirat (DERÜLT) pontosan az ikon alá (pozíció finomhangolva)
        w_text = weather_hu.upper()
        w_bbox = draw.textbbox((0, 0), w_text, font=f_d)
        w_offset = (120 - (w_bbox[2] - w_bbox[0])) // 2
        draw.text((int(curr_x + w_offset), int(mid_y + 50)), w_text, font=f_d, fill=colors["dim"])
        
        curr_x += 160 # Kevesebb helyet foglal, így a szöveg közelebb kerül

    day_name = ["Hétfő", "Kedd", "Szerda", "Csütörtök", "Péntek", "Szombat", "Vasárnap"][now_dt.weekday()].upper()
    draw.text((int(curr_x), int(mid_y - 90)), day_name, font=f_l, fill=colors["dim"])
    draw.text((int(curr_x), int(mid_y - 65)), f"{temp}°C", font=f_t, fill=colors["main"])
    
    curr_x += draw.textbbox((0,0), f"{temp}°C", font=f_t)[2] + 80
    draw.line([(curr_x, WIDGET_Y+40), (curr_x, WIDGET_Y+160)], fill=colors["line"], width=3)
    curr_x += 80

    # --- 2. SZEKCIÓ: RÉSZLETEK ---
    details = [("Érzet", f"{round(curr_r['main']['feels_like'])}°C"),
               ("Szél", f"{round(curr_r['wind']['speed']*3.6)} km/h"),
               ("Pára", f"{curr_r['main']['humidity']}%")]
    for label, val in details:
        draw.text((int(curr_x), int(mid_y - 50)), label.upper(), font=f_l, fill=colors["dim"])
        draw.text((int(curr_x), int(mid_y)), val, font=f_v, fill=colors["main"])
        curr_x += max(draw.textbbox((0,0), label.upper(), font=f_l)[2], draw.textbbox((0,0), val, font=f_v)[2]) + 90

    # --- 3. SZEKCIÓ: 3 NAPOS ELŐREJELZÉS ---
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
        draw.text((int(curr_x), int(mid_y - 80)), d_name, font=f_l, fill=colors["dim"])
        draw.text((int(curr_x), int(mid_y - 45)), f"{round(day['main']['temp'])}°C", font=f_v, fill=colors["main"])
        
        # Kis ikon az előrejelzés alá
        f_icon_name = get_icon_name(day['weather'][0]['id'], False)
        f_icon_path = f"images/PNG/{f_icon_name}.png"
        if os.path.exists(f_icon_path):
            f_icon = Image.open(f_icon_path).convert("RGBA").resize((50, 50), Image.Resampling.LANCZOS)
            img.paste(f_icon, (int(curr_x), int(mid_y + 10)), f_icon)
        
        curr_x += 160

    draw.text((int(curr_x + 20), int(mid_y - 15)), f"FRISSÍTVE: {update_time}", font=f_u, fill=colors["dim"])

    img.convert("RGB").save("images/current.jpg", "JPEG", quality=100, subsampling=0)
    
    v_param = int(time.time())
    image_url = f"{BASE_URL}/current.jpg?v={v_param}"
    with open("weather.json", "w", encoding="utf-8") as f:
        json.dump([{"location": CITY, "title": f"{weather_hu} {temp}C", "image_url": image_url}], f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
