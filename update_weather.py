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
WIDGET_WIDTH  = 2200
WIDGET_HEIGHT = 360   # Apple TV HERO ROW
WIDGET_Y      = 80
OFFSET_LEFT   = 135
INNER_MARGIN  = 80
ICON_SIZE     = 80

# Forecast panel méretek
FC_ICON_SIZE  = 64
FC_COL_WIDTH  = 150

# Betűméretek – Apple TV stílus
FONT_TEMP   = 150
FONT_DESC   = 40
FONT_LABEL  = 30
FONT_VALUE  = 32
FONT_UPDATE = 22
FONT_FC_DAY = 30
FONT_FC_TMP = 36
FONT_FC_DSC = 22

# ============================================================
# HÁTTÉRKÉP MAPPING
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
        if img.size != (3840, 2160):
            img = img.resize((3840, 2160), Image.Resampling.LANCZOS)
        return img
    return Image.new("RGBA", (3840, 2160), (5, 5, 15, 255))

def find_font(bold=False):
    paths = [
        "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf"    if bold else "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
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
    if weather_id == 801: return "PÁR FELHŐ"
    if weather_id == 802: return "FELHŐS"
    if weather_id == 803: return "ERŐSEN FELHŐS"
    if weather_id == 804: return "BORULT"
    if weather_id == 511: return "ÓNOS ESŐ"
    if weather_id in range(500, 599): return "ESŐS"
    if weather_id in range(600, 699): return "HAVAS"
    if weather_id in range(700, 799): return "KÖDÖS"
    if weather_id in range(200, 299): return "ZIVATAROS"
    return "VÁLTOZÉKONY"

def get_forecast_hu(weather_id):
    if weather_id == 800: return "NAPOS"
    if weather_id in [801, 802]: return "FELHŐS"
    if weather_id == 803: return "FELHŐS"
    if weather_id == 804: return "BORULT"
    if weather_id in range(500, 599): return "ESŐS"
    if weather_id in range(600, 699): return "HAVAS"
    if weather_id in range(200, 299): return "ZIVATAR"
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
        print(f"  [icon] Nem sikerült betölteni: {name} – {e}")
        return None

def draw_glass_bar(img, bx, by, bw, bh, blur=20, dark=60):
    region = img.crop((bx, by, bx + bw, by + bh)).convert("RGBA")
    blurred = region.filter(ImageFilter.GaussianBlur(blur))
    mask = Image.new("L", (bw, bh), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, bw - 1, bh - 1), radius=50, fill=200)
    overlay = Image.new("RGBA", (bw, bh), (0, 0, 15, dark))
    blurred.putalpha(mask)
    result = Image.alpha_composite(blurred, overlay)
    img.paste(result, (bx, by), result)

    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle(
        (bx, by, bx + bw - 1, by + bh - 1),
        radius=50,
        outline=(255, 255, 255, 35),
        width=1
    )
    return img

def draw_divider(draw, x, y_top, y_bot, color):
    draw.line([(x, y_top), (x, y_bot)], fill=color, width=1)
