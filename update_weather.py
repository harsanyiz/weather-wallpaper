import requests
import json
import os
import time
from datetime import datetime, timezone, timedelta
from PIL import Image, ImageDraw, ImageFont, ImageStat

API_KEY = os.environ.get("OWM_API_KEY")
GITHUB_USER = "harsanyiz"
GITHUB_REPO = "weather-wallpaper"
BRANCH = "main"
BASE_URL = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/{BRANCH}/images"

# ============================================================
# KONFIGURÁCIÓ
# ============================================================
CITY = "Budapest"
WIDGET_WIDTH = 2200
WIDGET_HEIGHT = 200
WIDGET_Y = 100
OFFSET_LEFT = 135
INNER_MARGIN = 80

FONT_TEMP = 90
FONT_DESC = 32
FONT_LABEL = 28
FONT_VALUE = 36
FONT_UPDATE = 24
# ============================================================

def find_font(bold=False):
    paths = [
        "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    ]
    for p in paths:
        if os.path.exists(p): return p
    return None

def get_f(size, bold=False):
    path = find_font(bold)
    if path: return ImageFont.truetype(path, size)
    return ImageFont.load_default()

def get_image_name(weather_id, is_night):
    suffix = "night" if is_night else "day"
    if weather_id in [611, 612, 613, 615, 616]: return f"sleet_{suffix}"
    elif weather_id in [620, 621, 622, 600, 601, 602]: return f"snow_{suffix}"
    elif weather_id == 800: return f"sunny_{suffix}"
    else: return f"cloudy_{suffix}"

def get_weather_hu(weather_id):
    mapping = {800: "Der\u00fclt", 801: "P\u00e1r felh\u0151", 802: "R\u00e9szben felh\u0151s",
               803: "Felh\u0151s", 804: "Borult", 511: "\u00d3nos es\u0151"}
    return mapping.get(weather_id, "V\u00e1ltoz\u00e9kony")

def get_weather_symbol(weather_id, is_night):
    # Sima Unicode szimbolumok - nem color emoji, minden font tudja
    if weather_id == 800:
        return "\u263d" if is_night else "\u2600"   # Hold / Nap
    elif weather_id in [801, 802]:
        return "\u2601"                              # Felhos
    elif weather_id in [803, 804]:
        return "\u2601\u2601"                        # Borult
    elif weather_id in range(500, 532):
        return "\u2602"                              # Eso
    elif weather_id in range(300, 322):
        return "\u2602"                              # Szitalo
    elif weather_id in [611, 612, 613, 615, 616]:
        return "\u2744"                              # Onos
    elif weather_id in range(600, 623):
        return "\u2744"                              # Ho
    elif weather_id in range(200, 233):
        return "\u26a1"                              # Zivatar
    elif weather_id in [701, 711, 721, 731, 741]:
        return "\u2248"                              # Kod
    else:
        return "\u2601"

def get_day_hu(date_obj):
    napok = ["H\u00e9tf\u0151", "Kedd", "Szerda", "Cs\u00fct\u00f6rt\u00f6k", "P\u00e9ntek", "Szombat", "Vas\u00e1rnap"]
    return napok[date_obj.weekday()]

def get_text_colors(brightness):
    if brightness > 145:
        return {"main": (0,0,0,230), "dim": (0,0,0,140), "line": (0,0,0,40)}
    return {"main": (255,255,255,255), "dim": (255,255,255,160), "line": (255,255,255,40)}

def main():
    try:
        resp   = requests.get(f"https://api.openweathermap.org/data/2.5/weather?q={CITY}&appid={API_KEY}&units=metric").json()
        f_resp = requests.get(f"https://api.openweathermap.org/data/2.5/forecast?q={CITY}&appid={API_KEY}&units=metric").json()

        temp       = round(resp["main"]["temp"])
        feels      = round(resp["main"]["feels_like"])
        humidity   = resp["main"]["humidity"]
        wind       = round(resp["wind"]["speed"] * 3.6)
        weather_id = resp["weather"][0]["id"]
        tz_offset  = resp.get("timezone", 3600)
        now_dt     = datetime.now(timezone(timedelta(seconds=tz_offset)))
        update_time = now_dt.strftime("%H:%M")
        is_night   = now_dt.timestamp() < resp["sys"]["sunrise"] or now_dt.timestamp() > resp["sys"]["sunset"]
        image_name = get_image_name(weather_id, is_night)
        weather_hu = get_weather_hu(weather_id)
        symbol     = get_weather_symbol(weather_id, is_night)

        forecast_list = []
        seen_days = set()
        today = now_dt.date()
        for entry in f_resp['list']:
            dt_obj = datetime.fromtimestamp(entry['dt'], tz=timezone(timedelta(seconds=tz_offset)))
            if dt_obj.date() > today and dt_obj.date() not in seen_days and dt_obj.hour >= 12:
                forecast_list.append(entry)
                seen_days.add(dt_obj.date())
            if len(forecast_list) == 3: break
    except Exception as e:
        print(f"Hiba: {e}"); return

    src, dst = f"images/{image_name}.jpg", "images/current.jpg"
    img = Image.open(src).convert("RGB")
    if img.size != (3840, 2160):
        img = img.resize((3840, 2160), Image.Resampling.LANCZOS)

    W, H = img.size
    bx, by, bw, bh = OFFSET_LEFT, WIDGET_Y, WIDGET_WIDTH, WIDGET_HEIGHT

    region = img.crop((bx, by, bx + bw, by + bh)).convert("L")
    avg_brightness = ImageStat.Stat(region).mean[0]
    colors = get_text_colors(avg_brightness)

    draw = ImageDraw.Draw(img)

    f_t  = get_f(FONT_TEMP, True)
    f_d  = get_f(FONT_DESC)
    f_l  = get_f(FONT_LABEL)
    f_v  = get_f(FONT_VALUE, True)
    f_u  = get_f(FONT_UPDATE)
    f_sym = get_f(FONT_TEMP)   # Nagy szimbolum ugyanolyan meret mint a fok

    curr_x = int(bx + INNER_MARGIN)
    mid_y  = int(by + (bh // 2))

    # --- 1. SZEKCIÓ: SZIMBÓLUM + TEMP + LEÍRÁS ---
    sym_txt  = symbol
    temp_txt = f"{temp}\u00b0C"
    desc_txt = weather_hu.upper()
    day_txt  = get_day_hu(now_dt).upper()

    sym_w  = draw.textbbox((0, 0), sym_txt, font=f_sym)[2]
    temp_w = draw.textbbox((0, 0), temp_txt, font=f_t)[2]
    desc_w = draw.textbbox((0, 0), desc_txt, font=f_d)[2]
    day_w  = draw.textbbox((0, 0), day_txt, font=f_l)[2]

    # Szimbolum + fok egymás mellett
    draw.text((curr_x, int(mid_y - 60)), sym_txt, font=f_sym, fill=colors["main"])
    draw.text((curr_x + sym_w + 20, int(mid_y - 60)), temp_txt, font=f_t, fill=colors["main"])

    combined_w = sym_w + 20 + temp_w
    draw.text((int(curr_x + (combined_w - desc_w) / 2), int(mid_y + 38)), desc_txt, font=f_d, fill=colors["dim"])
    draw.text((int(curr_x + (combined_w - day_w) / 2), int(mid_y - 90)), day_txt, font=f_l, fill=colors["dim"])

    curr_x += combined_w + 70
    draw.line([(curr_x, by+40), (curr_x, by+bh-40)], fill=colors["line"], width=3)
    curr_x += 60

    # --- 2. SZEKCIÓ: ADATOK ---
    fields = [
        ("\u00c9rzet", f"{feels}\u00b0C"),
        ("Sz\u00e9l",  f"{wind} km/h"),
        ("P\u00e1ra",  f"{humidity}%")
    ]
    for label, val in fields:
        lw = draw.textbbox((0,0), label.upper(), font=f_l)[2]
        vw = draw.textbbox((0,0), val, font=f_v)[2]
        draw.text((curr_x, int(mid_y - 45)), label.upper(), font=f_l, fill=colors["dim"])
        draw.text((curr_x, int(mid_y)), val, font=f_v, fill=colors["main"])
        curr_x += max(lw, vw) + 80

    # --- 3. SZEKCIÓ: ELŐREJELZÉS ---
    draw.line([(curr_x, by+40), (curr_x, by+bh-40)], fill=colors["line"], width=3)
    curr_x += 60

    for day in forecast_list:
        dt_obj  = datetime.fromtimestamp(day['dt'], tz=timezone(timedelta(seconds=tz_offset)))
        d_name  = get_day_hu(dt_obj).upper()[:3]
        f_wid   = day['weather'][0]['id']
        f_sym   = get_weather_symbol(f_wid, False)
        f_val   = f"{round(day['main']['temp'])}\u00b0C"

        sw = draw.textbbox((0,0), f_sym, font=f_l)[2]
        vw = draw.textbbox((0,0), f_val, font=f_v)[2]
        nw = draw.textbbox((0,0), d_name, font=f_l)[2]
        col_w = max(sw + 10 + vw, nw)

        draw.text((int(curr_x + (col_w - nw)/2), int(mid_y - 50)), d_name, font=f_l, fill=colors["dim"])
        draw.text((curr_x, int(mid_y)), f_sym, font=f_l, fill=colors["dim"])
        draw.text((curr_x + sw + 10, int(mid_y)), f_val, font=f_v, fill=colors["main"])
        curr_x += col_w + 60

    # --- 4. FRISSÍTÉS ---
    draw.text((curr_x + 20, int(mid_y - 12)), f"FRISS\u00cdTVE: {update_time}", font=f_u, fill=colors["dim"])

    img.save(dst, "JPEG", quality=100, subsampling=0)

    v_param = int(time.time())
    image_url = f"{BASE_URL}/current.jpg?v={v_param}"
    weather_json = [{"location": CITY, "title": f"{weather_hu} {temp}C",
                     "author": "OpenWeatherMap", "image_url": image_url, "url_img": image_url}]
    with open("weather.json", "w", encoding="utf-8") as f:
        json.dump(weather_json, f, ensure_ascii=False, indent=2)
    print("Kesz!")

if __name__ == "__main__":
    main()
