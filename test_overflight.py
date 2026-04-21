#!/usr/bin/env python3
import os
import sys
import time

print("=== TESZT SZKIPT INDIÍTÁSA ===")
print(f"Python verzió: {sys.version}")
print(f"Aktuális könyvtár: {os.getcwd()}")
print(f"Fájl létezik? {os.path.exists('test_overflight.py')}")

try:
    from PIL import Image, ImageDraw
    print("✓ PIL (Pillow) sikeresen betöltve")
except ImportError as e:
    print(f"✗ PIL Import hiba: {e}")
    sys.exit(1)

try:
    # 1. Mappa létrehozása
    print("\n1. Mappa ellenőrzés...")
    os.makedirs("images", exist_ok=True)
    print(f"   ✓ images mappa létezik: {os.path.exists('images')}")
    
    # 2. Kép generálása
    print("\n2. Kép generálása...")
    width, height = 3840, 2160
    img = Image.new('RGB', (width, height), color=(73, 109, 137))
    draw = ImageDraw.Draw(img)
    
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    draw.text((100, 100), f"TEST IMAGE - {timestamp}", fill=(255, 255, 255))
    draw.text((100, 200), "Overflight Plugin Test", fill=(255, 255, 255))
    print(f"   ✓ Kép mérete: {width}x{height}")
    
    # 3. Mentés
    print("\n3. Kép mentése...")
    output_path = "images/current.jpg"
    img.save(output_path, "JPEG", quality=95)
    print(f"   ✓ Mentve: {output_path}")
    
    # 4. Ellenőrzés
    print("\n4. Fájl ellenőrzés...")
    if os.path.exists(output_path):
        size = os.path.getsize(output_path)
        print(f"   ✓ Fájl létezik, mérete: {size} bytes")
        
        # Mappa tartalmának listázása
        print("\n5. images mappa tartalma:")
        for f in os.listdir("images"):
            print(f"   - {f}")
    else:
        print(f"   ✗ A fájl NEM létezik: {output_path}")
        sys.exit(1)
    
    # 6. weather.json frissítés
    print("\n6. weather.json frissítés...")
    import json
    weather_json = [{
        "location": "TEST",
        "title": f"Test {timestamp}",
        "author": "GitHub Action",
        "image_url": f"https://raw.githubusercontent.com/harsanyiz/weather-wallpaper/main/images/current.jpg?v={int(time.time())}",
        "url_img": f"https://raw.githubusercontent.com/harsanyiz/weather-wallpaper/main/images/current.jpg?v={int(time.time())}"
    }]
    
    with open("weather.json", "w", encoding="utf-8") as f:
        json.dump(weather_json, f, indent=2)
    print("   ✓ weather.json mentve")
    
    print("\n=== KÉSZ, SIKERESEN LÉTREJÖTT A KÉP ===")
    
except Exception as e:
    print(f"\n✗ HIBA: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
