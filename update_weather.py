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
# KONFIGURÁCIÓ
# ============================================================
CITY = "Budapest"

SCREEN_W = 3840
SCREEN_H = 2160

# Widget - felül középen
WIDGET_WIDTH = 3200
WIDGET_HEIGHT = 280
WIDGET_X = (SCREEN_W - WIDGET_WIDTH) // 2
WIDGET_Y = 50

# Belső margók - NÖVELVE az összecsúszás elkerülésére
INNER_PADDING = 50
SECTION_GAP = 50

# Ikon méretek
MAIN_ICON_SIZE = 85
FC_ICON_SIZE = 55
AUX_ICON_SIZE = 28

# Betűméretek
FONT_MAIN_TEMP = 84
FONT_MAIN_DESC = 34
FONT_SECTION_TITLE = 28
FONT_SUN = 30
FONT_FC_DAY = 32
FONT_FC_TEMP = 36
FONT_FC_DESC = 26
FONT_NAMEDAY = 34
FONT_UPDATE = 24
FONT_VALUE = 32

# ============================================================

BG_MAP = {
    "sunny_day": "images/sunny_day.jpg",
    "sunny_night": "images/sunny_night.jpg",
    "cloudy_day": "images/cloudy_day.jpg",
    "cloudy_night": "images/cloudy_night.jpg",
    "rainy_day": "images/rainy_day.jpg",
    "rainy_night": "images/rainy_night.jpg",
    "snow_day": "images/snow_day.jpg",
    "snow_night": "images/snow_night.jpg",
    "foggy_day": "images/foggy_day.jpg",
    "foggy_night": "images/foggy_night.jpg",
    "sleet_day": "images/sleet_day.jpg",
    "sleet_night": "images/sleet_night.jpg",
    "hail_day": "images/hail_day.jpg",
    "hail_night": "images/hail_night.jpg",
}

def get_bg_key(weather_id, is_night):
    suffix = "night" if is_night else "day"
    if weather_id == 800:
        return f"sunny_{suffix}"
    if weather_id in [801, 802, 803, 804]:
        return f"cloudy_{suffix}"
    if weather_id in range(500, 599):
        return f"rainy_{suffix}"
    if weather_id == 511:
        return f"sleet_{suffix}"
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
    img = Image.new("RGBA", (SCREEN_W, SCREEN_H), (15, 15, 25, 255))
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
    if weather_id == 800:
        return f"{suffix}_clear"
    if weather_id == 801:
        return f"{suffix}_partial_cloud"
    if weather_id in [802, 803]:
        return "cloudy"
    if weather_id == 804:
        return "overcast"
    if weather_id == 511:
        return f"{suffix}_sleet"
    if weather_id in range(500, 599):
        return f"{suffix}_rain"
    if weather_id in range(600, 699):
        return f"{suffix}_snow"
    if weather_id in range(200, 299):
        return f"{suffix}_rain_thunder"
    if weather_id in range(700, 799):
        return "cloudy"
    return "cloudy"

def get_weather_hu(weather_id):
    if weather_id == 800:
        return "DERÜLT"
    if weather_id == 801:
        return "PÁRFELHŐS"
    if weather_id == 802:
        return "FELHŐS"
    if weather_id == 803:
        return "ERŐSEN FELHŐS"
    if weather_id == 804:
        return "BORULT"
    if weather_id == 511:
        return "ÓNOS ESŐ"
    if weather_id in range(500, 599):
        return "ESŐ"
    if weather_id in range(600, 699):
        return "HÓ"
    if weather_id in range(700, 799):
        return "KÖD"
    if weather_id in range(200, 299):
        return "ZIVATAR"
    return "VÁLTOZÓ"

def get_forecast_hu(weather_id):
    if weather_id == 800:
        return "NAP"
    if weather_id in [801, 802, 803]:
        return "FELHŐS"
    if weather_id == 804:
        return "BORULT"
    if weather_id in range(500, 599):
        return "ESŐ"
    if weather_id in range(600, 699):
        return "HÓ"
    if weather_id in range(200, 299):
        return "ZIVATAR"
    return "BORULT"

def load_icon(name, size=None):
    target = size or MAIN_ICON_SIZE
    url = f"{BASE_URL}/images/ICONS_PNG80/{name}.png"
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        icon = Image.open(BytesIO(r.content)).convert("RGBA")
        return icon.resize((target, target), Image.Resampling.LANCZOS)
    except:
        return None

