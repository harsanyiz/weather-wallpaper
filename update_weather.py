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
# KONFIGURÁCIÓ - BALRA IGAZÍTVA
# ============================================================
CITY = "Budapest"

# Képernyő méret
SCREEN_W = 3840
SCREEN_H = 2160

# Widget - BALRA IGAZÍTVA, KISEBB SZÉLESSÉG
WIDGET_WIDTH = 2600          # Változtatva: 3400 -> 2600
WIDGET_HEIGHT = 280          # Kicsit magasabb
WIDGET_X = 80                # Változtatva: középről balra
WIDGET_Y = 60

# Belső margók - NAGYOBB az összecsúszás ellen
INNER_MARGIN = 60

# Ikon méretek
ICON_SIZE = 80
FC_ICON_SIZE = 52
SUN_ICON_SIZE = 32
WIND_ICON_SIZE = 28
HUM_ICON_SIZE = 28

# Betűméretek
FONT_TEMP = 92
FONT_DESC = 32
FONT_LABEL = 26
FONT_VALUE = 36
FONT_SUN = 30
FONT_FC_DAY = 32
FONT_FC_TMP = 36
FONT_FC_DSC = 26
FONT_NAMEDAY = 36
FONT_UPDATE = 24

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
    return Image.new("RGBA", (SCREEN_W, SCREEN_H), (5, 5, 15, 255))

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
        return "PÁR FELHŐ"
    if weather_id == 802:
        return "FELHŐS"
    if weather_id == 803:
        return "ERŐSEN FELHŐS"
    if weather_id == 804:
        return "BORULT"
    if weather_id == 511:
        return "ÓNOS ESŐ"
    if weather_id in range(500, 599):
        return "ESŐS"
    if weather_id in range(600, 699):
        return "HAVAS"
    if weather_id in range(700, 799):
        return "KÖDÖS"
    if weather_id in range(200, 299):
        return "ZIVATAROS"
    return "VÁLTOZÉKONY"

def get_forecast_hu(weather_id):
    if weather_id == 800:
        return "NAP"
    if weather_id in [801, 802]:
        return "FELHŐS"
    if weather_id == 803:
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
    target = size or ICON_SIZE
    url = f"{BASE_URL}/images/ICONS_PNG80/{name}.png"
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        icon = Image.open(BytesIO(r.content)).convert("RGBA")
        return icon.resize((target, target), Image.Resampling.LANCZOS)
    except Exception as e:
        print(f"  [icon] Nem sikerült betölteni: {name}")
        return None

def draw_glass_bar(img, bx, by, bw, bh, blur=40, dark=80):
    region = img.crop((bx, by, bx + bw, by + bh)).convert("RGBA")
    blurred = region.filter(ImageFilter.GaussianBlur(blur))
    mask = Image.new("L", (bw, bh), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, bw - 1, bh - 1), radius=30, fill=200)
    overlay = Image.new("RGBA", (bw, bh), (0, 0, 15, dark))
    blurred.putalpha(mask)
    result = Image.alpha_composite(blurred, overlay)
    draw = ImageDraw.Draw(result)
    draw.rounded_rectangle((0, 0, bw - 1, bh - 1), radius=30, outline=(255, 255, 255, 35), width=1)
    img.paste(result, (bx, by), result)
    return img

