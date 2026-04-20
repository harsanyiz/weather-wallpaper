import requests
import json
import os
import time
from datetime import datetime, timezone, timedelta
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageStat

# Konfiguráció
API_KEY = os.environ.get("OWM_API_KEY")
GITHUB_USER = "harsanyiz"
GITHUB_REPO = "weather-wallpaper"
BRANCH = "main"
BASE_URL = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/{BRANCH}/images"

# ============================================================
# 4K-RA OPTIMALIZÁLT DESIGN KONFIGURÁCIÓ (3840x2160-as képhez)
# ============================================================
CITY = "Budapest"
WIDGET_WIDTH = 2200   # Arányos szélesség 4K-n
WIDGET_HEIGHT = 200   # Dupla magasság a korábbihoz képest
WIDGET_Y = 100        # Pozíció fentről
OFFSET_LEFT = 100     # Pozíció balról
CORNER_RADIUS = 100   # Kerekítés mértéke
INNER_MARGIN = 80     # Belső margó a kártyán belül

# 4K-s betűméretek
FONT_TEMP = 84        # Fő hőmérséklet
FONT_LABEL = 28       # Címkék (pl. ÉRZET, SZÉL)
FONT_VALUE = 36       # Értékek (pl. 10 km/h)
FONT_UPDATE = 24      # Frissítve felirat
FONT_TODAY = 22       # Nap neve a hőfok felett
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

def get_image_name(weather_id, is_night):
    suffix = "night" if is_night else "day"
    # Kibővített logika az összes fájltípushoz
    if 200 <= weather_id <= 531: return f"rainy_{suffix}"
    elif 600 <= weather_id <= 602 or 620 <= weather_id <= 622: return f"snow_{suffix}"
    elif weather_id in [511, 611, 612, 613, 615, 616]: return f"sleet_{suffix}"
    elif 701 <= weather_id <= 781: return f"foggy_{suffix}"
    elif weather_id == 800: return f"sunny_{suffix}"
    else: return f"cloudy_{suffix}"

def get_weather_hu(weather_id):
    mapping = {800: "Derült", 801: "Pár felhő", 804: "Borult", 511: "Ónos eső"}
    return mapping.get(weather_id, "Változékony")

def get_day_hu(date_obj, full=False):
    napok = ["Hétfő", "Kedd", "Szerda", "Csütörtök", "Péntek", "Szombat", "Vasárnap"]
    if full: return napok[date_obj.weekday()].upper()
    return napok[date_obj.weekday()][:3]

def get_glass_color(brightness):
    return (255, 255, 255, 160) if brightness > 145 else (0, 0, 0, 140)

def get_text_colors(brightness):
    if brightness > 145:
        return {"main": (0,0,0,230), "dim": (0,0,0,140), "line": (0,0,0,40)}
    return {"main": (255,255,255,255), "dim": (255,255,255,160), "line": (255,255,255,40)}

def create_blurred_card(image, box_x, box_y, box_width, box_height, glass_color, radius):
    box_area = image.crop((box_x, box_y, box_x + box_width, box_y + box_height))
    blurred = box_area.filter(ImageFilter.GaussianBlur(40)) # Erősebb blur 4K-ra
    mask = Image.new("L", (box_width, box_height), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, box_width, box_height), radius=radius, fill=255)
    glass = Image.new("RGBA", (box_width, box_height), glass_color)
    blurred = blurred.convert("RGBA")
    blurred.putalpha(mask)
    return Image.alpha_composite(blurred, glass)

