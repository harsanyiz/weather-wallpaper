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
# HORIZONTÁLIS DESIGN KONFIGURÁCIÓ
# ============================================================
CITY = "Budapest"
WIDGET_WIDTH = 1100   
WIDGET_HEIGHT = 100
WIDGET_Y = 50
OFFSET_LEFT = 50      
CORNER_RADIUS = 50
INNER_MARGIN = 40

FONT_TEMP = 42
FONT_LABEL = 14
FONT_VALUE = 18
FONT_UPDATE = 12
FONT_TODAY = 11      # A mai nap nevének mérete
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
    mapping = {800: "Derült", 801: "Pár felhő", 804: "Borult", 511: "Ónos eső"}
    return mapping.get(weather_id, "Változékony")

def get_day_hu(date_obj, full=False):
    if full:
        napok = ["HÉTFŐ", "KEDD", "SZERDA", "CSÜTÖRTÖK", "PÉNTEK", "SZOMBAT", "VASÁRNAP"]
    else:
        napok = ["Hét", "Ked", "Sze", "Csü", "Pén", "Szo", "Vas"]
    return napok[date_obj.weekday()]

def get_glass_color(brightness):
    return (255, 255, 255, 160) if brightness > 145 else (0, 0, 0, 140)

def get_text_colors(brightness):
    if brightness > 145:
        return {"main": (0,0,0,230), "dim": (0,0,0,140), "line": (0,0,0,40)}
    return {"main": (255,255,255,255), "dim": (255,255,255,160), "line": (255,255,255,40)}

def create_blurred_card(image, box_x, box_y, box_width, box_height, glass_color, radius):
    box_area = image.crop((box_x, box_y, box_x + box_width, box_y + box_height))
    blurred = box_area.filter(ImageFilter.GaussianBlur(20))
    mask = Image.new("L", (box_width, box_height), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, box_width, box_height), radius=radius, fill=255)
    glass = Image.new("RGBA", (box_width, box_height), glass_color)
    blurred = blurred.convert("RGBA")
    blurred.putalpha(mask)
    return Image.alpha_composite(blurred, glass)

def main():
    try:
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
        
        # Mai nap teljes neve
        today_name = get_day_hu(now_dt, full=True)

        rain_chance = f"{round(f_data['list'][0].get('pop', 0) * 100)}%"

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

    src, dst = f"images/{image_name}.jpg", "images/current.jpg"
    img = Image.open(src).convert("RGB")
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

    f_t = get_f(FONT_TEMP, True)
    f_l = get_f(FONT_LABEL)
    f_v = get_f(FONT_VALUE, True)
    f_u = get_f(FONT_UPDATE)
    f_day = get_f(FONT_TODAY)

    curr_x = bx + INNER_MARGIN
    mid_y = by + (bh // 2)

    # 1. Mai nap neve + Aktuális Hőmérséklet
    draw.text((curr_x, mid_y - 38), today_name, font=f_day, fill=colors["dim"]) # Nap neve fent
    temp_txt = f"{temp}°C"
    draw.text((curr_x, mid_y - 25), temp_txt, font=f_t, fill=colors["main"])
    curr_x += draw.textbbox((0,0), temp_txt, font=f_t)[2] + 40

    # Első elválasztó vonal
    draw.line([(curr_x, by+25), (curr_x, by+bh-25)], fill=colors["line"], width=2)
    curr_x += 40

    # 2. ELŐREJELZÉS
    for day in forecast_list:
        dt_obj = datetime.fromtimestamp(day['dt'])
        day_name = get_day_hu(dt_obj)
        f_temp = f"{round(day['main']['temp'])}°C"
        
        draw.text((curr_x, mid_y - 20), day_name.upper(), font=f_l, fill=colors["dim"])
        draw.text((curr_x, mid_y), f_temp, font=f_v, fill=colors["main"])
        curr_x += 80 

    # Második elválasztó vonal
    draw.line([(curr_x, by+25), (curr_x, by+bh-25)], fill=colors["line"], width=2)
    curr_x += 40

    # 3. RÉSZLETEK
    fields = [
        ("Érzet", f"{round(data['main']['feels_like'])}°C"),
        ("Szél", f"{round(data['wind']['speed']*3.6)} km/h"),
        ("Eső %", rain_chance)
    ]

    for label, val in fields:
        draw.text((curr_x, mid_y - 20), label.upper(), font=f_l, fill=colors["dim"])
        draw.text((curr_x, mid_y), val, font=f_v, fill=colors["main"])
        curr_x += max(draw.textbbox((0,0), label.upper(), font=f_l)[2], draw.textbbox((0,0), val, font=f_v)[2]) + 50

    # 4. Frissítési idő
    update_txt = f"FRISSÍTVE: {update_time}"
    draw.text((curr_x + 10, mid_y - 8), update_txt, font=f_u, fill=colors["dim"])

    img.convert("RGB").save(dst, "JPEG", quality=95)
    
    v_param = int(time.time())
    image_url = f"{BASE_URL}/current.jpg?v={v_param}"
    
    weather_json = [{
        "location": CITY, 
        "title": f"{weather_hu} {temp}C",
        "author": "Gemini Design", 
        "image_url": image_url,
        "url_img": image_url
    }]
    
    with open("weather.json", "w", encoding="utf-8") as f:
        json.dump(weather_json, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
