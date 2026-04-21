#!/usr/bin/env python3
import os
import sys
import time
import random
from PIL import Image, ImageDraw, ImageFont

print("=== TESZT SZKIPT INDIÍTÁSA ===")

try:
    from PIL import Image, ImageDraw, ImageFont
    print("✓ PIL (Pillow) sikeresen betöltve")
except ImportError as e:
    print(f"✗ PIL Import hiba: {e}")
    sys.exit(1)

try:
    # Mappa létrehozása
    os.makedirs("images", exist_ok=True)
    
    # Kép mérete
    width, height = 3840, 2160
    
    # Véletlenszerű színű háttér
    random_color = (random.randint(0,255), random.randint(0,255), random.randint(0,255))
    img = Image.new('RGB', (width, height), color=random_color)
    draw = ImageDraw.Draw(img)
    
    # Betűtípus keresés (nagy méretben)
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ]
    
    font_size = 120  # NAGY betűméret
    font = None
    for path in font_paths:
        if os.path.exists(path):
            try:
                font = ImageFont.truetype(path, font_size)
                print(f"✓ Betűtípus betöltve: {path}")
                break
            except:
                continue
    
    if font is None:
        font = ImageFont.load_default()
        print("✓ Alapértelmezett betűtípus")
    
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    unique_id = int(time.time() * 1000)
    
    # Szövegek - MOST KÖZÉPRE IGAZÍTVA és NAGYON
    center_x = width // 2
    center_y = height // 2
    
    # 1. sor (fent)
    text1 = f"TEST IMAGE - {timestamp}"
    bbox1 = draw.textbbox((0, 0), text1, font=font)
    w1 = bbox1[2] - bbox1[0]
    draw.text((center_x - w1//2, 200), text1, fill=(255, 255, 255), font=font)
    
    # 2. sor (középen)
    text2 = f"Unique ID: {unique_id}"
    bbox2 = draw.textbbox((0, 0), text2, font=font)
    w2 = bbox2[2] - bbox2[0]
    draw.text((center_x - w2//2, center_y - 100), text2, fill=(255, 255, 255), font=font)
    
    # 3. sor (lent)
    text3 = f"Random color: {random_color}"
    bbox3 = draw.textbbox((0, 0), text3, font=font)
    w3 = bbox3[2] - bbox3[0]
    draw.text((center_x - w3//2, height - 300), text3, fill=(255, 255, 255), font=font)
    
    # Extra: nagy cím a tetején
    title_font_size = 180
    for path in font_paths:
        if os.path.exists(path):
            try:
                title_font = ImageFont.truetype(path, title_font_size)
                break
            except:
                continue
    else:
        title_font = ImageFont.load_default()
    
    title_text = "OVERFLIGHT TEST"
    title_bbox = draw.textbbox((0, 0), title_text, font=title_font)
    title_w = title_bbox[2] - title_bbox[0]
    draw.text((center_x - title_w//2, 100), title_text, fill=(255, 255, 0), font=title_font)
    
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
    import traceback
    traceback.print_exc()
    sys.exit(1)
