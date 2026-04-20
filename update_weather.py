import requests
import json
import os
import time
from datetime import datetime, timezone, timedelta
from PIL import Image, ImageDraw, ImageFont

# Konfiguráció
API_KEY = os.environ.get("OWM_API_KEY")
GITHUB_USER = "harsanyiz"
GITHUB_REPO = "weather-wallpaper"
BRANCH = "main"
BASE_URL = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/{BRANCH}/images"

CITY = "Budapest"
WIDGET_Y = 150 # Lejjebb visszük kicsit
OFFSET_LEFT = 150

def get_text_icon(weather_id):
    # Brutálisan egyszerűsített szöveges jelzések
    if weather_id == 800: return "[ NAP ]"
    elif 801 <= weather_id <= 804: return "{ FELHO }"
    elif 500 <= weather_id <= 531: return "/ ESO /"
    elif 600 <= weather_id <= 622: return "* HO *"
    return "( ! )"

def main():
    try:
        resp = requests.get(f"https://api.openweathermap.org/data/2.5/weather?q={CITY}&appid={API_KEY}&units=metric").json()
        temp = round(resp["main"]["temp"])
        weather_id = resp["weather"][0]["id"]
        tz_offset = resp.get("timezone", 3600)
        now_dt = datetime.now(timezone(timedelta(seconds=tz_offset)))
        update_time = now_dt.strftime("%H:%M")
        
        is_night = now_dt.timestamp() < resp["sys"]["sunrise"] or now_dt.timestamp() > resp["sys"]["sunset"]
        bg_name = "sunny_day" if weather_id == 800 and not is_night else "cloudy_day"
        if is_night: bg_name = bg_name.replace("day", "night")
        
        # 4K helyett Full HD-val próbáljuk, mert a szövegesnél ez stabilabb
        img = Image.open(f"images/{bg_name}.jpg").convert("RGB").resize((1920, 1080))
        draw = ImageDraw.Draw(img)
        
        # Fontok betöltése
        try:
            # Vastag betűtípust használunk az ikon helyett
            font_big = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 80)
            font_main = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 120)
            font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 30)
        except:
            font_big = font_main = font_small = ImageFont.load_default()

        icon_text = get_text_icon(weather_id)
        
        # ELRENDEZÉS: Csak szöveg, semmi vonal, semmi alakzat
        # 1. Ikon szöveggel
        draw.text((OFFSET_LEFT, WIDGET_Y), icon_text, font=font_big, fill=(255, 255, 0))
        
        # 2. Hőmérséklet
        draw.text((OFFSET_LEFT + 400, WIDGET_Y - 20), f"{temp}°C", font=font_main, fill=(255, 255, 255))
        
        # 3. Időbélyeg
        draw.text((OFFSET_LEFT + 400, WIDGET_Y + 110), f"FRISSITVE: {update_time}", font=font_small, fill=(200, 200, 200))

        # MENTÉS: Alacsony minőségű JPEG, hogy a fájlméret ne legyen gond
        img.save("images/current.jpg", "JPEG", quality=75, optimize=True)

        # JSON frissítés egyedi URL-lel
        v_param = int(time.time())
        weather_json = [{
            "location": CITY, 
            "title": f"{temp}C - {update_time}", 
            "image_url": f"{BASE_URL}/current.jpg?v={v_param}"
        }]
        
        with open("weather.json", "w", encoding="utf-8") as f:
            json.dump(weather_json, f, ensure_ascii=False, indent=2)

    except Exception as e:
        print(f"Hiba: {e}")

if __name__ == "__main__":
    main()
