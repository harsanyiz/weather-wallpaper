#!/usr/bin/env python3
import requests
import json
import os
import time
from io import BytesIO
from datetime import datetime, timezone, timedelta
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# ============================================================
# TV-OPTIMALIZÁLT KONFIGURÁCIÓ
# ============================================================
CONFIG = {
    "city": "Budapest",
    "api_key": os.environ.get("OWM_API_KEY"),
    "github_user": "harsanyiz",
    "github_repo": "weather-wallpaper",
    "branch": "main",
    
    # 4K TV SAFE MÉRETEK
    "canvas_size": (3840, 2160),
    "widget_width": 2400,
    "widget_height": 300,
    "widget_y": 350,        # ← TV STATUS BAR UTÁN (300px + buffer)
    "widget_x": 220,        # Bal margin
    
    # TV-DIZÁJN SZÍNEK
    "colors": {
        "bg_primary": (8, 12, 22, 255),
        "glass_bg": (12, 18, 35, 180),
        "glass_border": (255, 255, 255, 40),
        "text_primary": (255, 255, 255, 255),
        "text_secondary": (210, 215, 225, 220),
        "text_accent": (100, 200, 255, 255),
        "divider": (255, 255, 255, 60),
    },
    
    # TV-BETŰMÉRETEK (3m távolságra optimalizálva)
    "fonts": {
        "temp": 110,
        "day": 36,
        "desc": 34,
        "value": 38,
        "forecast_day": 32,
        "forecast_temp": 36,
        "forecast_desc": 24,
        "nameday": 40,
        "update": 26,
        "sun": 30
    }
}

# ============================================================
# SEGÉDFÜGGVÉNYEK
# ============================================================

def find_font(bold=False):
    paths = [
        "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "./fonts/NotoSans-Bold.ttf" if bold else "./fonts/NotoSans-Regular.ttf",
    ]
    for path in paths:
        if os.path.exists(path):
            return path
    return None

def get_font(size, bold=False):
    font_path = find_font(bold)
    if font_path:
        try:
            return ImageFont.truetype(font_path, size)
        except:
            pass
    return ImageFont.load_default()

def load_icon(name, size=80):
    try:
        url = f"https://raw.githubusercontent.com/{CONFIG['github_user']}/{CONFIG['github_repo']}/{CONFIG['branch']}/images/ICONS_PNG80/{name}.png"
        response = requests.get(url, timeout=8)
        response.raise_for_status()
        icon = Image.open(BytesIO(response.content)).convert("RGBA")
        return icon.resize((size, size), Image.Resampling.LANCZOS)
    except:
        return None

