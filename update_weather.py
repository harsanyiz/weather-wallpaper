import requests
import json
import os
from datetime import datetime, timezone, timedelta
from PIL import Image, ImageDraw, ImageFont, ImageFilter

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

def create_blurred_card(image, box_x, box_y, box_width, box_height, radius=25, blur_strength=12):
    box_area = image.crop((box_x, box_y, box_x + box_width, box_y + box_height))
    blurred = box_area.filter(ImageFilter.GaussianBlur(blur_strength))
    
    mask = Image.new("L", (box_width, box_height), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle((0, 0, box_width, box_height), radius=radius, fill=255)
    
    glass = Image.new("RGBA", (box_width, box_height), (0, 0, 0, 80))
    
    blurred = blurred.convert("RGBA")
    blurred.putalpha(mask)
    glass.putalpha(mask.point(lambda p: p * 0.6))
    
    result = Image.alpha_composite(blurred, glass)
    
    border = Image.new("RGBA", (box_width, box_height), (0, 0, 0, 0))
    border_draw = ImageDraw.Draw(border)
    border_draw.rounded_rectangle((0, 0, box_width, box_height), radius=radius, outline=(255, 255, 255, 40), width=1)
    
    result = Image.alpha_composite(result, border)
    return result

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
    rain_chance = get_rain_chance(weather_id)
    image_name = get_image_name(weather_id, is_night)

    print(f"{weather_hu} | {temp}°C | Csapadék: {rain_chance}%")

    src = f"images/{image_name}.jpg"
    dst = "images/current.jpg"

    img = Image.open(src).convert("RGB")
    W, H = img.size

    # Box méretei - elég széles
    box_width = 380
    box_height = 400
    box_x = W - box_width - 50
    box_y = int(H/2) - int(box_height/2)
    radius = 24

    blurred_card = create_blurred_card(img, box_x, box_y, box_width, box_height, radius, blur_strength=10)
    
    img = img.convert("RGBA")
    img.paste(blurred_card, (box_x, box_y), blurred_card)
    img = img.convert("RGB")
    draw = ImageDraw.Draw(img)

    # Betűtípusok
    try:
        font_temp = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 80)
        font_label = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 26)
        font_value = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 26)
        font_date = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
    except:
        font_temp = font_label = font_value = font_date = ImageFont.load_default()

    margin_left = 30
    x = box_x + margin_left
    y = box_y + 45
    
    # 1. Hőmérséklet - középen
    temp_text = f"{temp}°C"
    bbox = draw.textbbox((0, 0), temp_text, font=font_temp)
    temp_width = bbox[2] - bbox[0]
    temp_x = box_x + (box_width - temp_width) // 2
    draw.text((temp_x, y), temp_text, font=font_temp, fill=(255, 255, 255))
    
    # Keret
    frame_padding = 15
    draw.rectangle([(temp_x - frame_padding, y - frame_padding), 
                    (temp_x + temp_width + frame_padding, y + (bbox[3] - bbox[1]) + frame_padding)], 
                   outline=(255, 255, 255, 50), width=2)
    
    # 2. Érzet (egy sor)
    y += 105
    draw.text((x, y), "ÉRZET", font=font_label, fill=(180, 180, 180))
    draw.text((x + 100, y), f"{feels_like}°C", font=font_value, fill=(255, 255, 255))
    
    # Elválasztó
    y += 40
    draw.line([(x, y), (box_x + box_width - margin_left, y)], fill=(255, 255, 255, 40), width=1)
    
    # 3. Időjárás (egy sor)
    y += 38
    draw.text((x, y), "IDŐJÁRÁS", font=font_label, fill=(180, 180, 180))
    draw.text((x + 100, y), weather_hu, font=font_value, fill=(255, 255, 255))
    
    # 4. Csapadék (egy sor)
    y += 45
    draw.text((x, y), "CSAPADÉK", font=font_label, fill=(180, 180, Espes))
    if rain_chance > 0:
        draw.text((x + 100, y), f"{rain_chance}%", font=font_value, fill=(200, 220, 255))
    else:
        draw.text((x + 100, y), "nincs", font=font_value, fill=(200, 220, 200))
    
    # 5. Páratartalom + Szél EGY SORBAN (hogy elférjen)
    y += 45
    
    # Páratartalom
    draw.text((x, y), "PÁRA", font=font_label, fill=(180, 180, 180))
    draw.text((x + 70, y), f"{humidity}%", font=font_value, fill=(255, 255, 255))
    
    # Szél (jobb oldalra)
    wind_text = f"{wind} km/h"
    wind_label = "SZÉL"
    
    # Szél címke jobb oldalra
    wind_label_x = box_x + box_width - margin_left - 120
    draw.text((wind_label_x, y), wind_label, font=font_label, fill=(180, 180, 180))
    draw.text((wind_label_x + 60, y), wind_text, font=font_value, fill=(255, 255, 255))

    # Dátum és hely
    now_hu = datetime.now(timezone(timedelta(hours=2))).strftime("%Y.%m.%d. %H:%M")
    date_text = f"Budapest  |  {now_hu}"
    
    date_y = box_y + box_height + 22
    bbox = draw.textbbox((0, 0), date_text, font=font_date)
    date_width = bbox[2] - bbox[0]
    date_x = box_x + (box_width - date_width) // 2
    
    draw.text((date_x, date_y), date_text, font=font_date, fill=(130, 130, 130))

    img.save(dst, "JPEG", quality=95)
    print(f"✓ current.jpg elkészült")

    image_url = f"{BASE_URL}/current.jpg"
    weather_json = [{
        "location": "Budapest",
        "title": f"{weather_hu} • {temp}°C",
        "author": "OpenWeatherMap",
        "url_img": image_url
    }]

    with open("weather.json", "w", encoding="utf-8") as f:
        json.dump(weather_json, f, ensure_ascii=False, indent=2)

    print(f"✓ weather.json elkészült")

if __name__ == "__main__":
    main()