def main():
    try:
        # ── 1. ADATOK ──────────────────────────────────────────────
        resp   = requests.get(
            f"https://api.openweathermap.org/data/2.5/weather"
            f"?q={CITY}&appid={API_KEY}&units=metric"
        ).json()
        f_resp = requests.get(
            f"https://api.openweathermap.org/data/2.5/forecast"
            f"?q={CITY}&appid={API_KEY}&units=metric"
        ).json()

        temp       = round(resp["main"]["temp"])
        feels      = round(resp["main"]["feels_like"])
        humidity   = resp["main"]["humidity"]
        wind       = round(resp["wind"]["speed"] * 3.6)
        weather_id = resp["weather"][0]["id"]
        tz_offset  = resp.get("timezone", 3600)

        now_ts   = time.time()
        is_night = now_ts < resp["sys"]["sunrise"] or now_ts > resp["sys"]["sunset"]

        today_icon_name = get_icon_name(weather_id, is_night)
        weather_hu      = get_weather_hu(weather_id)

        tz = timezone(timedelta(seconds=tz_offset))
        sunrise_str = datetime.fromtimestamp(resp["sys"]["sunrise"], tz=tz).strftime("%H:%M")
        sunset_str  = datetime.fromtimestamp(resp["sys"]["sunset"],  tz=tz).strftime("%H:%M")
        local_now   = datetime.now(tz)

        # ── 2. HÁTTÉRKÉP ───────────────────────────────────────────
        img = load_bg(weather_id, is_night)

        # ── 3. GLASS BAR (Apple TV stílus) ─────────────────────────
        img = draw_glass_bar(img, OFFSET_LEFT, WIDGET_Y, WIDGET_WIDTH, WIDGET_HEIGHT, blur=20, dark=60)

        draw = ImageDraw.Draw(img)

        # Színek – Apple TV
        c_main = (255, 255, 255, 255)
        c_dim  = (220, 225, 235, 200)
        c_ter  = (200, 205, 215, 140)
        c_div  = (255, 255, 255, 40)

        # Betűk
        f_temp = get_f(FONT_TEMP, bold=True)
        f_desc = get_f(FONT_DESC)
        f_day  = get_f(FONT_LABEL)
        f_val  = get_f(FONT_VALUE, bold=True)
        f_fc_d = get_f(FONT_FC_DAY, bold=True)
        f_fc_t = get_f(FONT_FC_TMP, bold=True)
        f_fc_s = get_f(FONT_FC_DSC)
        f_upd  = get_f(FONT_UPDATE)

        mid_y = WIDGET_Y + WIDGET_HEIGHT // 2
        y_top = WIDGET_Y + 30
        y_bot = WIDGET_Y + WIDGET_HEIGHT - 30

        curr_x = OFFSET_LEFT + 60

        # ───────────────────────────────────────────────────────────
        # BAL BLOKK – ÓRIÁSI IKON + HŐFOK
        # ───────────────────────────────────────────────────────────
        icon_big = load_icon(today_icon_name, size=180)
        if icon_big:
            img.paste(icon_big, (curr_x, mid_y - 140), icon_big)

        curr_x += 220

        temp_txt = f"{temp}°C"
        draw.text((curr_x, mid_y - 120), temp_txt, font=f_temp, fill=c_main)

        temp_w = draw.textbbox((0, 0), temp_txt, font=f_temp)[2]

        draw.text((curr_x, mid_y + 40), weather_hu, font=f_desc, fill=c_dim)

        napok_hosszu = ["HÉTFŐ", "KEDD", "SZERDA", "CSÜTÖRTÖK", "PÉNTEK", "SZOMBAT", "VASÁRNAP"]
        mai_nap = napok_hosszu[local_now.weekday()]
        draw.text((curr_x, mid_y + 90), mai_nap, font=f_day, fill=c_ter)

        curr_x += temp_w + 140
        draw_divider(draw, curr_x, y_top, y_bot, c_div)
        curr_x += 50

        # ───────────────────────────────────────────────────────────
        # KÖZÉPSŐ BLOKK – sunrise / sunset + 3 adat
        # ───────────────────────────────────────────────────────────
        SUN = 56
        day_icon   = load_icon("day_clear",   size=SUN)
        night_icon = load_icon("night_clear", size=SUN)

        # Sunrise
        if day_icon:
            img.paste(day_icon, (curr_x, mid_y - 120), day_icon)
        draw.text((curr_x + SUN + 12, mid_y - 110), sunrise_str, font=f_val, fill=c_main)

        curr_x += 200

        # Sunset
        if night_icon:
            img.paste(night_icon, (curr_x, mid_y - 120), night_icon)
        draw.text((curr_x + SUN + 12, mid_y - 110), sunset_str, font=f_val, fill=c_main)

        curr_x += 240

        # Alsó sor – wind / humidity / feels
        label_icons = [
            ("tornado", f"{wind} km/h"),
            ("para",    f"{humidity}%"),
            ("feel",    f"{feels}°C"),
        ]

        rx = curr_x
        for icon_name, val in label_icons:
            ic = load_icon(icon_name, size=48)
            if ic:
                img.paste(ic, (rx, mid_y + 10), ic)
            draw.text((rx + 60, mid_y + 18), val, font=f_val, fill=c_main)
            rx += 200

        curr_x = rx + 40
        draw_divider(draw, curr_x, y_top, y_bot, c_div)
        curr_x += 50

        # ───────────────────────────────────────────────────────────
        # JOBB BLOKK – 4 nap előrejelzés
        # ───────────────────────────────────────────────────────────
        tz = timezone(timedelta(seconds=tz_offset))
        today_date = datetime.now(tz).date()

        seen_days = set()
        fc_entries = []

        for entry in f_resp['list']:
            dt = datetime.fromtimestamp(entry['dt'], tz=tz)
            if dt.date() > today_date and dt.date() not in seen_days:
                if dt.hour >= 11:
                    fc_entries.append((dt, entry))
                    seen_days.add(dt.date())
            if len(fc_entries) == 4:
                break

        if len(fc_entries) < 4:
            seen_days2 = set(e[0].date() for e in fc_entries)
            for entry in f_resp['list']:
                dt = datetime.fromtimestamp(entry['dt'], tz=tz)
                if dt.date() > today_date and dt.date() not in seen_days2:
                    fc_entries.append((dt, entry))
                    seen_days2.add(dt.date())
                if len(fc_entries) == 4:
                    break
            fc_entries.sort(key=lambda x: x[0])

        for dt, entry in fc_entries[:4]:
            d_name = ["HÉ", "KE", "SZE", "CS", "PÉ", "SZO", "VA"][dt.weekday()]
            f_id   = entry['weather'][0]['id']
            f_temp = f"{round(entry['main']['temp'])}°C"
            f_desc = get_forecast_hu(f_id)

            cx = curr_x + FC_COL_WIDTH // 2

            # Nap neve
            w = draw.textbbox((0, 0), d_name, font=f_fc_d)[2]
            draw.text((cx - w // 2, y_top + 10), d_name, font=f_fc_d, fill=c_main)

            # Ikon
            ic = load_icon(get_icon_name(f_id, False), size=FC_ICON_SIZE)
            if ic:
                img.paste(ic, (cx - FC_ICON_SIZE // 2, mid_y - 40), ic)

            # Hőfok
            tw = draw.textbbox((0, 0), f_temp, font=f_fc_t)[2]
            draw.text((cx - tw // 2, y_bot - 80), f_temp, font=f_fc_t, fill=c_main)

            # Leírás
            dw = draw.textbbox((0, 0), f_desc, font=f_fc_s)[2]
            draw.text((cx - dw // 2, y_bot - 40), f_desc, font=f_fc_s, fill=c_dim)

            curr_x += FC_COL_WIDTH

        # ───────────────────────────────────────────────────────────
        # FRISSÍTVE
        # ───────────────────────────────────────────────────────────
        update_line1 = "FRISSÍTVE"
        update_line2 = local_now.strftime("%H:%M")

        upd_w = max(
            draw.textbbox((0, 0), update_line1, font=f_upd)[2],
            draw.textbbox((0, 0), update_line2, font=f_upd)[2]
        )

        upd_x = OFFSET_LEFT + WIDGET_WIDTH - upd_w - 40

        draw.text((upd_x, mid_y + 40), update_line1, font=f_upd, fill=c_dim)
        draw.text((upd_x, mid_y + 70), update_line2, font=f_upd, fill=c_main)

        # ── MENTÉS ───────────────────────────────────────────────────
        os.makedirs("images", exist_ok=True)
        img.convert("RGB").save("images/current.jpg", "JPEG", quality=95)
        print(f"[OK] images/current.jpg elmentve ({local_now.strftime('%H:%M')})")

        # JSON frissítés
        v_param   = int(time.time())
        image_url = (
            f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}"
            f"/{BRANCH}/images/current.jpg?v={v_param}"
        )
        weather_json = [{
            "location":  CITY,
            "title":     f"{weather_hu} {temp}°C",
            "image_url": image_url,
            "url_img":   image_url,
        }]
        with open("weather.json", "w", encoding="utf-8") as f:
            json.dump(weather_json, f, ensure_ascii=False, indent=2)
        print("[OK] weather.json frissítve")

    except Exception as e:
        import traceback
        print(f"[HIBA] {e}")
        traceback.print_exc()
