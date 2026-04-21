#!/usr/bin/env python3
import requests
import json
import os
import time
from io import BytesIO
from datetime import datetime, timezone, timedelta
from PIL import Image, ImageDraw, ImageFont, ImageFilter

API_KEY = os.environ.get("OWM_API_KEY")
GITHUB_USER = "harsanyiz"
GITHUB_REPO = "weather-wallpaper"
BRANCH = "main"
BASE_URL = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/{BRANCH}"

# ============================================================
# KONFIGURÁCIÓ - FENTRE, TV LAUNCHER IKONOK MELLETT
# ============================================================
CITY = "Budapest"

# Képernyő méret (4K TV)
SCREEN_W = 3840
SCREEN_H = 2160

# Widget pozíció - FENT, jobbra tolva (bal oldalon lehetnek launcher ikonok)
WIDGET_WIDTH = 3000
WIDGET_HEIGHT = 260
WIDGET_X = (SCREEN_W - WIDGET_WIDTH) // 2  # Középre, de lehet jobbra is: SCREEN_W - WIDGET_WIDTH - 50
WIDGET_Y = 40  # Fent, kis margóval

# Belső margók
INNER_PADDING = 45
SECTION_GAP = 35

# Ikon méretek
MAIN_ICON_SIZE = 90
FC_ICON_SIZE = 52
SUN_ICON_SIZE = 30
AUX_ICON_SIZE = 26

# Betűméretek (jól olvasható távolról)
FONT_MAIN_TEMP = 82
FONT_MAIN_DESC = 30
FONT_SECTION_TITLE = 26
FONT_VALUE = 34
FONT_LABEL = 24
FONT_SUN = 28
FONT_FC_DAY = 28
FONT_FC_TEMP = 32
FONT_FC_DESC = 22
FONT_NAMEDAY = 30
FONT_UPDATE = 20

# ============================================================

BG_MAP = {
    "sunny_day":         "images/sunny_day.jpg",
    "sunny_night":       "images/sunny_night.jpg",
    "cloudy_day":        "images/cloudy_day.jpg",
    "cloudy_night":      "images/cloudy_night.jpg",
    "rainy_day":         "images/rainy_day.jpg",
    "rainy_night":       "images/rainy_night.jpg",
    "snow_day":          "images/snow_day.jpg",
    "snow_night":        "images/snow_night.jpg",
    "foggy_day":         "images/foggy_day.jpg",
    "foggy_night":       "images/foggy_night.jpg",
    "sleet_day":         "images/sleet_day.jpg",
    "sleet_night":       "images/sleet_night.jpg",
    "hail_day":          "images/hail_day.jpg",
    "hail_night":        "images/hail_night.jpg",
}

def get_bg_key(weather_id, is_night):
    suffix = "night" if is_night else "day"
    if weather_id == 800:
        return f"sunny_{suffix}"
    if weather_id in [801, 802, 803, 804]:
        return f"cloudy_{suffix}"
    if weather_id in range(500, 511):
        return f"rainy_{suffix}"
    if weather_id == 511:
        return f"sleet_{suffix}"
    if weather_id in range(512, 599):
        return f"rainy_{suffix}"
    if weather_id in range(600, 699):
        return f"snow_{suffix}"
    if weather_id in range(700, 799):
        return f"foggy_{suffix}"
    if weather_id in range(200, 299):
        return f"rainy_{suffix}"
    return f"cloudy_{suffix}"

def load_bg(weather_id, is_night):
    key = get_bg_key(weather_id, is_night)
    path = BG_MAP.get(key)
    if path and os.path.exists(path):
        img = Image.open(path).convert("RGBA")
        if img.size != (SCREEN_W, SCREEN_H):
            img = img.resize((SCREEN_W, SCREEN_H), Image.Resampling.LANCZOS)
        return img
    # Default dark gradient
    img = Image.new("RGBA", (SCREEN_W, SCREEN_H), (10, 10, 20, 255))
    draw = ImageDraw.Draw(img)
    for i in range(SCREEN_H):
        alpha = int(20 * (1 - i/SCREEN_H))
        draw.line([(0, i), (SCREEN_W, i)], fill=(20, 20, 40, alpha))
    return img

