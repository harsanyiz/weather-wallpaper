import requests
import json
import os
from datetime import datetime, timezone, timedelta
from PIL import Image, ImageDraw, ImageFont

# --- Konfig ---
API_KEY = os.environ.get("OWM_API_KEY", "f1140d0ccb478ba741a957a67dd074ca")
CITY = "Budapest"
GITHUB_USER = "harsanyiz"
GITHUB_REPO = "weather-wallpaper"
BRANCH = "main"

BASE_URL = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/{BRANCH}/images"

def get_image_name(weather_id, is_night):
    suffix = "night" if is_night else "day"
    if weather_id in [611, 612, 613, 615, 616]:
        return f"sleet_{suffix}"
    elif weather_id in [620, 621, 622, 600, 601, 602]:
        return f"snow_{suffix}"
    elif weather_id in [511]:
        return f"hail_{suffix}"
    elif weather_id in [781, 771, 762, 761, 751, 731, 721, 711, 701]:
        return f"foggy_{suffix}"
    elif weather_id in [200, 201, 202, 210, 211, 212, 221, 230, 231, 232]:
        return f"hail_{suffix}"
    elif weather_id in range(500, 532):
        return f"rainy_{suffix}"
    elif weather_id in range(300, 322):
        return f"rainy_{suffix}"
    elif weather_id in [800]:
        return f"sunny_{suffix}"
    elif weather_id in [801, 802, 803, 804]:
        return f"cloudy_{suffix}"
    else:
        return f"cloudy_{suffix}"

def get_weather_hu(weather_id):
    if weather_id in [611, 612, 613, 615, 616]:
        return "Ónos eső"
    elif weather_id in [620, 621, 622, 600, 601, 602]:
        return "Havazás"
    elif weather_id == 511:
        return "Jégeső"
    elif weather_id in [781, 771, 762, 761, 751, 731, 721, 711, 701]:
        return "Köd"
    elif weather_id in range(200, 233):
        return "Zivatar"
    elif weather_id in range(500, 532):
        return "Eső"
    elif weather_id in range(300, 322):
        return "Szitálás"
    elif weather_id == 800:
        return "Derült"
    elif weather_id in [801, 802]:
        return "Enyhén felhős"
    elif weather_id in [803, 804]:
        return "Felhős"
    else:
        return "Változékony"

def get_weather_icon(weather_id):
    if weather_id in [611, 612, 613, 615, 616]:
        return "🌨️"
    elif weather_id in [620, 621, 622, 600, 601, 602]:
        return "❄️"
    elif weather_id == 511:
        return "🧊"
    elif weather_id in [781, 771, 762, 761, 751, 731, 721, 711, 701]:
        return "🌫️"
    elif weather_id in range(200, 233):
        return "⛈️"
    elif weather_id in range(500, 532):
        return "🌧️"
    elif weather_id in range(300, 322):
        return "💧"
    elif weather_id == 800:
        return "☀️"
    elif weather_id in [801, 802]:
        return "⛅"
    elif weather_id in [803, 804]:
        return "☁️"
    else:
        return "🌡️"

def get_rain_chance(weather_id):
    if weather_id in range(200, 233):
        return 80
    elif weather_id in range(500, 532):
        return 70
    elif weather_id in range(300, 322):
        return 50
    elif weather_id in [611, 612, 613, 615, 616]:
        return 60
    elif weather_id in [801, 802]:
        return 20
    elif weather_id in [803, 804]:
        return 30
    elif weather_id == 800:
        return 0
    else:
        return 10

def draw_rounded_rectangle(draw, xy, radius, fill, outline=None, width=1):
    """Lekerekített sarkú téglalap rajzolása"""
    x1, y1, x2, y2 = xy
    draw.rectangle([(x1 + radius, y1), (x2 - radius, y2)], fill=fill, outline=outline, width=width)
    draw.rectangle([(x1, y1 + radius), (x2, y2 - radius)], fill=fill, outline=outline, width=width)
    draw.pieslice([(x1, y1), (x1 + radius * 2, y1 + radius * 2)], 180, 270, fill=fill, outline=outline, width=width)
    draw.pieslice([(x2 - radius * 2, y1), (x2, y1 + radius * 2)], 270, 360, fill=fill, outline=outline, width=width)
    draw.pieslice([(x1, y2 - radius * 2), (x1 + radius * 2, y2)], 90, 180, fill=fill, outline=outline, width=width)
    draw.pieslice([(x2 - radius * 2, y2 - radius * 2), (x2, y2)], 0, 90, fill=fill, outline=outline, width=width)

