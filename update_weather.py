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
WIDGET_HEIGHT = 240
WIDGET_Y      = 80
OFFSET_LEFT   = 135
INNER_MARGIN  = 80
ICON_SIZE     = 80

# Forecast panel méretek
FC_ICON_SIZE  = 48   # kisebb ikon az előrejelzésnél
FC_COL_WIDTH  = 120  # egy nap oszlopszélessége

FONT_TEMP   = 90
FONT_DESC   = 30
FONT_LABEL  = 26
FONT_VALUE  = 34
FONT_UPDATE = 22
FONT_SUN    = 20
FONT_FC_DAY = 28   # nap neve (felül)
FONT_FC_TMP = 30   # hőmérséklet (alul)
FONT_FC_DSC = 20   # leírás (alul, kicsi)
# ============================================================

# ---- Háttérkép mapping ----
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
        # resize to 3840x2160 ha szükséges
        if img.size != (3840, 2160):
            img = img.resize((3840, 2160), Image.Resampling.LANCZOS)
        return img
    # fallback: sötét alap
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

def draw_glass_bar(img, bx, by, bw, bh, blur=40, dark=100):
    """Glassmorphism bar: blur + sötét overlay + rounded mask."""
    region = img.crop((bx, by, bx + bw, by + bh)).convert("RGBA")
    blurred = region.filter(ImageFilter.GaussianBlur(blur))
    mask = Image.new("L", (bw, bh), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, bw - 1, bh - 1), radius=30, fill=200)
    overlay = Image.new("RGBA", (bw, bh), (0, 0, 15, dark))
    blurred.putalpha(mask)
    result = Image.alpha_composite(blurred, overlay)
    img.paste(result, (bx, by), result)

    # Finom keret
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle(
        (bx, by, bx + bw - 1, by + bh - 1),
        radius=30,
        outline=(255, 255, 255, 35),
        width=1
    )
    return img

