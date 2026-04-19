import requests
import json
import os
import urllib.request
from datetime import datetime, timezone, timedelta
from PIL import Image, ImageDraw, ImageFont

# --- Konfig ---
API_KEY = os.environ.get("OWM_API_KEY", "f1140d0ccb478ba741a957a67dd074ca")
CITY = "Budapest"
GITHUB_USER = "harsanyiz"
GITHUB_REPO = "weather-wallpaper"
BRANCH = "main"

BASE_URL = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/{BRANCH}/images"

# Noto Color Emoji font letöltése ha nincs
EMOJI_FONT_PATH = "/tmp/NotoColorEmoji.ttf"
EMOJI_FONT_URL = "https://github.com/googlefonts/noto-emoji/raw/main/fonts/NotoColorEmoji.ttf"

def ensure_emoji_font():
    """Letölti a Noto Color Emoji fontot ha még nincs meg"""
    if not os.path.exists(EMOJI_FONT_PATH):
        print("📥 Noto Color Emoji font letöltése...")
        try:
            urllib.request.urlretrieve(EMOJI_FONT_URL, EMOJI_FONT_PATH)
            print("✓ Emoji font letöltve")
        except Exception as e:
            print(f"⚠️ Emoji font letöltés sikertelen: {e}")
            return False
    return True

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
    x1, y1, x2, y2 = xy
    draw.rectangle([(x1 + radius, y1), (x2 - radius, y2)], fill=fill, outline=outline, width=width)
    draw.rectangle([(x1, y1 + radius), (x2, y2 - radius)], fill=fill, outline=outline, width=width)
    draw.pieslice([(x1, y1), (x1 + radius * 2, y1 + radius * 2)], 180, 270, fill=fill, outline=outline, width=width)
    draw.pieslice([(x2 - radius * 2, y1), (x2, y1 + radius * 2)], 270, 360, fill=fill, outline=outline, width=width)
    draw.pieslice([(x1, y2 - radius * 2), (x1 + radius * 2, y2)], 90, 180, fill=fill, outline=outline, width=width)
    draw.pieslice([(x2 - radius * 2, y2 - radius * 2), (x2, y2)], 0, 90, fill=fill, outline=outline, width=width)

def main():
    # Emoji font előkészítése
    ensure_emoji_font()
    
    # Időjárás lekérés
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
    box_width = 520  # Kicsit szélesebb az emojik miatt
    box_height = 360
    box_x = W - box_width - 50
    box_y = int(H/2) - int(box_height/2)
    radius = 25

    # Átlátszó overlay
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ov_draw = ImageDraw.Draw(overlay)
    
    draw_rounded_rectangle(ov_draw, (box_x, box_y, box_x + box_width, box_y + box_height), 
                          radius, (0, 0, 0, 160), outline=(255, 255, 255, 80), width=2)
    
    img = img.convert("RGBA")
    img = Image.alpha_composite(img, overlay)
    img = img.convert("RGB")
    draw = ImageDraw.Draw(img)

    # Betűtípusok - EMOJIKHOZ KÜLÖN FONT!
    try:
        # Normál szöveghez DejaVu
        font_temp = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 95)
        font_feels = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 36)
        font_weather = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 40)
        font_detail = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 32)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 28)
        
        # Emoji font (ha van)
        if os.path.exists(EMOJI_FONT_PATH):
            font_emoji = ImageFont.truetype(EMOJI_FONT_PATH, 36)
            font_emoji_small = ImageFont.truetype(EMOJI_FONT_PATH, 28)
        else:
            font_emoji = font_detail
            font_emoji_small = font_small
    except Exception as e:
        print(f"Betűtípus betöltési hiba: {e}")
        font_temp = font_feels = font_weather = font_detail = font_small = font_emoji = font_emoji_small = ImageFont.load_default()

    # Pozíciók
    margin_left = 35
    x = box_x + margin_left
    y = box_y + 45
    
    # 1. Hőmérséklet
    draw.text((x, y), f"{temp}°C", font=font_temp, fill=(255, 255, 255))
    
    # 2. Érzet
    y += 115
    draw.text((x, y), f"Érzet: {feels_like}°C", font=font_feels, fill=(220, 220, 220))
    
    # 3. Időjárás + elválasztó
    y += 55
    draw.line([(x, y - 15), (box_x + box_width - margin_left, y - 15)], fill=(255, 255, 255, 60), width=1)
    
    # Emoji + szöveg külön rajzolva (hogy az emoji a megfelelő fon ttel jelenjen meg)
    draw.text((x, y), weather_icon, font=font_emoji, fill=(255, 255, 255))
    # Az emoji utáni szóköz és szöveg
    icon_width = draw.textbbox((0, 0), weather_icon, font=font_emoji)[2]
    draw.text((x + icon_width + 10, y), weather_hu, font=font_weather, fill=(255, 255, 255))
    
    # 4. Csapadék
    y += 55
    if rain_chance > 0:
        draw.text((x, y), "🌧️", font=font_emoji, fill=(200, 220, 255))
        rain_icon_width = draw.textbbox((0, 0), "🌧️", font=font_emoji)[2]
        draw.text((x + rain_icon_width + 10, y), f"Csapadék esélye: {rain_chance}%", font=font_detail, fill=(200, 220, 255))
    else:
        draw.text((x, y), "☀️", font=font_emoji, fill=(200, 220, 200))
        sun_icon_width = draw.textbbox((0, 0), "☀️", font=font_emoji)[2]
        draw.text((x + sun_icon_width + 10, y), "Csapadék nem várható", font=font_detail, fill=(200, 220, 200))
    
    # 5. Páratartalom és szél
    y += 48
    # Páratartalom emoji + szám
    draw.text((x, y), "💧", font=font_emoji_small, fill=(180, 180, 180))
    humid_icon_width = draw.textbbox((0, 0), "💧", font=font_emoji_small)[2]
    draw.text((x + humid_icon_width + 8, y), f"{humidity}%", font=font_small, fill=(180, 180, 180))
    
    # Szél
    humid_text_width = draw.textbbox((0, 0), f"{humidity}%", font=font_small)[2]
    wind_x = x + humid_icon_width + 8 + humid_text_width + 25
    draw.text((wind_x, y), "💨", font=font_emoji_small, fill=(180, 180, 180))
    wind_icon_width = draw.textbbox((0, 0), "💨", font=font_emoji_small)[2]
    draw.text((wind_x + wind_icon_width + 8, y), f"{wind} km/h", font=font_small, fill=(180, 180, 180))

    # 6. Dátum
    now_hu = datetime.now(timezone(timedelta(hours=2))).strftime("%Y.%m.%d. %H:%M")
    date_text = f"Budapest  •  {now_hu}"
    
    # Dátum emoji
    date_x = box_x + (box_width - 300) // 2  # Közelítő középre igazítás
    draw.text((date_x, box_y + box_height + 20), "📍", font=font_emoji_small, fill=(160, 160, 160))
    marker_width = draw.textbbox((0, 0), "📍", font=font_emoji_small)[2]
    draw.text((date_x + marker_width + 8, box_y + box_height + 20), date_text, font=font_small, fill=(160, 160, 160))

    img.save(dst, "JPEG", quality=95)
    print(f"✓ current.jpg elkészült (emojikkal)")

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
