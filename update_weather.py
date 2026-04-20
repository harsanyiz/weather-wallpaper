import requests
import json
import os
import time
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

FONT_TEMP = 90        
FONT_DESC = 32        
FONT_LABEL = 28       
FONT_VALUE = 36       
FONT_UPDATE = 24      

def get_f(size, bold=False):
    path = "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf"
    if not os.path.exists(path):
        path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    if os.path.exists(path): return ImageFont.truetype(path, size)
    return ImageFont.load_default()

def get_image_name(weather_id, is_night):
    suffix = "night" if is_night else "day"
    if weather_id in [611, 612, 613, 615, 616]: return f"sleet_{suffix}"
    elif weather_id in [620, 621, 622, 600, 601, 602]: return f"snow_{suffix}"
    elif weather_id == 800: return f"sunny_{suffix}"
    else: return f"cloudy_{suffix}"

def get_icon_file(weather_id, is_night):
    suffix = "night" if is_night else "day"
    if weather_id == 800: return f"{suffix}_clear.png"
    elif weather_id in [801, 802]: return f"{suffix}_partial_cloud.png"
    elif weather_id in [803, 804]: return "overcast.png"
    elif 500 <= weather_id <= 531: return f"{suffix}_rain.png"
    elif 600 <= weather_id <= 622: return f"{suffix}_snow.png"
    return "cloudy.png"

def main():
    try:
        resp = requests.get(f"https://api.openweathermap.org/data/2.5/weather?q={CITY}&appid={API_KEY}&units=metric").json()
        f_resp = requests.get(f"https://api.openweathermap.org/data/2.5/forecast?q={CITY}&appid={API_KEY}&units=metric").json()

        temp, weather_id = round(resp["main"]["temp"]), resp["weather"][0]["id"]
        tz_offset = resp.get("timezone", 3600)
        now_dt = datetime.now(timezone(timedelta(seconds=tz_offset)))
        is_night = now_dt.timestamp() < resp["sys"]["sunrise"] or now_dt.timestamp() > resp["sys"]["sunset"]
        
        image_name = get_image_name(weather_id, is_night)
        icon_name = get_icon_file(weather_id, is_night)
        weather_hu = {800: "Derült", 801: "Pár felhő", 802: "Részben felhős", 803: "Felhős", 804: "Borult"}.get(weather_id, "Változékony")
    except: return

    # Háttér betöltése (a régi kódod stabil alapja)
    src = f"images/{image_name}.jpg"
    img = Image.open(src if os.path.exists(src) else "images/sunny_day.jpg").convert("RGB")
    img = img.resize((3840, 2160), Image.Resampling.LANCZOS).convert("RGBA")
    draw = ImageDraw.Draw(img)
    
    colors = {"main": (255,255,255,255), "dim": (255,255,255,160), "line": (255,255,255,40)}
    f_t, f_d, f_l, f_v, f_u = get_f(FONT_TEMP, True), get_f(FONT_DESC), get_f(FONT_LABEL), get_f(FONT_VALUE, True), get_f(FONT_UPDATE)
    
    curr_x = OFFSET_LEFT + INNER_MARGIN
    mid_y = WIDGET_Y + 100

    # --- 1. SZEKCIÓ: FŐ IKON (EXTRA KICSI) + ADATOK ---
    icon_path = f"images/PNG/{icon_name}"
    if os.path.exists(icon_path):
        icon_img = Image.open(icon_path).convert("RGBA").resize((90, 90), Image.Resampling.LANCZOS)
        img.paste(icon_img, (int(curr_x), int(mid_y - 45)), icon_img)
        curr_x += 120

    day_txt = (["Hétfő", "Kedd", "Szerda", "Csütörtök", "Péntek", "Szombat", "Vasárnap"][now_dt.weekday()]).upper()
    draw.text((curr_x, mid_y - 85), day_txt, font=f_l, fill=colors["dim"])
    draw.text((curr_x, mid_y - 60), f"{temp}°C", font=f_t, fill=colors["main"])
    draw.text((curr_x, mid_y + 35), weather_hu.upper(), font=f_d, fill=colors["dim"])
    
    curr_x += draw.textbbox((0,0), f"{temp}°C", font=f_t)[2] + 80
    draw.line([(curr_x, WIDGET_Y+40), (curr_x, WIDGET_Y+160)], fill=colors["line"], width=3)
    curr_x += 60

    # --- 2. SZEKCIÓ: RÉSZLETEK ---
    fields = [("Érzet", f"{round(resp['main']['feels_like'])}°C"),
              ("Szél", f"{round(resp['wind']['speed']*3.6)} km/h"),
              ("Pára", f"{resp['main']['humidity']}%")]
    for label, val in fields:
        draw.text((curr_x, mid_y - 45), label.upper(), font=f_l, fill=colors["dim"])
        draw.text((curr_x, mid_y), val, font=f_v, fill=colors["main"])
        curr_x += max(draw.textbbox((0,0), label.upper(), font=f_l)[2], draw.textbbox((0,0), val, font=f_v)[2]) + 80

    # --- 3. SZEKCIÓ: ELŐREJELZÉS IKONOKKAL ---
    draw.line([(curr_x, WIDGET_Y+40), (curr_x, WIDGET_Y+160)], fill=colors["line"], width=3)
    curr_x += 60
    
    seen = set()
    f_list = []
    for e in f_resp['list']:
        d = datetime.fromtimestamp(e['dt'], tz=timezone(timedelta(seconds=tz_offset)))
        if d.date() > now_dt.date() and d.date() not in seen and d.hour >= 12:
            f_list.append(e); seen.add(d.date())
        if len(f_list) == 3: break

    for day in f_list:
        dn = (["Hét", "Ked", "Sze", "Csü", "Pén", "Szo", "Vas"][datetime.fromtimestamp(day['dt']).weekday()]).upper()
        draw.text((curr_x, mid_y - 45), dn, font=f_l, fill=colors["dim"])
        draw.text((curr_x, mid_y), f"{round(day['main']['temp'])}°C", font=f_v, fill=colors["main"])
        
        # Kis ikon az előrejelzéshez
        f_icon_fn = get_icon_file(day['weather'][0]['id'], False)
        f_icon_p = f"images/PNG/{f_icon_fn}"
        if os.path.exists(f_icon_p):
            f_i = Image.open(f_icon_p).convert("RGBA").resize((40, 40), Image.Resampling.LANCZOS)
            img.paste(f_i, (int(curr_x + 80), int(mid_y - 40)), f_i)
        curr_x += 160

    # Mentés a régi kódod stabil módján
    img.convert("RGB").save("images/current.jpg", "JPEG", quality=95, optimize=True)
    
    # JSON frissítése
    v_param = int(time.time())
    weather_json = [{"location": CITY, "title": f"{weather_hu} {temp}C", "image_url": f"{BASE_URL}/current.jpg?v={v_param}"}]
    with open("weather.json", "w", encoding="utf-8") as f:
        json.dump(weather_json, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