def draw_divider(draw, x, y_top, y_bot, color):
    draw.line([(x, y_top), (x, y_bot)], fill=color, width=1)

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
            nameday_one_line = " · ".join(nameday_list)
        else:
            nameday_one_line = ""

        img = load_bg(weather_id, is_night)
        img = draw_glass_bar(img, WIDGET_X, WIDGET_Y, WIDGET_WIDTH, WIDGET_HEIGHT)

        draw = ImageDraw.Draw(img)
        c_main = (255, 255, 255, 255)
        c_dim = (200, 205, 215, 200)
        c_div = (255, 255, 255, 45)

        f_t = get_f(FONT_TEMP, bold=True)
        f_d = get_f(FONT_DESC)
        f_l = get_f(FONT_LABEL)
        f_v = get_f(FONT_VALUE, bold=True)
        f_u = get_f(FONT_UPDATE)
        f_s = get_f(FONT_SUN)
        f_fd = get_f(FONT_FC_DAY, bold=True)
        f_ft = get_f(FONT_FC_TMP, bold=True)
        f_fc = get_f(FONT_FC_DSC)
        f_n = get_f(FONT_NAMEDAY)

        mid_y = WIDGET_Y + WIDGET_HEIGHT // 2
        y_top = WIDGET_Y + 30
        y_bot = WIDGET_Y + WIDGET_HEIGHT - 30
        curr_x = WIDGET_X + INNER_MARGIN

        # ======================= SZEKCIÓ 1: MA =======================
        draw.text((curr_x, mid_y - 105), "MA", font=f_l, fill=c_dim)
        
        temp_txt = f"{temp}°C"
        draw.text((curr_x, mid_y - 88), temp_txt, font=f_t, fill=c_main)

        weather_text = weather_hu
        draw.text((curr_x, mid_y + 5), weather_text, font=f_d, fill=c_dim)
        
        weather_w = draw.textbbox((0, 0), weather_text, font=f_d)[2]
        feels_temp = f"{feels}°C"
        draw.text((curr_x + weather_w + 20, mid_y + 5), feels_temp, font=f_d, fill=c_dim)

        temp_w = draw.textbbox((0, 0), temp_txt, font=f_t)[2]
        icon_img = load_icon(today_icon_name)
        if icon_img:
            icon_y = mid_y - 88 + 18
            img.paste(icon_img, (curr_x + temp_w + 18, icon_y), icon_img)

        curr_x += max(temp_w + 160, 320)
        draw_divider(draw, curr_x, y_top, y_bot, c_div)
        curr_x += 40

        # ======================= SZEKCIÓ 2: NAPKELTE + SZÉL/PÁRA =======================
        mid_block_width = 480
        
        day_icon = load_icon("day_clear", size=SUN_ICON_SIZE)
        night_icon = load_icon("night_clear", size=SUN_ICON_SIZE)
        
        sr_w = draw.textbbox((0, 0), sunrise_str, font=f_s)[2]
        ss_w = draw.textbbox((0, 0), sunset_str, font=f_s)[2]
        
        sun_total_w = SUN_ICON_SIZE + 8 + sr_w + 40 + SUN_ICON_SIZE + 8 + ss_w
        sun_x = curr_x + (mid_block_width - sun_total_w) // 2
        
        rx = sun_x
        if day_icon:
            img.paste(day_icon, (rx, mid_y - 28), day_icon)
        draw.text((rx + SUN_ICON_SIZE + 8, mid_y - 28), sunrise_str, font=f_s, fill=c_main)
        rx += SUN_ICON_SIZE + 8 + sr_w + 40
        
        if night_icon:
            img.paste(night_icon, (rx, mid_y - 28), night_icon)
        draw.text((rx + SUN_ICON_SIZE + 8, mid_y - 28), sunset_str, font=f_s, fill=c_main)
        
        wind_icon = load_icon("tornado", size=WIND_ICON_SIZE)
        hum_icon = load_icon("para", size=HUM_ICON_SIZE)
        
        wind_text = f"{wind} km/h"
        hum_text = f"{humidity}%"
        
        wind_ico_w = (WIND_ICON_SIZE + 8) if wind_icon else 0
        hum_ico_w = (HUM_ICON_SIZE + 8) if hum_icon else 0
        
        wind_w = draw.textbbox((0, 0), wind_text, font=f_d)[2]
        hum_w = draw.textbbox((0, 0), hum_text, font=f_d)[2]
        
        total_w2 = wind_ico_w + wind_w + 60 + hum_ico_w + hum_w
        info_x = curr_x + (mid_block_width - total_w2) // 2
        row_y = mid_y + 28
        
        wx = info_x
        if wind_icon:
            img.paste(wind_icon, (wx, row_y), wind_icon)
        draw.text((wx + wind_ico_w, row_y), wind_text, font=f_d, fill=c_dim)
        
        hx = info_x + wind_ico_w + wind_w + 60
        if hum_icon:
            img.paste(hum_icon, (hx, row_y), hum_icon)
        draw.text((hx + hum_ico_w, row_y), hum_text, font=f_d, fill=c_dim)
        
        curr_x += mid_block_width
        draw_divider(draw, curr_x, y_top, y_bot, c_div)
        curr_x += 40

        # ======================= SZEKCIÓ 3: ELŐREJELZÉS =======================
        napok = ["H", "K", "SZ", "CS", "P", "SZ", "V"]
        seen_days = set()
        today_date = datetime.now().date()
        
        fc_entries = []
        for entry in f_resp['list']:
            dt = datetime.fromtimestamp(entry['dt'], tz=tz)
            if dt.date() > today_date and dt.date() not in seen_days:
                if dt.hour >= 12:
                    fc_entries.append((dt, entry))
                    seen_days.add(dt.date())
            if len(fc_entries) == 4:
                break
        
        fc_col_w = 145
        for dt, entry in fc_entries[:4]:
            d_name = napok[dt.weekday()]
            f_id = entry['weather'][0]['id']
            f_temp = f"{round(entry['main']['temp'])}°"
            f_desc = get_forecast_hu(f_id)
            
            col_cx = curr_x + fc_col_w // 2
            
            day_w = draw.textbbox((0, 0), d_name, font=f_fd)[2]
            draw.text((col_cx - day_w // 2, y_top + 5), d_name, font=f_fd, fill=c_main)
            
            f_icon = load_icon(get_icon_name(f_id, False), size=FC_ICON_SIZE)
            if f_icon:
                icon_x = col_cx - FC_ICON_SIZE // 2
                icon_y = mid_y - FC_ICON_SIZE // 2
                img.paste(f_icon, (icon_x, icon_y), f_icon)
            
            tmp_w = draw.textbbox((0, 0), f_temp, font=f_ft)[2]
            draw.text((col_cx - tmp_w // 2, y_bot - 55), f_temp, font=f_ft, fill=c_main)
            
            dsc_w = draw.textbbox((0, 0), f_desc, font=f_fc)[2]
            draw.text((col_cx - dsc_w // 2, y_bot - 25), f_desc, font=f_fc, fill=c_dim)
            
            curr_x += fc_col_w
        
        draw_divider(draw, curr_x, y_top, y_bot, c_div)
        curr_x += 40

        # ======================= SZEKCIÓ 4: NÉVNAP =======================
        right_end = WIDGET_X + WIDGET_WIDTH - INNER_MARGIN
        nd_cx = curr_x + (right_end - curr_x) // 2
        
        if nameday_one_line:
            draw.text((nd_cx, mid_y - 40), "NÉVNAP", font=f_l, fill=c_dim, anchor="mm")
            
            nd_w = draw.textbbox((0, 0), nameday_one_line, font=f_n)[2]
            if nd_w > (right_end - curr_x - 40):
                smaller_font = get_f(FONT_NAMEDAY - 8)
                draw.text((nd_cx, mid_y), nameday_one_line, font=smaller_font, fill=c_main, anchor="mm")
            else:
                draw.text((nd_cx, mid_y), nameday_one_line, font=f_n, fill=c_main, anchor="mm")
            
            update_text = f"Frissítve: {local_now.strftime('%H:%M')}"
            draw.text((nd_cx, y_bot - 25), update_text, font=f_u, fill=c_dim, anchor="mm")
        else:
            update_text = f"Frissítve: {local_now.strftime('%H:%M')}"
            draw.text((nd_cx, mid_y - 10), update_text, font=f_u, fill=c_dim, anchor="mm")

        # ======================= MENTÉS =======================
        os.makedirs("images", exist_ok=True)
        img.convert("RGB").save("images/current.jpg", "JPEG", quality=95)
        print(f"[OK] images/current.jpg ({local_now.strftime('%H:%M')})")
        
        # Kép megnyitása Windows-on
        if os.name == 'nt':
            os.startfile(os.path.abspath("images/current.jpg"))
        
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
        print("[OK] weather.json")
        
    except Exception as e:
        import traceback
        print(f"[HIBA] {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()
