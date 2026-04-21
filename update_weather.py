import requests
import json
from io import BytesIO
import os
import time
import math
from datetime import datetime, timezone, timedelta
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageStat

API_KEY = os.environ.get("OWM_API_KEY")
GITHUB_USER = "harsanyiz"
GITHUB_REPO = "weather-wallpaper"
BRANCH = "main"
BASE_URL = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/{BRANCH}/images"

# ============================================================
# KONFIGURÁCIÓ - EREDETI STÍLUS
# ============================================================
CITY = "Budapest"
WIDGET_WIDTH = 2200
WIDGET_HEIGHT = 220
WIDGET_Y = 80
OFFSET_LEFT = 135
INNER_MARGIN = 80

FONT_TEMP   = 90
FONT_DESC   = 32
FONT_LABEL  = 28
FONT_VALUE  = 36
FONT_UPDATE = 24
FONT_SUN    = 22
FONT_TIMESTAMP = 28
ICON_SIZE   = 80
# ============================================================

# Ikon cache
icon_cache = {}

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

def get_icon_name(weather_id, is_night):
    """OWM weather_id → ikon fájlnév (a meglévő jpg-k alapján)"""
    suffix = "night" if is_night else "day"
    
    if weather_id in [611, 612, 613, 615, 616]:
        return f"sleet_{suffix}"
    elif weather_id in [620, 621, 622, 600, 601, 602]:
        return f"snow_{suffix}"
    elif weather_id == 800:
        return f"sunny_{suffix}"
    elif weather_id in [500, 501, 502, 511, 520, 521, 522]:
        return f"rainy_{suffix}"
    elif weather_id in [200, 201, 202, 210, 211, 212, 221, 230, 231, 232]:
        return f"hail_{suffix}"
    elif weather_id in [701, 711, 721, 741, 751, 761, 762]:
        return f"foggy_{suffix}"
    else:
        return f"cloudy_{suffix}"

def load_icon(name):
    """PNG/JPG ikon betöltése cache-el - a te mappádban jpg-k vannak"""
    if name in icon_cache and icon_cache[name] is not None:
        return icon_cache[name]
    
    # Először jpg-t próbálunk (a te fájljaid .jpg)
    for ext in ['.jpg', '.png']:
        url = f"{BASE_URL}/ICONS_PNG80/{name}{ext}"
        try:
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                icon = Image.open(BytesIO(r.content)).convert("RGBA")
                icon = icon.resize((ICON_SIZE, ICON_SIZE), Image.Resampling.LANCZOS)
                icon_cache[name] = icon
                print(f"Ikon betöltve: {name}{ext}")
                return icon
        except:
            continue
    
    print(f"Ikon nem található: {name}")
    icon_cache[name] = None
    return None

