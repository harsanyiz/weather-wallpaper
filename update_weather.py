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
    """Becsült esély esőre/zivatarra az időjárás kód alapján"""
    if weather_id in range(200, 233):
        return 80  # Zivatar
    elif weather_id in range(500, 532):
        return 70  # Eső
    elif weather_id in range(300, 322):
        return 50  # Szitálás
    elif weather_id in [611, 612, 613, 615, 616]:
        return 60  # Ónos eső
    elif weather_id in [801, 802]:
        return 20  # Enyhén felhős
    elif weather_id in [803, 804]:
        return 30  # Felhős
    elif weather_id == 800:
        return 0   # Derült
    else:
        return 10

def main():
    # 1. Időjárás lekérés
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

    print(f"Időjárás: {weather_hu} ({weather_id}), esély: {rain_chance}%")

    # 2. Kép betöltése
    src = f"images/{image_name}.jpg"
    dst = "images/current.jpg"

    img = Image.open(src).convert("RGB")
    W, H = img.size  # 1920x1080

    # 3. Féláttetsző háttér a szöveg mögé (soft box)
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ov_draw = ImageDraw.Draw(overlay)
    
    # Soft box méretei (jobb oldalon, középtájon)
    box_width = 450
    box_height = 300
    box_x = W - box_width - 40  # jobb margó 40px
    box_y = int(H/2) - int(box_height/2)  # függőlegesen középre
    
    # Lekerekített sarkú téglalap (közelítőleg)
    ov_draw.rectangle([(box_x, box_y), (W - 40, box_y + box_height)], 
                      fill=(0, 0, 0, 140), outline=(255, 255, 255, 60), width=2)
    
    img = img.convert("RGBA")
    img = Image.alpha_composite(img, overlay)
    img = img.convert("RGB")
    draw = ImageDraw.Draw(img)

    # 4. Betűtípusok
    try:
        font_temp = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 110)
        font_feels = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 38)
        font_weather = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 42)
        font_detail = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 32)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 28)
    except:
        font_temp = ImageFont.load_default()
        font_feels = font_temp
        font_weather = font_temp
        font_detail = font_temp
        font_small = font_temp

    # 5. Pozíciók (soft boxon belül, balra igazítva a boxon belül)
    box_inner_x = box_x + 30
    y_offset = box_y + 40
    
    # Hőmérséklet (nagy szám)
    temp_text = f"{temp}°C"
    draw.text((box_inner_x, y_offset), temp_text, font=font_temp, fill=(255, 255, 255))
    
    # Érzet hőmérséklet (kisebbel alatta)
    feels_text = f"Érzet: {feels_like}°C"
    draw.text((box_inner_x, y_offset + 115), feels_text, font=font_feels, fill=(220, 220, 220))
    
    # Időjárás állapot + ikon (következő sor)
    weather_text = f"{weather_icon}  {weather_hu}"
    draw.text((box_inner_x, y_offset + 165), weather_text, font=font_weather, fill=(255, 255, 255))
    
    # Esély esőre (ha van)
    if rain_chance > 0:
        rain_text = f"🌧️  Csapadék esélye: {rain_chance}%"
        draw.text((box_inner_x, y_offset + 215), rain_text, font=font_detail, fill=(200, 200, 200))
    
    # Páratartalom és szél (egy sorban, egymás mellett)
    humid_text = f"💧 {humidity}%"
    wind_text = f"💨 {wind} km/h"
    
    # Két szöveg egymás mellett
    draw.text((box_inner_x, y_offset + 260), humid_text, font=font_small, fill=(180, 180, 180))
    # Mérd meg a humid_text szélességét
    bbox = draw.textbbox((0, 0), humid_text, font=font_small)
    humid_width = bbox[2] - bbox[0]
    draw.text((box_inner_x + humid_width + 30, y_offset + 260), wind_text, font=font_small, fill=(180, 180, 180))

    # 6. Dátum (kint a boxon kívül, alatta középre igazítva a boxhoz képest)
    now_hu = datetime.now(timezone(timedelta(hours=2))).strftime("%Y.%m.%d  %H:%M")
    date_text = f"📍 Budapest  •  {now_hu}"
    bbox = draw.textbbox((0, 0), date_text, font=font_small)
    date_width = bbox[2] - bbox[0]
    date_x = box_x + (box_width - date_width) // 2
    draw.text((date_x, box_y + box_height + 15), date_text, font=font_small, fill=(160, 160, 160))

    # 7. Kép mentése
    img.save(dst, "JPEG", quality=95)
    print(f"✓ current.jpg elkészült")

    # 8. JSON generálás
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