def draw_divider(draw, x, y_top, y_bot, color):
    for dx in [0, 3]:
        draw.line([(x + dx, y_top), (x + dx, y_bot)], fill=color, width=1)

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

        # ── 2. ALAP: HÁTTÉRKÉP (időjárás + napszak) ────────────────
        img = load_bg(weather_id, is_night)

        # ── 3. GLASS BAR ───────────────────────────────────────────
        img = draw_glass_bar(img, OFFSET_LEFT, WIDGET_Y, WIDGET_WIDTH, WIDGET_HEIGHT)

        draw = ImageDraw.Draw(img)
        c_main = (255, 255, 255, 255)
        c_dim  = (200, 205, 215, 200)
        c_div  = (255, 255, 255, 45)

        f_t  = get_f(FONT_TEMP,  bold=True)
        f_d  = get_f(FONT_DESC)
        f_l  = get_f(FONT_LABEL)
        f_v  = get_f(FONT_VALUE, bold=True)
        f_u  = get_f(FONT_UPDATE)
        f_s  = get_f(FONT_SUN)
        f_fd = get_f(FONT_FC_DAY, bold=True)
        f_ft = get_f(FONT_FC_TMP, bold=True)
        f_fc = get_f(FONT_FC_DSC)

        mid_y  = WIDGET_Y + WIDGET_HEIGHT // 2
        y_top  = WIDGET_Y + 30
        y_bot  = WIDGET_Y + WIDGET_HEIGHT - 30
        curr_x = OFFSET_LEFT + INNER_MARGIN

        # ── SZEKCIÓ 1: MA (hőmérséklet + ikon + leírás) ────────────
        napok_hosszu = ["HÉTFŐ", "KEDD", "SZERDA", "CSÜTÖRTÖK", "PÉNTEK", "SZOMBAT", "VASÁRNAP"]
        mai_nap = napok_hosszu[local_now.weekday()]
        c_ghost = (200, 205, 215, 110)   # egy árnyalattal halványabb mint c_dim

        ma_w = draw.textbbox((0, 0), "MA", font=f_l)[2]
        draw.text((curr_x,           mid_y - 105), "MA",    font=f_l, fill=c_dim)
        draw.text((curr_x + ma_w + 10, mid_y - 105), mai_nap, font=f_l, fill=c_ghost)
        temp_txt = f"{temp}°C"
        draw.text((curr_x, mid_y - 88), temp_txt, font=f_t, fill=c_main)

        temp_w = draw.textbbox((0, 0), temp_txt, font=f_t)[2]
        icon_img = load_icon(today_icon_name)
        if icon_img:
            # a hőfok szöveg tetejétől számítva optikai közép, régi és új pozíció közepe
            text_top = mid_y - 88
            icon_y = text_top + 18   # kb. a régi és új közepe
            img.paste(icon_img, (curr_x + temp_w + 18, icon_y), icon_img)

        draw.text((curr_x, mid_y + 35), weather_hu, font=f_d, fill=c_dim)

        curr_x += max(temp_w + 160, 270)
        draw_divider(draw, curr_x, y_top, y_bot, c_div)
        curr_x += 36

        # ── SZEKCIÓ 2+3: NAPKELTE/NAPNYUGTA + ADATOK – két sor, egy blokk ──────────────────
        LABEL_ICON_SIZE = 36
        SUN_ICON_SIZE   = 36

        day_icon   = load_icon("day_clear",   size=SUN_ICON_SIZE)
        night_icon = load_icon("night_clear", size=SUN_ICON_SIZE)

        # Két sor magasságának kiszámítása, a blokk mid_y körül középre
        val_h  = draw.textbbox((0, 0), "0°C", font=f_v)[3]
        time_h = draw.textbbox((0, 0), "00:00", font=f_v)[3]
        row_h  = max(LABEL_ICON_SIZE, val_h)
        gap    = 14   # sorok közötti rés

        # két sor összmagassága
        block_h = row_h + gap + row_h
        block_y = mid_y - block_h // 2   # blokk teteje

        # 1. SOR: ☀️ 05:44  •  🌙 19:40  (felső)
        sun_row_y   = block_y
        sicon_y     = sun_row_y + (row_h - SUN_ICON_SIZE) // 2
        stext_y     = sun_row_y + (row_h - time_h) // 2

        sun_start_x = curr_x

        if day_icon:
            img.paste(day_icon, (curr_x, sicon_y), day_icon)
        sr_w = draw.textbbox((0, 0), sunrise_str, font=f_v)[2]
        draw.text((curr_x + SUN_ICON_SIZE + 8, stext_y), sunrise_str, font=f_v, fill=c_main)
        curr_x += SUN_ICON_SIZE + 8 + sr_w + 16

        dot_w = draw.textbbox((0, 0), "•", font=f_v)[2]
        draw.text((curr_x, stext_y), "•", font=f_v, fill=c_dim)
        curr_x += dot_w + 16

        if night_icon:
            img.paste(night_icon, (curr_x, sicon_y), night_icon)
        ss_w = draw.textbbox((0, 0), sunset_str, font=f_v)[2]
        draw.text((curr_x + SUN_ICON_SIZE + 8, stext_y), sunset_str, font=f_v, fill=c_main)
        sun_end_x = curr_x + SUN_ICON_SIZE + 8 + ss_w

        # 2. SOR: 🌡️ 10°C  🌪️ 11km/h  💧 57%  (alsó, ugyanolyan szélességre igazítva)
        label_icons = [
            ("feel",    f"{feels}°C"),
            ("tornado", f"{wind} km/h"),
            ("para",    f"{humidity}%"),
        ]
        # Előre kiszámítjuk a sor teljes szélességét hogy középre igazíthassuk
        row2_total = 0
        for icon_name, val in label_icons:
            val_w = draw.textbbox((0, 0), val, font=f_v)[2]
            row2_total += LABEL_ICON_SIZE + 10 + val_w + 30
        row2_total -= 30  # utolsó rés levonása

        sun_width   = sun_end_x - sun_start_x
        block_width = max(sun_width, row2_total)

        # 2. sor bal széle úgy hogy középre essen a napkelte sorhoz képest
        row2_x = sun_start_x + (sun_width - row2_total) // 2
        row2_y = block_y + row_h + gap
        icon_oy = row2_y + (row_h - LABEL_ICON_SIZE) // 2
        text_oy = row2_y + (row_h - val_h) // 2

        rx = row2_x
        for icon_name, val in label_icons:
            lbl_icon = load_icon(icon_name, size=LABEL_ICON_SIZE)
            if lbl_icon:
                img.paste(lbl_icon, (rx, icon_oy), lbl_icon)
            val_w = draw.textbbox((0, 0), val, font=f_v)[2]
            draw.text((rx + LABEL_ICON_SIZE + 10, text_oy), val, font=f_v, fill=c_main)
            rx += LABEL_ICON_SIZE + 10 + val_w + 30

        # block_width = a két sor közül a szélesebb, curr_x a napsütötte sor vége alapján
        curr_x = max(sun_end_x, row2_x + row2_total) + 30
        draw_divider(draw, curr_x, y_top, y_bot, c_div)
        curr_x += 36

        # ── SZEKCIÓ 4: ELŐREJELZÉS ───────────────────────────────────
        # Layout: nap neve FELÜL (nagy), ikon középen, hőfok + leírás ALUL (kicsi)
        napok = ["HÉ", "KE", "SZE", "CS", "PÉ", "SZO", "VA"]
        seen_days = set()
        count = 0
        today_date = datetime.now().date()

        fc_entries = []
        for entry in f_resp['list']:
            dt = datetime.fromtimestamp(entry['dt'], tz=tz)
            if dt.date() > today_date and dt.date() not in seen_days:
                if dt.hour >= 11:
                    fc_entries.append((dt, entry))
                    seen_days.add(dt.date())
            if len(fc_entries) == 4:
                break

        # Ha valamelyik napra nem volt 11 utáni adat, vegyük a legközelebbit
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

        fc_start_x = curr_x

        widget_right = OFFSET_LEFT + WIDGET_WIDTH - INNER_MARGIN
        upd1_w = draw.textbbox((0, 0), "FRISSÍTVE", font=f_u)[2]
        upd2_w = draw.textbbox((0, 0), "00:00", font=f_u)[2]
        upd_reserved = max(upd1_w, upd2_w) + 80
        fc_available = widget_right - upd_reserved - fc_start_x
        fc_col_w = min(FC_COL_WIDTH, fc_available // 4)

        for dt, entry in fc_entries[:4]:
            d_name = napok[dt.weekday()]
            f_id   = entry['weather'][0]['id']
            f_temp = f"{round(entry['main']['temp'])}°C"
            f_desc = get_forecast_hu(f_id)

            col_cx = curr_x + fc_col_w // 2

            # NAP NEVE – felső sor
            day_w = draw.textbbox((0, 0), d_name, font=f_fd)[2]
            draw.text((col_cx - day_w // 2, y_top + 2), d_name, font=f_fd, fill=c_main)

            # IKON – középre
            f_icon = load_icon(get_icon_name(f_id, False), size=FC_ICON_SIZE)
            if f_icon:
                icon_x = col_cx - FC_ICON_SIZE // 2
                icon_y = mid_y - FC_ICON_SIZE // 2 - 8
                img.paste(f_icon, (icon_x, icon_y), f_icon)

            # HŐFOK – alsó sor
            tmp_w = draw.textbbox((0, 0), f_temp, font=f_ft)[2]
            draw.text((col_cx - tmp_w // 2, y_bot - 58), f_temp, font=f_ft, fill=c_main)

            # LEÍRÁS – legalsó sor
            dsc_w = draw.textbbox((0, 0), f_desc, font=f_fc)[2]
            draw.text((col_cx - dsc_w // 2, y_bot - 28), f_desc, font=f_fc, fill=c_dim)

            curr_x += fc_col_w

        # ── SZEKCIÓ 5: FRISSÍTVE – jobb szélhez rögzítve ────────────
        update_line1 = "FRISSÍTVE"
        update_line2 = local_now.strftime("%H:%M")
        upd1_w = draw.textbbox((0, 0), update_line1, font=f_u)[2]
        upd2_w = draw.textbbox((0, 0), update_line2, font=f_u)[2]
        upd_text_w = max(upd1_w, upd2_w)
        upd_x = widget_right - upd_text_w

        # Elválasztó mindig megjelenik, fix pozícióban a szöveg előtt
        div_x = upd_x - 40
        draw_divider(draw, div_x, y_top, y_bot, c_div)

        draw.text((upd_x, mid_y - 28), update_line1, font=f_u, fill=c_dim)
        draw.text((upd_x, mid_y +  4), update_line2, font=f_u, fill=c_main)

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

if __name__ == "__main__":
    main()
