# update_weather.py - FŐPROGRAM (összeköti a logikát és a kinézetet)
import json
import time
import os
from PIL import Image
from logic_weather import fetch_weather_data, get_day_hu, get_weather_hu
from ui_weather import draw_weather_widget

GITHUB_USER = "harsanyiz"
GITHUB_REPO = "weather-wallpaper"
BRANCH = "main"
BASE_URL = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/{BRANCH}/images"
CITY = "Budapest"

def main():
    try:
        # 1. Adatok lekérése (logika)
        weather_data, forecast_list, update_time, raw_data = fetch_weather_data()
        
        # 2. Háttérkép betöltése és méretezése
        src = f"images/{weather_data['image_name']}.jpg"
        dst = "images/current.jpg"
        img = Image.open(src).convert("RGB")
        if img.size != (3840, 2160):
            img = img.resize((3840, 2160), Image.Resampling.LANCZOS)
        
        # 3. Widget kirajzolása (kinézet)
        img = draw_weather_widget(img, weather_data, forecast_list, update_time)
        
        # 4. Mentés
        img.convert("RGB").save(dst, "JPEG", quality=100, subsampling=0)
        
        # 5. JSON frissítése
        v_param = int(time.time())
        image_url = f"{BASE_URL}/current.jpg?v={v_param}"
        weather_json = [{
            "location": CITY, 
            "title": f"{weather_data['weather_hu']} {weather_data['temp']}C", 
            "author": "Gemini Design", 
            "image_url": image_url, 
            "url_img": image_url
        }]
        with open("weather.json", "w", encoding="utf-8") as f:
            json.dump(weather_json, f, ensure_ascii=False, indent=2)
            
        print(f"Weather wallpaper updated successfully at {update_time}")
        
    except Exception as e:
        print(f"Hiba: {e}")

if __name__ == "__main__":
    main()
