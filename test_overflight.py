#!/usr/bin/env python3
import os
import sys
import time
import random
from PIL import Image, ImageDraw

print("=== TESZT SZKIPT INDIÍTÁSA ===")

try:
    from PIL import Image, ImageDraw
    print("✓ PIL (Pillow) sikeresen betöltve")
except ImportError as e:
    print(f"✗ PIL Import hiba: {e}")
    sys.exit(1)

try:
    # Mappa létrehozása
    os.makedirs("images", exist_ok=True)
    
    # Véletlenszerű színű kép
    width, height = 3840, 2160
    random_color = (random.randint(0,255), random.randint(0,255), random.randint(0,255))
    img = Image.new('RGB', (width, height), color=random_color)
    draw = ImageDraw.Draw(img)
    
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    unique_id = int(time.time() * 1000)  # Egyedi ID
    
    # Szövegek
    draw.text((100, 100), f"TEST IMAGE - {timestamp}", fill=(255, 255, 255))
    draw.text((100, 200), f"Unique ID: {unique_id}", fill=(255, 255, 255))
    draw.text((100, 300), f"Random color: {random_color}", fill=(255, 255, 255))
    
    # Mentés
    output_path = "images/current.jpg"
    img.save(output_path, "JPEG", quality=95)
    print(f"✓ Kép mentve: {output_path} (méret: {os.path.getsize(output_path)} bytes)")
    
    # weather.json frissítés
    import json
    weather_json = [{
        "location": "TEST",
        "title": f"Test {timestamp}",
        "author": "GitHub Action",
        "image_url": f"https://raw.githubusercontent.com/harsanyiz/weather-wallpaper/main/images/current.jpg?v={unique_id}",
        "url_img": f"https://raw.githubusercontent.com/harsanyiz/weather-wallpaper/main/images/current.jpg?v={unique_id}"
    }]
    
    with open("weather.json", "w", encoding="utf-8") as f:
        json.dump(weather_json, f, indent=2)
    print("✓ weather.json frissítve")
    
    print("=== KÉSZ ===")
    
except Exception as e:
    print(f"✗ HIBA: {e}")
    sys.exit(1)
