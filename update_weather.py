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
# ÚJ HORIZONTÁLIS DESIGN KONFIGURÁCIÓ
# ============================================================
CITY = "Budapest"
WIDGET_WIDTH = 1200   # Szélesebb sáv
WIDGET_HEIGHT = 100   # Vékonyabb magasság
WIDGET_X = 360        # Középre tájolva (1920-as szélességnél)
WIDGET_Y = 50         # Fent a margótól
CORNER_RADIUS = 50    # Teljesen lekerekített "pill" forma
INNER_MARGIN = 40

# Betűméretek a sávhoz igazítva
FONT_TEMP = 42
FONT_LABEL = 14
FONT_VALUE = 18
FONT_FOOTER = 12

VISIBLE_FIELDS = ["feels", "weather", "clouds", "rain_chance", "humidity", "wind"]
GLASS_STYLE = "auto"
# ============================================================

FONT_PATHS_REGULAR = ["/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf", "/usr/share/fonts/noto/NotoSans-Regular.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]
FONT_PATHS_BOLD = ["/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf", "/usr/share/fonts/noto/NotoSans-Bold.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]
FONT_PATHS_EMOJI = ["/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf", "/usr/share/fonts/noto/NotoColorEmoji.ttf"]

def find_font(bold=False):
    paths = FONT_PATHS_BOLD if bold else FONT_PATHS_REGULAR
    for p in paths:
        if os.path.exists(p): return p
    return None

def find_emoji_font():
    for p in FONT_PATHS_EMOJI:
        if os.path.exists(p): return p
    return None

def get_f(size, bold=False):
    path = find_font(bold)
    if path: return ImageFont.truetype(path, size)
    return ImageFont.load_default()

def get_emoji_f(size):
    path = find_emoji_font()
    if path:
        try: return ImageFont.truetype(path, size)
        except: pass
    return None

def get_image_name(weather_id, is_night):
    suffix = "night" if is_night else "day"
    if weather_id in [611, 612, 613, 615, 616]: return f"sleet_{suffix}"
    elif weather_id in [620, 621, 622, 600, 601, 602]: return f"snow_{suffix}"
    elif weather_id == 800: return f"sunny_{suffix}"
    else: return f"cloudy_{suffix}"

def get_weather_hu(weather_id):
    mapping = {800: "Derült", 801: "Pár felhő", 804: "Borult", 511: "Ónos eső"}
    if weather_id in mapping: return mapping[weather_id]
    return "Változékony"

def get_weather_icon(weather_id, is_night):
    if weather_id == 800: return "☀️" if not is_night else "🌙"
    return "☁️"

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
        temp, weather_id = round(data["main"]["temp"]), data["weather"][0]["id"]
        tz_offset = data.get("timezone", 3600)
        now_dt = datetime.now(timezone(timedelta(seconds=tz_offset)))
        is_night = now_dt.timestamp() < data["sys"]["sunrise"] or now_dt.timestamp() > data["sys"]["sunset"]
        image_name = get_image_name(weather_id, is_night)
        weather_hu = get_weather_hu(weather_id)
    except Exception as e:
        print(f"Hiba: {e}"); return

    src, dst = f"images/{image_name}.jpg", "images/current.jpg"
    img = Image.open(src).convert("RGB")
    W, H = img.size

    # Régió számítása
    bx, by, bw, bh = (W - WIDGET_WIDTH) // 2, WIDGET_Y, WIDGET_WIDTH, WIDGET_HEIGHT
    region = img.crop((bx, by, bx + bw, by + bh)).convert("L")
    avg_brightness = ImageStat.Stat(region).mean[0]
    
    colors = get_text_colors(avg_brightness)
    glass_c = get_glass_color(avg_brightness)

    card = create_blurred_card(img, bx, by, bw, bh, glass_c, CORNER_RADIUS)
    img = img.convert("RGBA")
    img.paste(card, (bx, by), card)
    draw = ImageDraw.Draw(img)

    f_t, f_l, f_v = get_f(FONT_TEMP, True), get_f(FONT_LABEL), get_f(FONT_VALUE, True)

    # Rajzolás vízszintesen
    curr_x = bx + INNER_MARGIN
    mid_y = by + (bh // 2)

    # 1. Hőmérséklet
    temp_txt = f"{temp}°C"
    draw.text((curr_x, mid_y - 25), temp_txt, font=f_t, fill=colors["main"])
    curr_x += draw.textbbox((0,0), temp_txt, font=f_t)[2] + 40

    # Választóvonal
    draw.line([(curr_x, by+25), (curr_x, by+bh-25)], fill=colors["line"], width=2)
    curr_x += 40

    # 2. Egyéb adatok sora
    fields_to_show = [
        ("Érzet", f"{round(data['main']['feels_like'])}°C"),
        ("Szél", f"{round(data['wind']['speed']*3.6)} km/h"),
        ("Pára", f"{data['main']['humidity']}%")
    ]

    for label, val in fields_to_show:
        draw.text((curr_x, mid_y - 20), label.upper(), font=f_l, fill=colors["dim"])
        draw.text((curr_x, mid_y), val, font=f_v, fill=colors["main"])
        l_w = draw.textbbox((0,0), label.upper(), font=f_l)[2]
        v_w = draw.textbbox((0,0), val, font=f_v)[2]
        curr_x += max(l_w, v_w) + 50

    # Mentés
    img.convert("RGB").save(dst, "JPEG", quality=95)
    
    # JSON frissítés a cache-trükkel ÉS lista formátummal
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
    print(f"Minden kész! weather.json és current.jpg frissítve.")

if __name__ == "__main__":
    main()
