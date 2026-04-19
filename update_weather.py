import requests
import json
import os
import shutil
from datetime import datetime, timezone, timedelta
from PIL import Image, ImageDraw, ImageFont

# --- Konfig ---
API_KEY = os.environ.get("OWM_API_KEY", "f1140d0ccb478ba741a957a67dd074ca")
CITY = "Budapest"
GITHUB_USER = "harsanyiz"
GITHUB_REPO = "weather-wallpaper"
BRANCH = "main"

BASE_URL = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/{BRANCH}/images"

# OpenWeatherMap weather condition -> kép mapping
def get_image_name(weather_id, is_night):
    suffix = "night" if is_night else "day"

    if weather_id in [611, 612, 613, 615, 616]:  # Sleet / ónos
        return f"sleet_{suffix}"
    elif weather_id in [620, 621, 622, 600, 601, 602]:  # Snow
        return f"snow_{suffix}"
    elif weather_id in [511]:  # Freezing rain = jégeső
        return f"hail_{suffix}"
    elif weather_id in [781, 771, 762, 761, 751, 731, 721, 711, 701]:  # Fog/mist/haze
        return f"foggy_{suffix}"
    elif weather_id in [200, 201, 202, 210, 211, 212, 221, 230, 231, 232]:  # Thunder
        return f"hail_{suffix}"
    elif weather_id in range(500, 532):  # Rain
        return f"rainy_{suffix}"
    elif weather_id in range(300, 322):  # Drizzle
        return f"rainy_{suffix}"
    elif weather_id in [800]:  # Clear
        return f"sunny_{suffix}"
    elif weather_id in [801, 802, 803, 804]:  # Clouds
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

def main():
    # 1. Időjárás lekérés
    url = f"https://api.openweathermap.org/data/2.5/weather?q={CITY}&appid={API_KEY}&units=metric"
    resp = requests.get(url)
    data = resp.json()

    temp = round(data["main"]["temp"])
    feels_like = round(data["main"]["feels_like"])
    humidity = data["main"]["humidity"]
    wind = round(data["wind"]["speed"] * 3.6)  # m/s -> km/h
    weather_id = data["weather"][0]["id"]
    sunrise = data["sys"]["sunrise"]
    sunset = data["sys"]["sunset"]

    now_ts = datetime.now(timezone.utc).timestamp()
    is_night = now_ts < sunrise or now_ts > sunset

    weather_hu = get_weather_hu(weather_id)
    image_name = get_image_name(weather_id, is_night)

    print(f"Időjárás: {weather_hu} ({weather_id}), {'éjszaka' if is_night else 'nappal'}")
    print(f"Kép: {image_name}.jpg")
    print(f"Hőmérséklet: {temp}°C")

    # 2. Képre szöveg írása
    src = f"images/{image_name}.jpg"
    dst = "images/current.jpg"

    img = Image.open(src).convert("RGB")

    # Féláttetsző sáv jobb alulra
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ov_draw = ImageDraw.Draw(overlay)
    ov_draw.rectangle([(1020, 880), (1920, 1080)], fill=(0, 0, 0, 160))
    img = img.convert("RGBA")
    img = Image.alpha_composite(img, overlay)
    img = img.convert("RGB")
    draw = ImageDraw.Draw(img)

    # Betűméret – ImageFont nélkül default font 3x-os méret nem megy,
    # ezért ImageFont.truetype-ot próbálunk, fallback default
    try:
        font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 72)
        font_mid   = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 48)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 36)
    except:
        font_large = ImageFont.load_default()
        font_mid   = font_large
        font_small = font_large

    now_hu = datetime.now(timezone(timedelta(hours=2))).strftime("%Y.%m.%d  %H:%M")

    # Jobbra igazított szövegek
    W = 1920
    margin = 40

    def rtext(draw, y, text, font, fill):
        bbox = draw.textbbox((0, 0), text, font=font)
        w = bbox[2] - bbox[0]
        draw.text((W - margin - w, y), text, font=font, fill=fill)

    rtext(draw, 900,  f"{temp}°C  •  {weather_hu}", font_large, (255, 255, 255))
    rtext(draw, 990,  f"Érzet: {feels_like}°C  •  Páratartalom: {humidity}%  •  Szél: {wind} km/h", font_mid, (220, 220, 220))
    rtext(draw, 1045, f"Budapest  •  {now_hu}", font_small, (180, 180, 180))

    img.save(dst, "JPEG", quality=97)
    print(f"✓ current.jpg elkészült")

    # 3. JSON generálás
    image_url = f"{BASE_URL}/current.jpg"

    weather_json = [
        {
            "location": "Budapest",
            "title": f"{weather_hu} • {temp}°C",
            "author": "OpenWeatherMap",
            "url_img": image_url
        }
    ]

    with open("weather.json", "w", encoding="utf-8") as f:
        json.dump(weather_json, f, ensure_ascii=False, indent=2)

    print(f"✓ weather.json elkészült")
    print(f"JSON URL lesz: https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/{BRANCH}/weather.json")

if __name__ == "__main__":
    main()