def main():
    try:
        # Adatok lekérése
        resp = requests.get(f"https://api.openweathermap.org/data/2.5/weather?q={CITY}&appid={API_KEY}&units=metric")
        data = resp.json()
        f_resp = requests.get(f"https://api.openweathermap.org/data/2.5/forecast?q={CITY}&appid={API_KEY}&units=metric")
        f_data = f_resp.json()

        temp = round(data["main"]["temp"])
        weather_id = data["weather"][0]["id"]
        tz_offset = data.get("timezone", 3600)
        now_dt = datetime.now(timezone(timedelta(seconds=tz_offset)))
        update_time = now_dt.strftime("%H:%M")
        is_night = now_dt.timestamp() < data["sys"]["sunrise"] or now_dt.timestamp() > data["sys"]["sunset"]
        
        image_name = get_image_name(weather_id, is_night)
        weather_hu = get_weather_hu(weather_id)
        today_full = get_day_hu(now_dt, full=True)
        rain_chance = f"{round(f_data['list'][0].get('pop', 0) * 100)}%"

        forecast_list = []
        seen_days = set()
        today_date = now_dt.date()
        for entry in f_data['list']:
            d = datetime.fromtimestamp(entry['dt'], tz=timezone(timedelta(seconds=tz_offset))).date()
            if d > today_date and d not in seen_days:
                forecast_list.append(entry)
                seen_days.add(d)
            if len(forecast_list) == 3: break

    except Exception as e:
        print(f"Hiba az adatoknál: {e}"); return

    # Kép betöltése és 4K-ra méretezése
    src, dst = f"images/{image_name}.jpg", "images/current.jpg"
    img = Image.open(src).convert("RGB")
    if img.size != (3840, 2160):
        img = img.resize((3840, 2160), Image.Resampling.LANCZOS)

    # Szín és fényerő elemzés
    bx, by, bw, bh = OFFSET_LEFT, WIDGET_Y, WIDGET_WIDTH, WIDGET_HEIGHT
    region = img.crop((bx, by, bx + bw, by + bh)).convert("L")
    avg_brightness = ImageStat.Stat(region).mean[0]
    colors = get_text_colors(avg_brightness)
    glass_c = get_glass_color(avg_brightness)

    # Kártya létrehozása
    card = create_blurred_card(img, bx, by, bw, bh, glass_c, CORNER_RADIUS)
    img = img.convert("RGBA")
    img.paste(card, (bx, by), card)
    draw = ImageDraw.Draw(img)

    # Betűtípusok betöltése
    f_t, f_l, f_v, f_u, f_day = get_f(FONT_TEMP, True), get_f(FONT_LABEL), get_f(FONT_VALUE, True), get_f(FONT_UPDATE), get_f(FONT_TODAY)

    curr_x = bx + INNER_MARGIN
    mid_y = by + (bh // 2)

    # 1. NAP + HŐFOK (Centrálva)
    temp_txt = f"{temp}°C"
    temp_w = draw.textbbox((0,0), temp_txt, font=f_t)[2]
    day_w = draw.textbbox((0,0), today_full, font=f_day)[2]
    draw.text((curr_x + (temp_w - day_w)//2, mid_y - 68), today_full, font=f_day, fill=colors["dim"])
    draw.text((curr_x, mid_y - 42), temp_txt, font=f_t, fill=colors["main"])
    curr_x += temp_w + 80

    # Elválasztó vonal
    draw.line([(curr_x, by+50), (curr_x, by+bh-50)], fill=colors["line"], width=4)
    curr_x += 80

    # 2. ELŐREJELZÉS (3 nap)
    for day in forecast_list:
        day_name = get_day_hu(datetime.fromtimestamp(day['dt'])).upper()
        draw.text((curr_x, mid_y - 40), day_name, font=f_l, fill=colors["dim"])
        draw.text((curr_x, mid_y), f"{round(day['main']['temp'])}°C", font=f_v, fill=colors["main"])
        curr_x += 160 

    # Elválasztó vonal
    draw.line([(curr_x, by+50), (curr_x, by+bh-50)], fill=colors["line"], width=4)
    curr_x += 80

    # 3. RÉSZLETEK
    details = [("Érzet", f"{round(data['main']['feels_like'])}°C"), 
               ("Szél", f"{round(data['wind']['speed']*3.6)} km/h"), 
               ("Eső %", rain_chance)]
    for label, val in details:
        draw.text((curr_x, mid_y - 40), label.upper(), font=f_l, fill=colors["dim"])
        draw.text((curr_x, mid_y), val, font=f_v, fill=colors["main"])
        curr_x += 200

    # 4. FRISSÍTÉS IDŐPONTJA
    draw.text((curr_x, mid_y - 15), f"FRISSÍTVE: {update_time}", font=f_u, fill=colors["dim"])

    # Mentés
    img.convert("RGB").save(dst, "JPEG", quality=95)
    
    # JSON frissítés a cache elkerülése érdekében
    v_param = int(time.time())
    image_url = f"{BASE_URL}/current.jpg?v={v_param}"
    weather_json = [{"location": CITY, "title": f"{weather_hu} {temp}C", "author": "Gemini Design", "image_url": image_url, "url_img": image_url}]
    with open("weather.json", "w", encoding="utf-8") as f:
        json.dump(weather_json, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
