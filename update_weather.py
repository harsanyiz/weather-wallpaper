import requests
import json
import os
import time
from datetime import datetime, timezone, timedelta
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageStat

API_KEY = os.environ.get("OWM_API_KEY")
GITHUB_USER = "harsanyiz"
GITHUB_REPO = "weather-wallpaper"
BRANCH = "main"
BASE_URL = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/{BRANCH}/images"

# ============================================================
# 4K-S HORIZONTÁLIS DESIGN KONFIGURÁCIÓ
# ============================================================
CITY = "Budapest"
WIDGET_WIDTH = 2200   
WIDGET_HEIGHT = 200   
WIDGET_Y = 100        
OFFSET_LEFT = 135     # A Media ikon feletti fehér jelölőhöz igazítva
CORNER_RADIUS = 100   
INNER_MARGIN = 80     

# 4K-s betűméretek
FONT_TEMP = 90        # Fő hőmérséklet
FONT_DESC = 32        # Időjárás megnevezése (pl. DERÜLT)
FONT_LABEL = 28       # Címkék és a Nap neve (pl. ÉRZET, HÉTFŐ)
FONT_VALUE = 36       # Értékek (pl. 10 km/h)
FONT_UPDATE = 24      # Frissítve felirat
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
    if weather_id in [611, 612, 613, 615, 616]: return f"sleet_{suffix}"
    elif weather_id in [620, 621, 622, 600, 601, 602]: return f"snow_{suffix}"
    elif weather_id == 800: return f"sunny_{suffix}"
    else: return f"cloudy_{suffix}"

def get_weather_hu(weather_id):
    mapping = {800: "Derült", 801: "Pár felhő", 802: "Részben felhős", 803: "Felhős", 804: "Borult", 511: "Ónos eső"}
    return mapping.get(weather_id, "Változékony")

def get_day_hu(date_obj):
    napok = ["Hétfő", "Kedd", "Szerda", "Csütörtök", "Péntek", "Szombat", "Vasárnap"]
    return napok[date_obj.weekday()]

def get_glass_color(brightness):
    return (255, 255, 255, 160) if brightness > 145 else (0, 0, 0, 140)

def get_text_colors(brightness):
    if brightness > 145:
        return {"main": (0,0,0,230), "dim": (0,0,0,140), "line": (0,0,0,40)}
    return {"main": (255,255,255,255), "dim": (255,255,255,160), "line": (255,255,255,40)}

