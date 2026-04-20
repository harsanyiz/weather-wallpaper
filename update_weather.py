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

FONT_TEMP = 95        
FONT_DESC = 32        
FONT_LABEL = 28       
FONT_VALUE = 36       
FONT_UPDATE = 22      

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
        update_time = now_dt.strftime("%H:%M")
        is_night = now_dt.timestamp() < resp["sys"]["sunrise"] or now_dt.timestamp() > resp["sys"]["sunset"]
        
        bg_name = get_image_name(weather_id, is_night)
        main_icon_name = get_icon_file(weather_id, is_night)
        weather_hu = {800: "Derült", 801: "Pár felhő", 802: "Részben felhős", 803: "Felhős", 804: "Borult"}.get(weather_id, "Változékony")
    except: return

    # --- 1. LÉPÉS: ALAP KÉP ELŐKÉSZÍTÉSE (RGBA-ban dolgozunk a rétegek miatt) ---
    bg_path = f"images/{bg_name}.jpg"
    bg = Image.open(bg_path if os.path.exists(bg_path) else "images/sunny_day.jpg").convert("RGBA")
    if bg.size != (3840, 2160):
        bg = bg.resize((3840, 2160), Image.Resampling.LANCZOS)
    
    draw = ImageDraw.Draw(bg)
    colors = {"main": (255,255,255,255), "dim": (255,255,255,180), "line": (255,255,255,40)}
    f_t, f_d, f_l, f_v, f_u = get_f(FONT_TEMP, True), get_f(FONT_DESC), get_f(FONT_LABEL), get_f(FONT_VALUE, True), get_f(FONT_UPDATE)
    
    curr_x = OFFSET_LEFT + INNER_MARGIN
    mid_y = WIDGET_Y + 100

    # --- 2. LÉPÉS: FŐ IKON BEILLESZTÉSE (MASZKKAL) ---
    icon_p = f"images/PNG/{main_icon_name}"
    if os.path.exists(icon_p):
        m_icon = Image.open(icon_p).convert("RGBA").resize((110, 110), Image.Resampling.LANCZOS)
        # Itt a trükk: harmadik paraméterként is átadjuk az ikont (ez a maszk)
        bg.paste(m_icon, (int(curr_x), int(mid_y - 45)), m_icon)
        curr_x += 140

    # Szövegek
    day_txt = (["Hétfő", "Kedd", "Szerda", "Csütörtök", "Péntek", "Szombat", "Vasárnap"][now_dt.weekday()]).upper()
    draw.text((curr_x, mid_y - 85), day_txt, font=f_l, fill=colors["dim"])
    draw.text((curr_x, mid_y - 65), f"{temp}°C", font=f_t, fill=colors["main"])
    draw.text((curr_x, mid_y + 40), weather_hu.upper(), font=f_d, fill=colors["dim"])
    
    curr_x += draw.textbbox((0,0), f"{temp}°C", font=f_t)[2] + 80
    draw.line([(curr_x, WIDGET_Y+40), (curr_x, WIDGET_Y+160)], fill=colors["line"], width=3)
    curr_x += 80

    # --- 3. LÉPÉS: RÉSZLETEK IKONOKKAL ---
    fields = [("Érzet", f"{round(resp['main']['feels_like'])}°C", "day_clear.png"),
              ("Szél", f"{round(resp['wind']['speed']*3.6)} km/h", "wind.png"),
              ("Pára", f"{resp['main']['humidity']}%", "rain.png")]
    
    for label, val, i_name in fields:
        i_p = f"images/PNG/{i_name}"
        if os.path.exists(i_p):
            s_icon = Image.open(i_p).convert("RGBA").resize((35, 35), Image.Resampling.LANCZOS)
            bg.paste(s_icon, (int(curr_x - 45), int(mid_y - 5)), s_icon)
        draw.text((curr_x, mid_y - 50), label.upper(), font=f_l, fill=colors["dim"])
        draw.text((curr_x, mid_y), val, font=f_v, fill=colors["main"])
        curr_x += max(draw.textbbox((0,0), label.upper(), font=f_l)[2], draw.textbbox((0,0), val, font=f_v)[2]) + 100

    # Frissítve felirat
    draw.text((curr_x + 20, mid_y - 12), f"FRISSÍTVE: {update_time}", font=f_u, fill=colors["dim"])

    # --- 4. LÉPÉS: A "TV-BIZTOS" MENTÉS ---
    # Létrehozunk egy üres RGB képet, és rátesszük a munkánkat (ez megöli az átlátszóságot)
    final_img = Image.new("RGB", bg.size, (0, 0, 0))
    final_img.paste(bg, mask=bg.split()[3]) # Az alpha csatorna alapján másolunk
    
    # Kényszerített tiszta mentés metaadatok nélkül
    final_img.save("images/current.jpg", "JPEG", quality=90, optimize=True, subsampling=0)
    
    # JSON frissítése
    v_param = int(time.time())
    weather_json = [{"location": CITY, "title": f"{weather_hu} {temp}C", "image_url": f"{BASE_URL}/current.jpg?v={v_param}"}]
    with open("weather.json", "w", encoding="utf-8") as f:
        json.dump(weather_json, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