def create_gradient_background(size):
    w, h = size
    img = Image.new("RGBA", size, CONFIG["colors"]["bg_primary"])
    draw = ImageDraw.Draw(img)
    
    for y in range(h):
        alpha = int(255 * (1 - y / h * 0.3))
        color = (
            min(30, CONFIG["colors"]["bg_primary"][0] + y // 20),
            min(50, CONFIG["colors"]["bg_primary"][1] + y // 30),
            min(80, CONFIG["colors"]["bg_primary"][2] + y // 15),
            alpha
        )
        draw.line([(0, y), (w, y)], fill=color)
    return img

def draw_rounded_rect(draw, bounds, radius=30, fill=None, outline=None, width=1):
    x1, y1, x2, y2 = bounds
    if fill:
        draw.rounded_rectangle([x1, y1, x2, y2], radius=radius, fill=fill)
    if outline:
        draw.rounded_rectangle([x1+width//2, y1+width//2, x2-width//2, y2-width//2], 
                             radius=radius-width//2, outline=outline, width=width)

def draw_glass_effect(img, x, y, width, height, blur=25):
    region = img.crop((x, y, x + width, y + height)).convert("RGBA")
    blurred = region.filter(ImageFilter.GaussianBlur(blur))
    
    mask = Image.new("L", (width, height), 0)
    draw_mask = ImageDraw.Draw(mask)
    draw_mask.rounded_rectangle([0, 0, width, height], radius=28, fill=220)
    
    overlay = Image.new("RGBA", (width, height), CONFIG["colors"]["glass_bg"])
    blurred.putalpha(mask)
    glass_effect = Image.alpha_composite(blurred, overlay)
    
    img.paste(glass_effect, (x, y), glass_effect)
    
    draw = ImageDraw.Draw(img)
    draw_rounded_rect(draw, (x, y, x + width, y + height), 
                     radius=28, outline=CONFIG["colors"]["glass_border"], width=2)
    return img

def get_hungarian_weather(weather_id):
    weather_map = {
        800: "TISZTÁN",
        801: "FÉLFELHŐS", 
        802: "FELHŐS",
        803: "ERŐSEN FELHŐS",
        804: "BORULT",
    }
    if 500 <= weather_id < 600: return "ESŐS"
    if 600 <= weather_id < 700: return "HAVAS"
    if 200 <= weather_id < 300: return "ZIVATAR"
    if 700 <= weather_id < 800: return "KÖDÖS"
    return "VÁLTOZÓ"

def load_namedays():
    namedays = {}
    ics_path = "Data/Magyarnevnapok.ics"
    
    if not os.path.exists(ics_path):
        return namedays
    
    try:
        with open(ics_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        lines = content.split("\\n")
        current_date = None
        
        for line in lines:
            line = line.strip()
            if line.startswith("DTSTART;") and ":" in line:
                date_part = line.split(":")[1]
                if len(date_part) >= 8:
                    month, day = date_part[4:6], date_part[6:8]
                    current_date = f"{month}-{day}"
            
            elif line.startswith("SUMMARY") and current_date:
                summary = line.split(":", 1)[1] if ":" in line else ""
                if summary and summary not in ["Névnap", ""]:
                    summary = summary.replace("\\\\", ",")
                    namedays[current_date] = summary
                    current_date = None
    except:
        pass
    return namedays

# ============================================================
# FŐ PROGRAM - TV READY
# ============================================================

def main():
    print("🎥 TV IDŐJÁRÁS WIDGET GENERÁLÁS...")
    
    namedays = load_namedays()
    
    try:
        current = requests.get(
            f"https://api.openweathermap.org/data/2.5/weather?q={CONFIG['city']}&appid={CONFIG['api_key']}&units=metric",
            timeout=10
        ).json()
        forecast = requests.get(
            f"https://api.openweathermap.org/data/2.5/forecast?q={CONFIG['city']}&appid={CONFIG['api_key']}&units=metric",
            timeout=10
        ).json()
    except Exception as e:
        print(f"❌ API hiba: {e}")
        return
    
    # Adatok
    temp = round(current["main"]["temp"])
    humidity = current["main"]["humidity"]
    wind_kmh = round(current["wind"]["speed"] * 3.6)
    weather_id = current["weather"][0]["id"]
    tz_offset = current.get("timezone", 3600)
    
    tz = timezone(timedelta(seconds=tz_offset))
    sunrise = datetime.fromtimestamp(current["sys"]["sunrise"], tz)
    sunset = datetime.fromtimestamp(current["sys"]["sunset"], tz)
    now = datetime.now(tz)
    
    # Kép generálás
    img = create_gradient_background(CONFIG["canvas_size"])
    
    # TV-SAFE GLASS WIDGET
    wx, wy = CONFIG["widget_x"], CONFIG["widget_y"]
    ww, wh = CONFIG["widget_width"], CONFIG["widget_height"]
    img = draw_glass_effect(img, wx, wy, ww, wh)
    draw = ImageDraw.Draw(img)
    
    colors = CONFIG["colors"]
    fonts = {k: get_font(v) for k, v in CONFIG["fonts"].items()}
    
    current_x = wx + 80
    
    # 1. JELENLEGI IDŐJÁRÁS
    print("  ✅ Jelenlegi...")
    days = ["HÉTFŐ", "KEDD", "SZERDA", "CSÜTÖRTÖK", "PÉNTEK", "SZOMBAT", "VASÁRNAP"]
    day_name = days[now.weekday()]
    
    draw.text((current_x, wy + 35), "MA", font=fonts["day"], fill=colors["text_secondary"])
    temp_text = f"{temp}°"
    temp_w = draw.textbbox((0, 0), temp_text, font=fonts["temp"])[2]
    draw.text((current_x, wy + 65), temp_text, font=fonts["temp"], fill=colors["text_primary"])
    
    desc_text = get_hungarian_weather(weather_id)
    draw.text((current_x, wy + 195), desc_text, font=fonts["desc"], fill=colors["text_secondary"])
    
    icon_name = "day_clear" if weather_id == 800 else "day_cloudy" if 801 <= weather_id <= 804 else "day_rain"
    icon = load_icon(icon_name, 100)
    if icon:
        img.paste(icon, (current_x + temp_w + 30, wy + 75), icon)
    
    current_x += max(temp_w + 200, 420)
    
    # 2. NAPKELTE/NAPNYUGTA
    print("  ✅ Napadatok...")
    sun_section_w = 480
    sun_x = current_x + (sun_section_w - 380) // 2
    
    sr_icon = load_icon("day_clear", 32)
    if sr_icon: img.paste(sr_icon, (sun_x, wy + 70), sr_icon)
    draw.text((sun_x + 42, wy + 72), sunrise.strftime("%H:%M"), font=fonts["sun"], fill=colors["text_primary"])
    draw.text((sun_x + 140, wy + 78), "•", font=fonts["sun"], fill=colors["text_secondary"])
    
    ss_icon = load_icon("night_clear", 32)
    if ss_icon: img.paste(ss_icon, (sun_x + 180, wy + 70), ss_icon)
    draw.text((sun_x + 222, wy + 72), sunset.strftime("%H:%M"), font=fonts["sun"], fill=colors["text_primary"])
    
    # Szél + Pára
    row_y = wy + 160
    wind_icon = load_icon("tornado", 28)
    hum_icon = load_icon("para", 28)
    
    wind_x = sun_x + 20
    if wind_icon: img.paste(wind_icon, (wind_x, row_y + 2), wind_icon)
    draw.text((wind_x + 36, row_y), f"{wind_kmh} km/h", font=fonts["value"], fill=colors["text_secondary"])
    
    if hum_icon: img.paste(hum_icon, (wind_x + 160, row_y + 2), hum_icon)
    draw.text((wind_x + 196, row_y), f"{humidity}%", font=fonts["value"], fill=colors["text_secondary"])
    
    current_x += sun_section_w + 40
    
    # 3. ELŐREJELZÉS
    print("  ✅ Előrejelzés...")
    fc_width = 520
    fc_col_width = fc_width // 4
    fc_x = current_x
    
    short_days = ["HÉ", "KE", "SZE", "CSÜ", "PÉ", "SZO", "VA"]
    fc_items = []
    today_date = now.date()
    
    for item in forecast['list']:
        dt = datetime.fromtimestamp(item['dt'], tz)
        if dt.date() > today_date and len(fc_items) < 4:
            fc_items.append((dt, item))
    
    for i, (dt, item) in enumerate(fc_items):
        col_x = fc_x + i * fc_col_width + fc_col_width // 2
        
        draw.text((col_x - 20, wy + 40), short_days[dt.weekday()], 
                 font=fonts["forecast_day"], fill=colors["text_primary"])
        
        f_icon_name = "day_clear" if item['weather'][0]['id'] == 800 else "day_cloudy"
        f_icon = load_icon(f_icon_name, 52)
        if f_icon: img.paste(f_icon, (col_x - 26, wy + 75), f_icon)
        
        f_temp = f"{round(item['main']['temp'])}°"
        f_temp_w = draw.textbbox((0, 0), f_temp, font=fonts["forecast_temp"])[2]
        draw.text((col_x - f_temp_w//2, wy + 160), f_temp, 
                 font=fonts["forecast_temp"], fill=colors["text_primary"])
        
        f_desc = get_hungarian_weather(item['weather'][0]['id'])
        f_desc_w = draw.textbbox((0, 0), f_desc, font=fonts["forecast_desc"])[2]
        draw.text((col_x - f_desc_w//2, wy + 200), f_desc, 
                 font=fonts["forecast_desc"], fill=colors["text_secondary"])
    
    current_x += fc_width + 60
    
    # 4. NÉVNAP + FRISSÍTVE
    print("  ✅ Névnap...")
    nameday_section_w = 480
    nd_x = current_x + (nameday_section_w - 300) // 2
    
    today_str = now.strftime("%m-%d")
    nameday_text = namedays.get(today_str, "")
    update_text = now.strftime("Frissítve: %H:%M")
    
    if nameday_text:
        nd_font = fonts["nameday"]
        nd_w = draw.textbbox((0, 0), nameday_text, font=nd_font)[2]
        if nd_w > nameday_section_w - 60:
            nd_font = get_font(32)
        draw.text((nd_x + 20, wy + 80), nameday_text, font=nd_font, fill=colors["text_accent"])
        
        upd_w = draw.textbbox((0, 0), update_text, font=fonts["update"])[2]
        draw.text((nd_x + (nameday_section_w - upd_w) // 2, wy + 190), 
                 update_text, font=fonts["update"], fill=colors["text_secondary"])
    else:
        upd_w = draw.textbbox((0, 0), update_text, font=fonts["update"])[2]
        draw.text((nd_x + (nameday_section_w - upd_w) // 2, wy + 130), 
                 update_text, font=fonts["update"], fill=colors["text_secondary"])
    
    # MENTÉS
    print("  💾 Mentés...")
    os.makedirs("images", exist_ok=True)
    img.convert("RGB").save("images/current.jpg", "JPEG", quality=97, optimize=True)
    
    timestamp = int(time.time())
    image_url = f"https://raw.githubusercontent.com/{CONFIG['github_user']}/{CONFIG['github_repo']}/{CONFIG['branch']}/images/current.jpg?v={timestamp}"
    
    weather_data = [{
        "location": CONFIG["city"],
        "title": f"{get_hungarian_weather(weather_id)} {temp}°C",
        "image_url": image_url,
        "url_img": image_url,
        "timestamp": timestamp
    }]
    
    with open("weather.json", "w", encoding="utf-8") as f:
        json.dump(weather_data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ KÉSZ! images/current.jpg + weather.json ({now.strftime('%H:%M')})")
    print(f"📺 TV-SAFE: y={CONFIG['widget_y']}px")

if __name__ == "__main__":
    main()