def create_blurred_card(image, box_x, box_y, box_width, box_height, glass_color, radius):
    box_area = image.crop((box_x, box_y, box_x + box_width, box_y + box_height))
    blurred = box_area.filter(ImageFilter.GaussianBlur(40))
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

        temp, weather_id = round(data["main"]["temp"]), data["weather"][0]["id"]
        tz_offset = data.get("timezone", 3600)
        now_dt = datetime.now(timezone(timedelta(seconds=tz_offset)))
        update_time = now_dt.strftime("%H:%M")
        is_night = now_dt.timestamp() < data["sys"]["sunrise"] or now_dt.timestamp() > data["sys"]["sunset"]
        image_name = get_image_name(weather_id, is_night)
        weather_hu = get_weather_hu(weather_id)

        # 3 napos előrejelzés szűrése
        forecast_list = []
        seen_days = set()
        today = now_dt.date()
        for entry in f_data['list']:
            dt_obj = datetime.fromtimestamp(entry['dt'], tz=timezone(timedelta(seconds=tz_offset)))
            day_date = dt_obj.date()
            if day_date > today and day_date not in seen_days and dt_obj.hour >= 12:
                forecast_list.append(entry)
                seen_days.add(day_date)
            if len(forecast_list) == 3: break
    except Exception as e:
        print(f"Hiba: {e}"); return

    # Kép előkészítése
    src, dst = f"images/{image_name}.jpg", "images/current.jpg"
    img = Image.open(src).convert("RGB")
    if img.size != (3840, 2160):
        img = img.resize((3840, 2160), Image.Resampling.LANCZOS)
    
    W, H = img.size
    bx, by, bw, bh = OFFSET_LEFT, WIDGET_Y, WIDGET_WIDTH, WIDGET_HEIGHT
    
    region = img.crop((bx, by, bx + bw, by + bh)).convert("L")
    avg_brightness = ImageStat.Stat(region).mean[0]
    colors = get_text_colors(avg_brightness)
    glass_c = get_glass_color(avg_brightness)

    card = create_blurred_card(img, bx, by, bw, bh, glass_c, CORNER_RADIUS)
    img = img.convert("RGBA")
    img.paste(card, (bx, by), card)
    draw = ImageDraw.Draw(img)

    # Betűtípusok betöltése
    f_t = get_f(FONT_TEMP, True)
    f_d = get_f(FONT_DESC)
    f_l = get_f(FONT_LABEL)
    f_v = get_f(FONT_VALUE, True)
    f_u = get_f(FONT_UPDATE)

    curr_x = int(bx + INNER_MARGIN)
    mid_y = int(by + (bh // 2))

    # --- 1. SZEKCIÓ: NAP + HŐFOK + LEÍRÁS (KÖZÉPRE IGAZÍTVA) ---
    day_txt = get_day_hu(now_dt).upper()
    temp_txt = f"{temp}°C"
    desc_txt = weather_hu.upper()

    day_w = draw.textbbox((0, 0), day_txt, font=f_l)[2]
    temp_w = draw.textbbox((0, 0), temp_txt, font=f_t)[2]
    desc_w = draw.textbbox((0, 0), desc_txt, font=f_d)[2]
    max_w = max(day_w, temp_w, desc_w)

    draw.text((int(curr_x + (max_w - day_w) / 2), int(mid_y - 85)), day_txt, font=f_l, fill=colors["dim"])
    draw.text((int(curr_x + (max_w - temp_w) / 2), int(mid_y - 60)), temp_txt, font=f_t, fill=colors["main"])
    draw.text((int(curr_x + (max_w - desc_w) / 2), int(mid_y + 35)), desc_txt, font=f_d, fill=colors["dim"])
    
    curr_x += int(max_w + 70)
    draw.line([(curr_x, by+40), (curr_x, by+bh-40)], fill=colors["line"], width=3)
    curr_x += 60

    # --- 2. SZEKCIÓ: RÉSZLETEK (ÉRZET, SZÉL, PÁRA) ---
    fields = [
        ("Érzet", f"{round(data['main']['feels_like'])}°C"),
        ("Szél", f"{round(data['wind']['speed']*3.6)} km/h"),
        ("Pára", f"{data['main']['humidity']}%")
    ]
    for label, val in fields:
        l_txt = label.upper()
        draw.text((curr_x, mid_y - 45), l_txt, font=f_l, fill=colors["dim"])
        draw.text((curr_x, mid_y), val, font=f_v, fill=colors["main"])
        curr_x += max(draw.textbbox((0,0), l_txt, font=f_l)[2], draw.textbbox((0,0), val, font=f_v)[2]) + 80

    # --- 3. SZEKCIÓ: 3 NAPOS ELŐREJELZÉS ---
    draw.line([(curr_x, by+40), (curr_x, by+bh-40)], fill=colors["line"], width=3)
    curr_x += 60
    for day in forecast_list:
        d_name = get_day_hu(datetime.fromtimestamp(day['dt'])).upper()[:3] # Rövidített napnév
        f_val = f"{round(day['main']['temp'])}°C"
        draw.text((curr_x, mid_y - 45), d_name, font=f_l, fill=colors["dim"])
        draw.text((curr_x, mid_y), f_val, font=f_v, fill=colors["main"])
        curr_x += 140 

    # --- 4. SZEKCIÓ: FRISSÍTÉS ---
    update_txt = f"FRISSÍTVE: {update_time}"
    draw.text((curr_x + 20, mid_y - 12), update_txt, font=f_u, fill=colors["dim"])

    # Mentés 100%-os minőségben
    img.convert("RGB").save(dst, "JPEG", quality=100, subsampling=0)
    
    # JSON frissítése a webes felülethez
    v_param = int(time.time())
    image_url = f"{BASE_URL}/current.jpg?v={v_param}"
    weather_json = [{"location": CITY, "title": f"{weather_hu} {temp}C", "author": "Gemini Design", "image_url": image_url, "url_img": image_url}]
    with open("weather.json", "w", encoding="utf-8") as f:
        json.dump(weather_json, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