def main():
    url = f"https://api.openweathermap.org/data/2.5/weather?q={CITY}&appid={API_KEY}&units=metric"
    resp = requests.get(url)
    data = resp.json()

    temp = round(data["main"]["temp"])
    feels_like = round(data["main"]["feels_like"])
    humidity = data["main"]["humidity"]
    wind = round(data["wind"]["speed"] * 3.6)
    weather_id = data["weather"][0]["id"]
    sunrise = data["sys"]["sunrise"]
    sunset = data["sys"]["sunset"]

    now_ts = datetime.now(timezone.utc).timestamp()
    is_night = now_ts < sunrise or now_ts > sunset

    weather_hu = get_weather_hu(weather_id)
    weather_icon = get_weather_icon(weather_id)
    rain_chance = get_rain_chance(weather_id)
    image_name = get_image_name(weather_id, is_night)

    print(f"{weather_hu} | {temp}°C | Csapadék: {rain_chance}%")

    # Kép betöltése
    src = f"images/{image_name}.jpg"
    dst = "images/current.jpg"

    img = Image.open(src).convert("RGB")
    W, H = img.size

    # Soft box paraméterei
    box_width = 480
    box_height = 340
    box_x = W - box_width - 50
    box_y = int(H/2) - int(box_height/2)
    radius = 25

    # Átlátszó overlay
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ov_draw = ImageDraw.Draw(overlay)
    
    # Lekerekített sarkú háttér
    draw_rounded_rectangle(ov_draw, (box_x, box_y, box_x + box_width, box_y + box_height), 
                          radius, (0, 0, 0, 160), outline=(255, 255, 255, 80), width=2)
    
    img = img.convert("RGBA")
    img = Image.alpha_composite(img, overlay)
    img = img.convert("RGB")
    draw = ImageDraw.Draw(img)

    # Betűtípusok
    try:
        font_temp = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 95)
        font_feels = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 36)
        font_weather = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 40)
        font_detail = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 32)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 28)
    except:
        font_temp = font_feels = font_weather = font_detail = font_small = ImageFont.load_default()

    # Pozíciók (jobb oldalon, boxon belül balra igazítva)
    margin_left = 35
    x = box_x + margin_left
    y = box_y + 45
    
    # 1. Hőmérséklet
    draw.text((x, y), f"{temp}°C", font=font_temp, fill=(255, 255, 255))
    
    # 2. Érzet (kicsit lejjebb)
    y += 115
    draw.text((x, y), f"Érzet: {feels_like}°C", font=font_feels, fill=(220, 220, 220))
    
    # 3. Időjárás (vonalzóval elválasztva)
    y += 55
    # Vékony elválasztó
    draw.line([(x, y - 15), (box_x + box_width - margin_left, y - 15)], fill=(255, 255, 255, 60), width=1)
    
    draw.text((x, y), f"{weather_icon}  {weather_hu}", font=font_weather, fill=(255, 255, 255))
    
    # 4. Csapadék esély (ha van)
    y += 55
    if rain_chance > 0:
        draw.text((x, y), f"🌧️  Csapadék esélye: {rain_chance}%", font=font_detail, fill=(200, 220, 255))
    else:
        draw.text((x, y), f"☀️  Csapadék nem várható", font=font_detail, fill=(200, 220, 200))
    
    # 5. Páratartalom és szél egy sorban
    y += 48
    humid_text = f"💧 {humidity}%"
    wind_text = f"💨 {wind} km/h"
    
    draw.text((x, y), humid_text, font=font_small, fill=(180, 180, 180))
    bbox = draw.textbbox((0, 0), humid_text, font=font_small)
    humid_width = bbox[2] - bbox[0]
    draw.text((x + humid_width + 30, y), wind_text, font=font_small, fill=(180, 180, 180))

    # 6. Dátum és hely (box alatt, középen)
    now_hu = datetime.now(timezone(timedelta(hours=2))).strftime("%Y.%m.%d. %H:%M")
    date_text = f"📍  Budapest  •  {now_hu}"
    
    bbox = draw.textbbox((0, 0), date_text, font=font_small)
    date_width = bbox[2] - bbox[0]
    date_x = box_x + (box_width - date_width) // 2
    draw.text((date_x, box_y + box_height + 20), date_text, font=font_small, fill=(160, 160, 160))

    img.save(dst, "JPEG", quality=95)
    print(f"✓ current.jpg elkészült")

    # JSON
    image_url = f"{BASE_URL}/current.jpg"
    weather_json = [{
        "location": "Budapest",
        "title": f"{weather_icon} {weather_hu} • {temp}°C",
        "author": "OpenWeatherMap",
        "url_img": image_url
    }]

    with open("weather.json", "w", encoding="utf-8") as f:
        json.dump(weather_json, f, ensure_ascii=False, indent=2)

    print(f"✓ weather.json elkészült")

if __name__ == "__main__":
    main()
