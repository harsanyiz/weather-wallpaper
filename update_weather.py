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

# --- FULL HD MÉRETEZÉS (1920x1080) ---
CITY = "Budapest"
WIDGET_Y = 50         # 4K-hoz képest felezve
OFFSET_LEFT = 67      # 4K-hoz képest felezve
INNER_MARGIN = 40     

# Betűméretek felezve a 4K-hoz képest
FONT_TEMP = 48        
FONT_DESC = 18        
FONT_LABEL = 16       
FONT_VALUE = 20       
FONT_UPDATE = 12      

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

    # --- 1. FULL HD ALAP ---
    bg_path = f"images/{bg_name}.jpg"
    bg = Image.open(bg_path if os.path.exists(bg_path) else "images/sunny_day.jpg").convert("RGBA")
    # 1920x1080-ra méretezzük!
    bg = bg.resize((1920, 1080), Image.Resampling.LANCZOS)
    
    draw = ImageDraw.Draw(bg)
    colors = {"main": (255,255,255,255), "dim": (255,255,255,180), "line": (255,255,255,40)}
    f_t, f_d, f_l, f_v, f_u = get_f(FONT_TEMP, True), get_f(FONT_DESC), get_f(FONT_LABEL), get_f(FONT_VALUE, True), get_f(FONT_UPDATE)
    
    curr_x = OFFSET_LEFT + INNER_MARGIN
    mid_y = WIDGET_Y + 50

    # --- 2. IKONOK ---
    icon_p = f"images/PNG/{main_icon_name}"
    if os.path.exists(icon_p):
        m_icon = Image.open(icon_p).convert("RGBA").resize((60, 60), Image.Resampling.LANCZOS)
        bg.paste(m_icon, (int(curr_x), int(mid_y - 25)), m_icon)
        curr_x += 80

    day_txt = (["Hétfő", "Kedd", "Szerda", "Csütörtök", "Péntek", "Szombat", "Vasárnap"][now_dt.weekday()]).upper()
    draw.text((curr_x, mid_y - 45), day_txt, font=f_l, fill=colors["dim"])
    draw.text((curr_x, mid_y - 35), f"{temp}°C", font=f_t, fill=colors["main"])
    draw.text((curr_x, mid_y + 20), weather_hu.upper(), font=f_d, fill=colors["dim"])
    
    curr_x += draw.textbbox((0,0), f"{temp}°C", font=f_t)[2] + 40
    draw.line([(curr_x, WIDGET_Y+20), (curr_x, WIDGET_Y+80)], fill=colors["line"], width=2)
    curr_x += 40

    # Részletek ikonokkal (kicsiben)
    fields = [("Érzet", f"{round(resp['main']['feels_like'])}°C", "day_clear.png"),
              ("Szél", f"{round(resp['wind']['speed']*3.6)} km/h", "wind.png")]
    
    for label, val, i_name in fields:
        i_p = f"images/PNG/{i_name}"
        if os.path.exists(i_p):
            s_icon = Image.open(i_p).convert("RGBA").resize((20, 20), Image.Resampling.LANCZOS)
            bg.paste(s_icon, (int(curr_x - 25), int(mid_y - 2)), s_icon)
        draw.text((curr_x, mid_y - 25), label.upper(), font=f_l, fill=colors["dim"])
        draw.text((curr_x, mid_y), val, font=f_v, fill=colors["main"])
        curr_x += 80

    # --- 3. MENTÉS ---
    final_img = Image.new("RGB", bg.size, (0, 0, 0))
    final_img.paste(bg, mask=bg.split()[3])
    
    # Kisebb fájlméret, hogy a TV biztosan szeresse
    final_img.save("images/current.jpg", "JPEG", quality=85, optimize=True)
    
    v_param = int(time.time())
    weather_json = [{"location": CITY, "title": f"{weather_hu} {temp}C", "image_url": f"{BASE_URL}/current.jpg?v={v_param}"}]
    with open("weather.json", "w", encoding="utf-8") as f:
        json.dump(weather_json, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