def paste_icon(img, icon, cx, cy):
    """Ikon beillesztése – cx/cy a középpont."""
    if icon is None: return
    img.paste(icon, (cx - ICON_SIZE//2, cy - ICON_SIZE//2), icon)

def get_weather_hu(weather_id):
    mapping = {800: "Derült", 801: "Pár felhő", 802: "Részben felhős",
               803: "Felhős", 804: "Borult", 511: "Ónos eső"}
    return mapping.get(weather_id, "Változékony")

def get_forecast_hu(weather_id):
    if weather_id == 800: return "Napos"
    elif weather_id in [801, 802]: return "Felhős"
    elif weather_id in [803, 804]: return "Borult"
    elif weather_id in range(500, 532): return "Esős"
    elif weather_id in range(300, 322): return "Szitál"
    elif weather_id in range(600, 623): return "Havas"
    elif weather_id in range(200, 233): return "Zivatar"
    return "Változék"

def get_day_hu(date_obj):
    napok = ["Hétfő", "Kedd", "Szerda", "Csütörtök", "Péntek", "Szombat", "Vasárnap"]
    return napok[date_obj.weekday()]

def get_text_colors(brightness):
    if brightness > 145:
        return {"main": (0,0,0,230), "dim": (0,0,0,140), "line": (0,0,0,60), "blur": (0,0,0,80)}
    return {"main": (255,255,255,255), "dim": (255,255,255,160), "line": (255,255,255,50), "blur": (0,0,0,120)}

def draw_glass_bar(img, bx, by, bw, bh):
    """Eredeti blur sáv a widget mögött"""
    region = img.crop((bx, by, bx + bw, by + bh))
    blurred = region.filter(ImageFilter.GaussianBlur(30))
    mask = Image.new("L", (bw, bh), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle((0, 0, bw, bh), radius=30, fill=180)
    overlay = Image.new("RGBA", (bw, bh), (0, 0, 10, 100))
    blurred = blurred.convert("RGBA")
    blurred.putalpha(mask)
    result = Image.alpha_composite(blurred, overlay)
    img.paste(result, (bx, by), result)
    return img

def format_sun_time(ts, tz_offset):
    dt = datetime.fromtimestamp(ts, tz=timezone(timedelta(seconds=tz_offset)))
    return dt.strftime("%H:%M")

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
        full_timestamp = now_dt.strftime("%Y-%m-%d %H:%M:%S")
        is_night   = now_dt.timestamp() < resp["sys"]["sunrise"] or now_dt.timestamp() > resp["sys"]["sunset"]
        image_name = get_image_name(weather_id, is_night)
        icon_name  = get_icon_name(weather_id, is_night)
        weather_hu = get_weather_hu(weather_id)
        sunrise_str = format_sun_time(resp["sys"]["sunrise"], tz_offset)
        sunset_str  = format_sun_time(resp["sys"]["sunset"],  tz_offset)

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
    bx = OFFSET_LEFT
    by = WIDGET_Y
    bw = WIDGET_WIDTH
    bh = WIDGET_HEIGHT

    # Ikon betöltése
    weather_icon = load_icon(icon_name)

    img = img.convert("RGBA")
    img = draw_glass_bar(img, bx, by, bw, bh)

    region = img.crop((bx, by, bx + bw, by + bh)).convert("L")
    avg_brightness = ImageStat.Stat(region).mean[0]
    colors = get_text_colors(avg_brightness)

    draw = ImageDraw.Draw(img)

    f_t  = get_f(FONT_TEMP,   True)
    f_d  = get_f(FONT_DESC)
    f_l  = get_f(FONT_LABEL)
    f_v  = get_f(FONT_VALUE,  True)
    f_u  = get_f(FONT_UPDATE)
    f_s  = get_f(FONT_SUN)
    f_ts = get_f(FONT_TIMESTAMP)

    curr_x = int(bx + INNER_MARGIN)
    mid_y  = int(by + bh // 2)

    # --- 1. SZEKCIO: NAP + HOMERSEKLET + LEIRAS ---
    day_txt  = get_day_hu(now_dt).upper()
    temp_txt = f"{temp}°C"
    desc_txt = weather_hu.upper()

    day_w  = draw.textbbox((0,0), day_txt,  font=f_l)[2]
    temp_w = draw.textbbox((0,0), temp_txt, font=f_t)[2]
    desc_w = draw.textbbox((0,0), desc_txt, font=f_d)[2]
    max_w  = max(day_w, temp_w, desc_w)

    draw.text((int(curr_x + (max_w - day_w)  / 2), int(mid_y - 90)), day_txt,  font=f_l, fill=colors["dim"])
    draw.text((int(curr_x + (max_w - temp_w) / 2), int(mid_y - 62)), temp_txt, font=f_t, fill=colors["main"])
    draw.text((int(curr_x + (max_w - desc_w) / 2), int(mid_y + 38)), desc_txt, font=f_d, fill=colors["dim"])

    # Ikon a hőfok jobb oldalán
    paste_icon(img, weather_icon, int(curr_x + max_w + 35 + ICON_SIZE//2), mid_y - 10)
    curr_x += int(max_w + 35 + ICON_SIZE + 25)

    # Elegans elvalaszto – dupla vonal
    lc = colors["line"]
    draw.line([(curr_x,   by+35), (curr_x,   by+bh-35)], fill=lc, width=1)
    draw.line([(curr_x+4, by+35), (curr_x+4, by+bh-35)], fill=lc, width=1)
    curr_x += 40

    # --- 2. SZEKCIO: ADATOK ---
    fields = [
        ("Érzet", f"{feels}°C"),
        ("Szél",  f"{wind} km/h"),
        ("Pára",  f"{humidity}%"),
    ]
    for label, val in fields:
        lw = draw.textbbox((0,0), label.upper(), font=f_l)[2]
        vw = draw.textbbox((0,0), val,            font=f_v)[2]
        draw.text((curr_x, int(mid_y - 48)), label.upper(), font=f_l, fill=colors["dim"])
        draw.text((curr_x, int(mid_y + 2)),  val,           font=f_v, fill=colors["main"])
        curr_x += max(lw, vw) + 70

    # Dupla elvalaszto
    draw.line([(curr_x,   by+35), (curr_x,   by+bh-35)], fill=lc, width=1)
    draw.line([(curr_x+4, by+35), (curr_x+4, by+bh-35)], fill=lc, width=1)
    curr_x += 40

    # --- 3. SZEKCIO: NAPKELTE / NAPNYUGTA ---
    sun_label = "NAPKELTE / NAPNYUGTA"
    sun_val   = f"{sunrise_str}  •  {sunset_str}"
    slw = draw.textbbox((0,0), sun_label, font=f_s)[2]
    svw = draw.textbbox((0,0), sun_val,   font=f_v)[2]
    col_w = max(slw, svw)
    draw.text((int(curr_x + (col_w-slw)/2), int(mid_y - 48)), sun_label, font=f_s, fill=colors["dim"])
    draw.text((int(curr_x + (col_w-svw)/2), int(mid_y + 2)),  sun_val,   font=f_v, fill=colors["main"])
    curr_x += col_w + 70

    # Dupla elvalaszto
    draw.line([(curr_x,   by+35), (curr_x,   by+bh-35)], fill=lc, width=1)
    draw.line([(curr_x+4, by+35), (curr_x+4, by+bh-35)], fill=lc, width=1)
    curr_x += 40

    # --- 4. SZEKCIO: 3 NAPOS ELORELJELZES ---
    for day in forecast_list:
        dt_obj  = datetime.fromtimestamp(day['dt'], tz=timezone(timedelta(seconds=tz_offset)))
        d_name  = get_day_hu(dt_obj).upper()[:3]
        f_wid   = day['weather'][0]['id']
        f_val   = f"{round(day['main']['temp'])}°C"
        f_desc  = get_forecast_hu(f_wid).upper()

        nw = draw.textbbox((0,0), d_name, font=f_l)[2]
        vw = draw.textbbox((0,0), f_val,  font=f_v)[2]
        dw = draw.textbbox((0,0), f_desc, font=f_s)[2]
        col_w = max(nw, vw, dw)

        draw.text((int(curr_x + (col_w-nw)/2), int(mid_y - 90)), d_name, font=f_l, fill=colors["dim"])
        draw.text((int(curr_x + (col_w-vw)/2), int(mid_y - 55)), f_val,  font=f_v, fill=colors["main"])
        draw.text((int(curr_x + (col_w-dw)/2), int(mid_y - 10)), f_desc, font=f_s, fill=colors["dim"])
        curr_x += col_w + 55

    # --- 5. FRISSÍTÉS ---
    draw.line([(curr_x,   by+35), (curr_x,   by+bh-35)], fill=lc, width=1)
    draw.line([(curr_x+4, by+35), (curr_x+4, by+bh-35)], fill=lc, width=1)
    curr_x += 30
    update_txt = f"FRISSÍTVE\n{update_time}"
    draw.text((curr_x + 20, int(mid_y - 30)), update_txt, font=f_u, fill=colors["dim"])

    # ============================================================
    # 6. IDŐBÉLYEG A KÉP ALJÁN (vékony, nem zavaró)
    # ============================================================
    timestamp_y = H - 45
    timestamp_text = f"{full_timestamp}"
    ts_w = draw.textbbox((0,0), timestamp_text, font=f_ts)[2]
    draw.text((int((W - ts_w) / 2), timestamp_y), timestamp_text, font=f_ts, fill=colors["dim"])

    img.convert("RGB").save(dst, "JPEG", quality=100, subsampling=0)

    v_param   = int(time.time())
    image_url = f"{BASE_URL}/current.jpg?v={v_param}"
    weather_json = [{"location": CITY, "title": f"{weather_hu} {temp}C",
                     "author": "OpenWeatherMap", "image_url": image_url, "url_img": image_url}]
    with open("weather.json", "w", encoding="utf-8") as f:
        json.dump(weather_json, f, ensure_ascii=False, indent=2)
    print("Kész!")

if __name__ == "__main__":
    main()
