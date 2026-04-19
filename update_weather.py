import requests
import json
import os
from datetime import datetime, timezone, timedelta
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# --- Konfig ---
# Próbáld meg környezeti változóból, de ha nincs, marad a default (GitHub Secret-be tedd majd!)
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
    if weather_id in [611, 612, 613, 615, 616]: return "Ónos eső"
    elif weather_id in [620, 621, 622, 600, 601, 602]: return "Havazás"
    elif weather_id == 511: return "Jégeső"
    elif weather_id in [781, 771, 762, 761, 751, 731, 721, 711, 701]: return "Köd"
    elif weather_id in range(200, 233): return "Zivatar"
    elif weather_id in range(500, 532): return "Eső"
    elif weather_id in range(300, 322): return "Szitálás"
    elif weather_id == 800: return "Derült"
    elif weather_id in [801, 802]: return "Enyhén felhős"
    elif weather_id in [803, 804]: return "Felhős"
    else: return "Változékony"

def get_rain_chance(weather_id):
    if weather_id in range(200, 233): return 80
    elif weather_id in range(500, 532): return 70
    elif weather_id in range(300, 322): return 50
    elif weather_id == 800: return 0
    else: return 20

def create_blurred_card(image, box_x, box_y, box_width, box_height, radius=30, blur_strength=15):
    # Kivágjuk a területet a blurözéshez
    box_area = image.crop((box_x, box_y, box_x + box_width, box_y + box_height))
    blurred = box_area.filter(ImageFilter.GaussianBlur(blur_strength))
    
    # Maszk a lekerekített sarkokhoz
    mask = Image.new("L", (box_width, box_height), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle((0, 0, box_width, box_height), radius=radius, fill=255)
    
    # Sötétített réteg (üveg hatás)
    glass = Image.new("RGBA", (box_width, box_height), (0, 0, 0, 110)) # 110-es sötétítés a kontrasztért
    
    blurred = blurred.convert("RGBA")
    blurred.putalpha(mask)
    
    # Összeillesztés
    result = Image.alpha_composite(blurred, glass)
    
    # Finom fehér keret
    border = Image.new("RGBA", (box_width, box_height), (0, 0, 0, 0))
    border_draw = ImageDraw.Draw(border)
    border_draw.rounded_rectangle((0, 0, box_width, box_height), radius=radius, outline=(255, 255, 255, 40), width=1)
    
    return Image.alpha_composite(result, border)

def main():
    # 1. Adatok lekérése
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?q={CITY}&appid={API_KEY}&units=metric"
        resp = requests.get(url)
        data = resp.json()

        temp = round(data["main"]["temp"])
        feels_like = round(data["main"]["feels_like"])
        humidity = data["main"]["humidity"]
        wind = round(data["wind"]["speed"] * 3.6)
        weather_id = data["weather"][0]["id"]
        
        # Időzóna alapú óra (Budapest)
        tz_offset = data.get("timezone", 3600)
        now_dt = datetime.now(timezone(timedelta(seconds=tz_offset)))
        
        sunrise = data["sys"]["sunrise"]
        sunset = data["sys"]["sunset"]
        now_ts = datetime.now(timezone.utc).timestamp()
        is_night = now_ts < sunrise or now_ts > sunset

        weather_hu = get_weather_hu(weather_id)
        rain_chance = get_rain_chance(weather_id)
        image_name = get_image_name(weather_id, is_night)
    except Exception as e:
        print(f"Hiba az adatoknál: {e}")
        return

    # 2. Kép betöltése
    src = f"images/{image_name}.jpg"
    dst = "images/current.jpg"
    
    if not os.path.exists(src):
        # Ha nincs meg a specifikus kép, fallback egy alapra
        print(f"Hiányzó kép: {src}, próbálkozás alapértelmezettel...")
        src = "images/cloudy_day.jpg"

    img = Image.open(src).convert("RGB")
    W, H = img.size

    # 3. Kártya méretezés (Jobbra középre)
    box_width = 440
    box_height = 500
    box_x = W - box_width - 70
    box_y = (H - box_height) // 2

    # Üveg kártya felhelyezése
    blurred_card = create_blurred_card(img, box_x, box_y, box_width, box_height)
    img = img.convert("RGBA")
    img.paste(blurred_card, (box_x, box_y), blurred_card)
    draw = ImageDraw.Draw(img)

    # 4. Betűtípusok betöltése
    def get_font(size, bold=False):
        paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "C:/Windows/Fonts/arial.ttf",
            "/System/Library/Fonts/Cache/Roboto-Bold.ttf"
        ]
        for p in paths:
            if os.path.exists(p): return ImageFont.truetype(p, size)
        return ImageFont.load_default()

    font_temp = get_font(90, True)
    font_label = get_font(22, False)
    font_value = get_font(24, True)
    font_footer = get_font(18, False)

    # 5. Rajzolás
    margin = 40
    curr_y = box_y + 40

    # Fő hőmérséklet (Középre a kártyán)
    t_text = f"{temp}°"
    t_bbox = draw.textbbox((0, 0), t_text, font=font_temp)
    t_w = t_bbox[2] - t_bbox[0]
    draw.text((box_x + (box_width - t_w)//2, curr_y), t_text, font=font_temp, fill=(255, 255, 255, 255))
    
    curr_y += 130

    # Adatsorok kirajzolása (Balra címke, Jobbra érték)
    rows = [
        ("ÉRZET", f"{feels_like} °C"),
        ("IDŐJÁRÁS", weather_hu.upper()),
        ("CSAPADÉK", f"{rain_chance}%"),
        ("PÁRATARTALOM", f"{humidity}%"),
        ("SZÉLSEBESSÉG", f"{wind} km/h")
    ]

    for label, val in rows:
        # Címke
        draw.text((box_x + margin, curr_y), label, font=font_label, fill=(255, 255, 255, 140))
        # Érték (Jobbra igazítva)
        v_bbox = draw.textbbox((0, 0), val, font=font_value)
        v_w = v_bbox[2] - v_bbox[0]
        draw.text((box_x + box_width - margin - v_w, curr_y), val, font=font_value, fill=(255, 255, 255, 255))
        
        # Elválasztó vonal
        line_y = curr_y + 45
        draw.line([(box_x + margin, line_y), (box_x + box_width - margin, line_y)], fill=(255, 255, 255, 30), width=1)
        curr_y += 65

    # Footer (Város + Idő)
    footer_text = f"{CITY.upper()} • {now_dt.strftime('%H:%M')}"
    f_bbox = draw.textbbox((0, 0), footer_text, font=font_footer)
    f_w = f_bbox[2] - f_bbox[0]
    draw.text((box_x + (box_width - f_w)//2, box_y + box_height - 35), footer_text, font=font_footer, fill=(255, 255, 255, 100))

    # Mentés
    img.convert("RGB").save(dst, "JPEG", quality=95)
    print(f"✓ {dst} elkészült: {weather_hu}, {temp}°C")

    # JSON frissítése a widgeteknek
    weather_json = [{
        "location": CITY,
        "title": f"{weather_hu} • {temp}°C",
        "url_img": f"{BASE_URL}/current.jpg"
    }]
    with open("weather.json", "w", encoding="utf-8") as f:
        json.dump(weather_json, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