def draw_glass_bar(img, bx, by, bw, bh):
    region = img.crop((bx, by, bx + bw, by + bh)).convert("RGBA")
    blurred = region.filter(ImageFilter.GaussianBlur(40))
    mask = Image.new("L", (bw, bh), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, bw - 1, bh - 1), radius=35, fill=190)
    overlay = Image.new("RGBA", (bw, bh), (0, 0, 0, 50))
    blurred.putalpha(mask)
    result = Image.alpha_composite(blurred, overlay)
    ImageDraw.Draw(result).rounded_rectangle((1, 1, bw - 2, bh - 2), radius=33, outline=(255, 255, 255, 35), width=1)
    img.paste(result, (bx, by), result)
    return img

def draw_divider(draw, x, y_top, y_bot):
    draw.line([(x, y_top + 20), (x, y_bot - 20)], fill=(255, 255, 255, 30), width=1)

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
    except:
        pass
    return namedays

def main():
    try:
        NAMEDAYS = load_namedays()
        
        resp = requests.get(f"https://api.openweathermap.org/data/2.5/weather?q={CITY}&appid={API_KEY}&units=metric").json()
        f_resp = requests.get(f"https://api.openweathermap.org/data/2.5/forecast?q={CITY}&appid={API_KEY}&units=metric").json()

        temp = round(resp["main"]["temp"])
        feels = round(resp["main"]["feels_like"])
        humidity = resp["main"]["humidity"]
        wind = round(resp["wind"]["speed"] * 3.6)
        weather_id = resp["weather"][0]["id"]
        tz_offset = resp.get("timezone", 3600)

        now_ts = time.time()
        is_night = now_ts < resp["sys"]["sunrise"] or now_ts > resp["sys"]["sunset"]

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

        img = load_bg(weather_id, is_night)
        img = draw_glass_bar(img, WIDGET_X, WIDGET_Y, WIDGET_WIDTH, WIDGET_HEIGHT)

        draw = ImageDraw.Draw(img)
        
        c_main = (255, 255, 255, 255)
        c_soft = (255, 255, 255, 220)
        c_muted = (200, 205, 215, 180)
        c_subtle = (255, 255, 255, 90)

        f_temp = get_f(FONT_MAIN_TEMP, bold=True)
        f_desc = get_f(FONT_MAIN_DESC)
        f_title = get_f(FONT_SECTION_TITLE)
        f_sun = get_f(FONT_SUN)
        f_fc_day = get_f(FONT_FC_DAY, bold=True)
        f_fc_temp = get_f(FONT_FC_TEMP, bold=True)
        f_fc_desc = get_f(FONT_FC_DESC)
        f_nameday = get_f(FONT_NAMEDAY)
        f_update = get_f(FONT_UPDATE)

        y_center = WIDGET_Y + WIDGET_HEIGHT // 2
        y_top = WIDGET_Y + INNER_PADDING
        y_bottom = WIDGET_Y + WIDGET_HEIGHT - INNER_PADDING
        
        current_x = WIDGET_X + INNER_PADDING

        # ======================= 1. BAL - MAI IDŐJÁRÁS =======================
        # "MA" címke
        draw.text((current_x, y_top), "MA", font=f_title, fill=c_muted)
        
        # Hőmérséklet - NAGYON
        temp_text = f"{temp}°"
        draw.text((current_x, y_center - 40), temp_text, font=f_temp, fill=c_main)
        
        # Időjárás leírás
        desc_text = get_weather_hu(weather_id)
        draw.text((current_x, y_center + 25), desc_text, font=f_desc, fill=c_soft)
        
        # Hőérzet külön sorban, kisebbel
        feels_text = f"⬤ {feels}°"
        draw.text((current_x, y_center + 55), feels_text, font=f_title, fill=c_muted)
        
        # Ikon
        main_icon = load_icon(get_icon_name(weather_id, is_night), size=MAIN_ICON_SIZE)
        if main_icon:
            temp_width = draw.textbbox((0, 0), temp_text, font=f_temp)[2]
            icon_x = current_x + temp_width + 25
            icon_y = y_center - 48
            img.paste(main_icon, (icon_x, icon_y), main_icon)
        
        current_x += 260 + SECTION_GAP
        draw_divider(draw, current_x - SECTION_GAP//2, y_top, y_bottom)

        # ======================= 2. KÖZÉP - NAP/SZÉL/PÁRA =======================
        mid_width = 460
        mid_x = current_x + (mid_width // 2)
        
        # Napkelte sor
        draw.text((mid_x - 130, y_center - 20), "🌅", font=f_sun, fill=c_soft)
        draw.text((mid_x - 100, y_center - 20), sunrise_str, font=f_sun, fill=c_soft)
        
        draw.text((mid_x - 25, y_center - 20), "•", font=f_sun, fill=c_subtle)
        
        draw.text((mid_x + 5, y_center - 20), "🌇", font=f_sun, fill=c_soft)
        draw.text((mid_x + 35, y_center - 20), sunset_str, font=f_sun, fill=c_soft)
        
        # Szél sor
        draw.text((mid_x - 130, y_center + 15), "💨", font=f_sun, fill=c_muted)
        draw.text((mid_x - 100, y_center + 15), f"{wind} km/h", font=f_title, fill=c_muted)
        
        # Pára sor
        draw.text((mid_x - 130, y_center + 50), "💧", font=f_sun, fill=c_muted)
        draw.text((mid_x - 100, y_center + 50), f"{humidity}%", font=f_title, fill=c_muted)
        
        current_x += mid_width + SECTION_GAP
        draw_divider(draw, current_x - SECTION_GAP//2, y_top, y_bottom)

        # ======================= 3. ELŐREJELZÉS =======================
        napok_rovid = ["H", "K", "SZ", "CS", "P", "SZ", "V"]
        
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
        
        fc_col_width = 145
        for idx, (dt, entry) in enumerate(fc_entries[:4]):
            col_x = current_x + (idx * fc_col_width)
            col_center = col_x + fc_col_width // 2
            
            # Nap neve
            day_name = napok_rovid[dt.weekday()]
            draw.text((col_center, y_top + 5), day_name, font=f_fc_day, fill=c_soft, anchor="mm")
            
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
            draw.text((col_center, y_bottom - 60), f_temp_text, font=f_fc_temp, fill=c_main, anchor="mm")
            
            # Időjárás
            f_desc_text = get_forecast_hu(f_id)
            draw.text((col_center, y_bottom - 30), f_desc_text, font=f_fc_desc, fill=c_muted, anchor="mm")
        
        current_x += 4 * fc_col_width + SECTION_GAP
        draw_divider(draw, current_x - SECTION_GAP//2, y_top, y_bottom)

        # ======================= 4. JOBB - NÉVNAP =======================
        right_width = WIDGET_X + WIDGET_WIDTH - INNER_PADDING - current_x
        right_center = current_x + right_width // 2
        
        if nameday_one_line:
            # "NÉVNAP" felirat
            draw.text((right_center, y_center - 50), "NÉVNAP", font=f_title, fill=c_subtle, anchor="mm")
            
            # Névnapok listája
            nameday_bbox = draw.textbbox((0, 0), nameday_one_line, font=f_nameday)
            nameday_width = nameday_bbox[2] - nameday_bbox[0]
            
            if nameday_width > right_width - 40:
                smaller_font = get_f(FONT_NAMEDAY - 8)
                draw.text((right_center, y_center - 5), nameday_one_line, font=smaller_font, fill=c_main, anchor="mm")
            else:
                draw.text((right_center, y_center - 5), nameday_one_line, font=f_nameday, fill=c_main, anchor="mm")
        else:
            # Dátum
            date_text = local_now.strftime("%Y. %B %d.")
            draw.text((right_center, y_center - 10), date_text, font=f_nameday, fill=c_soft, anchor="mm")
        
        # Frissítve
        update_text = f"Frissítve: {local_now.strftime('%H:%M')}"
        draw.text((right_center, y_bottom - 20), update_text, font=f_update, fill=c_subtle, anchor="mm")

        # ======================= MENTÉS =======================
        os.makedirs("images", exist_ok=True)
        img.convert("RGB").save("images/current.jpg", "JPEG", quality=92)
        print(f"[OK] images/current.jpg ({local_now.strftime('%H:%M')})")
        
        v_param = int(time.time())
        image_url = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/{BRANCH}/images/current.jpg?v={v_param}"
        
        weather_json = [{
            "location": CITY,
            "title": f"{get_weather_hu(weather_id)} {temp}°C",
            "image_url": image_url,
            "url_img": image_url,
        }]
        
        with open("weather.json", "w", encoding="utf-8") as f:
            json.dump(weather_json, f, ensure_ascii=False, indent=2)
        print("[OK] weather.json")
        
    except Exception as e:
        import traceback
        print(f"[HIBA] {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()