def find_font(bold=False):
    paths = [
        "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for p in paths:
        if os.path.exists(p):
            return p
    return None

def get_f(size, bold=False):
    path = find_font(bold)
    if path:
        return ImageFont.truetype(path, size)
    return ImageFont.load_default()

def get_icon_name(weather_id, is_night):
    suffix = "night" if is_night else "day"
    if weather_id == 800: return f"{suffix}_clear"
    if weather_id == 801: return f"{suffix}_partial_cloud"
    if weather_id in [802, 803]: return "cloudy"
    if weather_id == 804: return "overcast"
    if weather_id == 511: return f"{suffix}_sleet"
    if weather_id in range(500, 599): return f"{suffix}_rain"
    if weather_id in range(600, 699): return f"{suffix}_snow"
    if weather_id in range(200, 299): return f"{suffix}_rain_thunder"
    if weather_id in range(700, 799): return "cloudy"
    return "cloudy"

def get_weather_hu(weather_id):
    if weather_id == 800: return "DERÜLT"
    if weather_id == 801: return "PÁRFELHŐS"
    if weather_id == 802: return "FELHŐS"
    if weather_id == 803: return "ERŐSEN FELHŐS"
    if weather_id == 804: return "BORULT"
    if weather_id == 511: return "ÓNOS ESŐ"
    if weather_id in range(500, 599): return "ESŐ"
    if weather_id in range(600, 699): return "HÓ"
    if weather_id in range(700, 799): return "KÖD"
    if weather_id in range(200, 299): return "ZIVATAR"
    return "VÁLTOZÓ"

def get_forecast_hu(weather_id):
    if weather_id == 800: return "NAP"
    if weather_id in [801, 802]: return "FELHŐS"
    if weather_id == 803: return "FELHŐS"
    if weather_id == 804: return "BORULT"
    if weather_id in range(500, 599): return "ESŐ"
    if weather_id in range(600, 699): return "HÓ"
    if weather_id in range(200, 299): return "ZIVATAR"
    return "BORULT"

def load_icon(name, size=None):
    target = size or MAIN_ICON_SIZE
    url = f"{BASE_URL}/images/ICONS_PNG80/{name}.png"
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        icon = Image.open(BytesIO(r.content)).convert("RGBA")
        return icon.resize((target, target), Image.Resampling.LANCZOS)
    except Exception as e:
        print(f"  [icon] Nem sikerült betölteni: {name}")
        return None

def draw_glass_bar_top(img, bx, by, bw, bh):
    """Elegáns glassmorphism widget - felülre optimalizálva"""
    # Kivágás a háttérből
    region = img.crop((bx, by, bx + bw, by + bh)).convert("RGBA")
    
    # Blur
    blurred = region.filter(ImageFilter.GaussianBlur(40))
    
    # Átlátszósági maszk
    mask = Image.new("L", (bw, bh), 0)
    draw_mask = ImageDraw.Draw(mask)
    draw_mask.rounded_rectangle((0, 0, bw - 1, bh - 1), radius=35, fill=190)
    
    # Sötét overlay - kicsit világosabb, mert fent van
    overlay = Image.new("RGBA", (bw, bh), (0, 0, 0, 45))
    
    blurred.putalpha(mask)
    result = Image.alpha_composite(blurred, overlay)
    
    # Vékony keret
    draw = ImageDraw.Draw(result)
    draw.rounded_rectangle(
        (1, 1, bw - 2, bh - 2),
        radius=33,
        outline=(255, 255, 255, 40),
        width=1
    )
    
    img.paste(result, (bx, by), result)
    return img

def draw_divider(draw, x, y_top, y_bot):
    """Vékony elválasztó vonal"""
    draw.line([(x, y_top + 15), (x, y_bot - 15)], fill=(255, 255, 255, 30), width=1)

def load_namedays():
    namedays = {}
    ics_path = "Data/Magyarnevnapok.ics"
    
    if not os.path.exists(ics_path):
        return namedays
    
    try:
        with open(ics_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        lines = content.split("\n")
        current_date = None
        
        for line in lines:
            line = line.strip()
            if line.startswith("DTSTART"):
                if ":" in line:
                    date_part = line.split(":")[1]
                    if len(date_part) >= 8:
                        month = date_part[4:6]
                        day = date_part[6:8]
                        current_date = f"{month}-{day}"
            elif line.startswith("SUMMARY") and current_date:
                summary = line.split(":", 1)[1] if ":" in line else ""
                if summary and summary not in ["Névnap", ""]:
                    summary = summary.replace("ű", "u").replace("ő", "o").replace("ú", "u")
                    summary = summary.replace("ó", "o").replace("ö", "o").replace("ü", "u")
                    summary = summary.replace("á", "a").replace("é", "e").replace("í", "i")
                    namedays[current_date] = summary
                    current_date = None
    except Exception as e:
        print(f"[WARN] Névnap betöltési hiba: {e}")
    
    return namedays

def main():
    try:
        NAMEDAYS = load_namedays()
        
        # API lekérdezések
        resp = requests.get(
            f"https://api.openweathermap.org/data/2.5/weather"
            f"?q={CITY}&appid={API_KEY}&units=metric"
        ).json()
        f_resp = requests.get(
            f"https://api.openweathermap.org/data/2.5/forecast"
            f"?q={CITY}&appid={API_KEY}&units=metric"
        ).json()

        temp = round(resp["main"]["temp"])
        feels = round(resp["main"]["feels_like"])
        humidity = resp["main"]["humidity"]
        wind = round(resp["wind"]["speed"] * 3.6)
        weather_id = resp["weather"][0]["id"]
        tz_offset = resp.get("timezone", 3600)

        now_ts = time.time()
        is_night = now_ts < resp["sys"]["sunrise"] or now_ts > resp["sys"]["sunset"]

        today_icon_name = get_icon_name(weather_id, is_night)
        weather_hu = get_weather_hu(weather_id)

        tz = timezone(timedelta(seconds=tz_offset))
        sunrise_str = datetime.fromtimestamp(resp["sys"]["sunrise"], tz=tz).strftime("%H:%M")
        sunset_str = datetime.fromtimestamp(resp["sys"]["sunset"], tz=tz).strftime("%H:%M")
        local_now = datetime.now(tz)

        today_str = local_now.strftime("%m-%d")
        nameday_text = NAMEDAYS.get(today_str, "")
        if nameday_text:
            nameday_text = nameday_text.replace("\\", ",")
            nameday_list = [n.strip() for n in nameday_text.split(",") if n.strip()]
            nameday_one_line = " · ".join(nameday_list[:3])
        else:
            nameday_one_line = ""

        # Háttér betöltése
        img = load_bg(weather_id, is_night)
        img = draw_glass_bar_top(img, WIDGET_X, WIDGET_Y, WIDGET_WIDTH, WIDGET_HEIGHT)

        draw = ImageDraw.Draw(img)
        
        # Színek
        c_main = (255, 255, 255, 255)
        c_soft = (255, 255, 255, 220)
        c_muted = (200, 205, 215, 180)
        c_subtle = (255, 255, 255, 90)

        # Fontok
        f_temp = get_f(FONT_MAIN_TEMP, bold=True)
        f_desc = get_f(FONT_MAIN_DESC)
        f_title = get_f(FONT_SECTION_TITLE)
        f_sun = get_f(FONT_SUN)
        f_fc_day = get_f(FONT_FC_DAY, bold=True)
        f_fc_temp = get_f(FONT_FC_TEMP, bold=True)
        f_fc_desc = get_f(FONT_FC_DESC)
        f_nameday = get_f(FONT_NAMEDAY)
        f_update = get_f(FONT_UPDATE)

        # Widget belső koordináták
        y_center = WIDGET_Y + WIDGET_HEIGHT // 2
        y_top = WIDGET_Y + INNER_PADDING
        y_bottom = WIDGET_Y + WIDGET_HEIGHT - INNER_PADDING
        
        current_x = WIDGET_X + INNER_PADDING

        # ======================= 1. BAL SZEKCIÓ - MAI IDŐJÁRÁS =======================
        # "MA" címke
        draw.text((current_x, y_top + 5), "MA", font=f_title, fill=c_muted)
        
        # Hőmérséklet
        temp_text = f"{temp}°"
        temp_bbox = draw.textbbox((0, 0), temp_text, font=f_temp)
        temp_width = temp_bbox[2] - temp_bbox[0]
        draw.text((current_x, y_center - 42), temp_text, font=f_temp, fill=c_main)
        
        # Időjárás leírás
        draw.text((current_x, y_center + 22), weather_hu, font=f_desc, fill=c_soft)
        
        # Hőérzet
        feels_text = f"{feels}°"
        desc_width = draw.textbbox((0, 0), weather_hu, font=f_desc)[2]
        feels_x = current_x + desc_width + 20
        
        draw.text((feels_x, y_center + 22), f"⬤ {feels_text}", font=f_desc, fill=c_muted)
        
        # Fő ikon
        main_icon = load_icon(today_icon_name, size=MAIN_ICON_SIZE)
        if main_icon:
            icon_x = current_x + temp_width + 25
            icon_y = y_center - 48
            img.paste(main_icon, (icon_x, icon_y), main_icon)
        
        # Bal szekció szélessége
        left_section_width = temp_width + 140
        current_x += left_section_width + SECTION_GAP
        
        # Elválasztó
        draw_divider(draw, current_x - SECTION_GAP//2, y_top, y_bottom)

        # ======================= 2. KÖZÉPSŐ SZEKCIÓ - RÉSZLETEK =======================
        mid_width = 460
        mid_x = current_x + (mid_width // 2)
        
        # Napkelte / Napnyugta
        sun_y = y_center - 20
        
        draw.text((mid_x - 130, sun_y + 5), "🌅", font=f_sun, fill=c_soft)
        draw.text((mid_x - 100, sun_y + 5), sunrise_str, font=f_sun, fill=c_soft)
        
        draw.text((mid_x - 25, sun_y + 5), "•", font=f_sun, fill=c_subtle)
        
        draw.text((mid_x + 5, sun_y + 5), "🌇", font=f_sun, fill=c_soft)
        draw.text((mid_x + 35, sun_y + 5), sunset_str, font=f_sun, fill=c_soft)
        
        # Szél és páratartalom
        info_y = y_center + 35
        
        draw.text((mid_x - 130, info_y + 3), "💨", font=f_sun, fill=c_muted)
        draw.text((mid_x - 100, info_y + 5), f"{wind} km/h", font=f_title, fill=c_muted)
        
        draw.text((mid_x + 5, info_y + 3), "💧", font=f_sun, fill=c_muted)
        draw.text((mid_x + 35, info_y + 5), f"{humidity}%", font=f_title, fill=c_muted)
        
        current_x += mid_width + SECTION_GAP
        draw_divider(draw, current_x - SECTION_GAP//2, y_top, y_bottom)

        # ======================= 3. ELŐREJELZÉS SZEKCIÓ =======================
        napok_rovid = ["H", "K", "SZE", "CS", "P", "SZO", "V"]
        
        seen_days = set()
        today_date = datetime.now().date()
        
        fc_entries = []
        for entry in f_resp['list']:
            dt = datetime.fromtimestamp(entry['dt'], tz=tz)
            if dt.date() > today_date and dt.date() not in seen_days:
                if 12 <= dt.hour <= 15:
                    fc_entries.append((dt, entry))
                    seen_days.add(dt.date())
            if len(fc_entries) == 4:
                break
        
        fc_col_width = 130
        for idx, (dt, entry) in enumerate(fc_entries[:4]):
            col_x = current_x + (idx * fc_col_width)
            col_center = col_x + fc_col_width // 2
            
            # Nap neve
            day_name = napok_rovid[dt.weekday()]
            day_bbox = draw.textbbox((0, 0), day_name, font=f_fc_day)
            draw.text((col_center - (day_bbox[2] - day_bbox[0]) // 2, y_top + 8), 
                     day_name, font=f_fc_day, fill=c_soft)
            
            # Ikon
            f_id = entry['weather'][0]['id']
            f_icon = load_icon(get_icon_name(f_id, False), size=FC_ICON_SIZE)
            if f_icon:
                icon_x = col_center - FC_ICON_SIZE // 2
                icon_y = y_center - FC_ICON_SIZE // 2
                img.paste(f_icon, (icon_x, icon_y), f_icon)
            
            # Hőmérséklet
            f_temp_val = round(entry['main']['temp'])
            f_temp_text = f"{f_temp_val}°"
            temp_bbox = draw.textbbox((0, 0), f_temp_text, font=f_fc_temp)
            draw.text((col_center - (temp_bbox[2] - temp_bbox[0]) // 2, y_bottom - 60),
                     f_temp_text, font=f_fc_temp, fill=c_main)
            
            # Leírás
            f_desc_text = get_forecast_hu(f_id)
            desc_bbox = draw.textbbox((0, 0), f_desc_text, font=f_fc_desc)
            draw.text((col_center - (desc_bbox[2] - desc_bbox[0]) // 2, y_bottom - 32),
                     f_desc_text, font=f_fc_desc, fill=c_muted)
        
        current_x += 4 * fc_col_width + SECTION_GAP
        draw_divider(draw, current_x - SECTION_GAP//2, y_top, y_bottom)

        # ======================= 4. JOBB SZEKCIÓ - NÉVNAP + FRISSÍTVE =======================
        right_width = WIDGET_X + WIDGET_WIDTH - INNER_PADDING - current_x
        right_center = current_x + right_width // 2
        
        if nameday_one_line:
            # Névnapok
            nameday_bbox = draw.textbbox((0, 0), nameday_one_line, font=f_nameday)
            nameday_width = nameday_bbox[2] - nameday_bbox[0]
            
            if nameday_width > right_width - 40:
                smaller_font = get_f(FONT_NAMEDAY - 6)
                nameday_bbox = draw.textbbox((0, 0), nameday_one_line, font=smaller_font)
                draw.text((right_center - (nameday_bbox[2] - nameday_bbox[0]) // 2, y_center - 20),
                         nameday_one_line, font=smaller_font, fill=c_main)
            else:
                draw.text((right_center - nameday_width // 2, y_center - 20),
                         nameday_one_line, font=f_nameday, fill=c_main)
            
            # Névnap felirat
            draw.text((right_center - 30, y_center - 55), "NÉVNAP", font=f_title, fill=c_subtle)
        else:
            # Dátum
            date_text = local_now.strftime("%Y. %B %d.")
            date_bbox = draw.textbbox((0, 0), date_text, font=f_nameday)
            draw.text((right_center - (date_bbox[2] - date_bbox[0]) // 2, y_center - 15),
                     date_text, font=f_nameday, fill=c_soft)
        
        # Frissítve
        update_text = f"Frissítve: {local_now.strftime('%H:%M')}"
        update_bbox = draw.textbbox((0, 0), update_text, font=f_update)
        draw.text((right_center - (update_bbox[2] - update_bbox[0]) // 2, y_bottom - 25),
                 update_text, font=f_update, fill=c_subtle)

        # ======================= MENTÉS =======================
        os.makedirs("images", exist_ok=True)
        img.convert("RGB").save("images/current.jpg", "JPEG", quality=92)
        print(f"[OK] images/current.jpg elmentve ({local_now.strftime('%H:%M')})")
        
        v_param = int(time.time())
        image_url = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/{BRANCH}/images/current.jpg?v={v_param}"
        
        weather_json = [{
            "location": CITY,
            "title": f"{weather_hu} {temp}°C",
            "image_url": image_url,
            "url_img": image_url,
        }]
        
        with open("weather.json", "w", encoding="utf-8") as f:
            json.dump(weather_json, f, ensure_ascii=False, indent=2)
        print("[OK] weather.json frissítve")
        
    except Exception as e:
        import traceback
        print(f"[HIBA] {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()
