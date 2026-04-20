import requests
import json
import os
from datetime import datetime, timezone, timedelta
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageStat

# --- Konfiguráció ---
API_KEY = os.environ.get("OWM_API_KEY", "f1140d0ccb478ba741a957a67dd074ca")
CITY = "Budapest"
GITHUB_USER = "harsanyiz"
GITHUB_REPO = "weather-wallpaper"
BRANCH = "main"
BASE_URL = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/{BRANCH}/images"

def get_image_name(weather_id, is_night):
    suffix = "night" if is_night else "day"
    if weather_id in [611, 612, 613, 615, 616]: return f"sleet_{suffix}"
    elif weather_id in [620, 621, 622, 600, 601, 602]: return f"snow_{suffix}"
    elif weather_id in [511]: return f"hail_{suffix}"
    elif weather_id in [781, 771, 762, 761, 751, 731, 721, 711, 701]: return f"foggy_{suffix}"
    elif weather_id in range(200, 233): return f"hail_{suffix}"
    elif weather_id in range(500, 532): return f"rainy_{suffix}"
    elif weather_id in range(300, 322): return f"rainy_{suffix}"
    elif weather_id == 800: return f"sunny_{suffix}"
    else: return f"cloudy_{suffix}"

def get_weather_hu(weather_id):
    mapping = {800: "Derült", 801: "Enyhén felhős", 802: "Enyhén felhős", 803: "Felhős", 804: "Felhős", 511: "Jégeső"}
    if weather_id in mapping: return mapping[weather_id]
    if weather_id in range(600, 623): return "Havazás"
    if weather_id in range(200, 233): return "Zivatar"
    if weather_id in range(500, 532): return "Eső"
    if weather_id in range(300, 322): return "Szitálás"
    return "Változékony"

def get_rain_chance(weather_id):
    if weather_id in range(200, 233): return 80
    if weather_id in range(500, 532): return 70
    if weather_id == 800: return 0
    return 20

def create_blurred_card(image, box_x, box_y, box_width, box_height, glass_color, radius=30, blur_strength=18):
    box_area = image.crop((box_x, box_y, box_x + box_width, box_y + box_height))
    blurred = box_area.filter(ImageFilter.GaussianBlur(blur_strength))
    mask = Image.new("L", (box_width, box_height), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle((0, 0, box_width, box_height), radius=radius, fill=255)
    glass = Image.new("RGBA", (box_width, box_height), glass_color)
    blurred = blurred.convert("RGBA")
    blurred.putalpha(mask)
    result = Image.alpha_composite(blurred, glass)
    border_color = (255, 255, 255, 50) if glass_color[0] < 128 else (0, 0, 0, 30)
    border = Image.new("RGBA", (box_width, box_height), (0, 0, 0, 0))
    ImageDraw.Draw(border).rounded_rectangle((0, 0, box_width, box_height), radius=radius, outline=border_color, width=1)
    return Image.alpha_composite(result, border)

def main():
    try:
        resp = requests.get(f"https://api.openweathermap.org/data/2.5/weather?q={CITY}&appid={API_KEY}&units=metric")
        data = resp.json()
        temp, feels, humidity = round(data["main"]["temp"]), round(data["main"]["feels_like"]), data["main"]["humidity"]
        wind, weather_id = round(data["wind"]["speed"] * 3.6), data["weather"][0]["id"]
        tz_offset = data.get("timezone", 3600)
        now_dt = datetime.now(timezone(timedelta(seconds=tz_offset)))
        weather_hu, rain_chance = get_weather_hu(weather_id), get_rain_chance(weather_id)
        image_name = get_image_name(weather_id, (now_dt.timestamp() < data["sys"]["sunrise"] or now_dt.timestamp() > data["sys"]["sunset"]))
    except: return

    src, dst = f"images/{image_name}.jpg", "images/current.jpg"
    img = Image.open(src).convert("RGB")
    W, H = img.size
    
    # --- JAVÍTOTT MÉRETEK (Szellősebb kártya) ---
    bw, bh = 440, 520  # Megemelt magasság a 0.5 cm-es pluszhoz
    bx, by = W - bw - 70, (H - bh) // 2

    # FÉNYERŐ FIGYELÉS (Sötét/Világos mód választás)
    region = img.crop((bx, by, bx + bw, by + bh)).convert("L")
    avg_brightness = ImageStat.Stat(region).mean[0]
    
    if avg_brightness > 145: # Világos háttér esetén
        glass_c, t_main, t_dim, l_color = (255, 255, 255, 140), (0, 0, 0, 230), (0, 0, 0, 130), (0, 0, 0, 40)
    else: # Sötét háttér esetén
        glass_c, t_main, t_dim, l_color = (0, 0, 0, 110), (255, 255, 255, 255), (255, 255, 255, 140), (255, 255, 255, 30)

    card = create_blurred_card(img, bx, by, bw, bh, glass_c)
    img = img.convert("RGBA")
    img.paste(card, (bx, by), card)
    draw = ImageDraw.Draw(img)

    def get_f(s, b=False):
        p = ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if b else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "arial.ttf"]
        for f in p: 
            if os.path.exists(f): return ImageFont.truetype(f, s)
        return ImageFont.load_default()

    f_t, f_l, f_v, f_f = get_f(90, True), get_f(22), get_f(24, True), get_f(18)
    
    # 1. Nagy hőmérséklet
    m, cy = 40, by + 40
    txt = f"{temp}°"
    tw = draw.textbbox((0,0), txt, font=f_t)[2]
    draw.text((bx + (bw - tw)//2, cy), txt, font=f_t, fill=t_main)
    cy += 135
    
    # 2. Adatsorok
    rows = [("ÉRZET", f"{feels} °C"), ("IDŐJÁRÁS", weather_hu.upper()), ("CSAPADÉK", f"{rain_chance}%"), ("PÁRA", f"{humidity}%"), ("SZÉL", f"{wind} km/h")]
    for lab, val in rows:
        draw.text((bx + m, cy), lab, font=f_l, fill=t_dim)
        vw = draw.textbbox((0,0), val, font=f_v)[2]
        draw.text((bx + bw - m - vw, cy), val, font=f_v, fill=t_main)
        draw.line([(bx + m, cy + 45), (bx + bw - m, cy + 45)], fill=l_color, width=1)
        cy += 65

    # --- JAVÍTOTT FOOTER (Budapest sor letolása a csík alá) ---
    ly = by + bh - 65 # A vonal fix távolságra a kártya aljától
    draw.line([(bx + m, ly), (bx + bw - m, ly)], fill=l_color, width=1)
    
    ftxt = f"{CITY.upper()} • {now_dt.strftime('%H:%M')}"
    fw = draw.textbbox((0,0), ftxt, font=f_f)[2]
    # Itt a +18 pixel tolja le a szöveget a vonal alá
    draw.text((bx + (bw - fw)//2, ly + 18), ftxt, font=f_f, fill=t_dim)

    img.convert("RGB").save(dst, "JPEG", quality=95)
    print(f"✓ {dst} mentve.")

if __name__ == "__main__": main()
