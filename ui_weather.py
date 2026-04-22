from PIL import Image, ImageDraw, ImageFont, ImageStat
from datetime import datetime, timezone, timedelta

# ============================================================
# 4K-S HORIZONTÁLIS DESIGN - PIXEL PERFECT EDITION
# ============================================================
WIDGET_WIDTH  = 2400
WIDGET_HEIGHT = 200
WIDGET_Y      = 100
OFFSET_LEFT   = 135
INNER_MARGIN  = 80

FONT_TEMP     = 100  # Picit növelve a tekintély kedvéért
FONT_HEADER   = 24
FONT_LABEL    = 28
FONT_VALUE    = 36
FONT_SMALL    = 34  # Nagyobb, hogy jobban látszódjon a baseline
FONT_DATETIME = 24
FONT_NAME     = 28
FONT_FORECAST_DAY = 22
FONT_FORECAST_TEMP = 32

ICON_DISPLAY_SIZE  = 160
FEEL_ICON_SIZE     = 34
WIND_ICON_SIZE     = 36
PARA_ICON_SIZE     = 36
FORECAST_ICON_SIZE = 56   # Nagyobb ikonok az előrejelzéshez
SUN_ICON_SIZE      = 40
ICON_GAP           = 12

def find_font(bold=False):
    paths = [
        "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for p in paths:
        import os
        if os.path.exists(p): return p
    return None

def get_f(size, bold=False):
    path = find_font(bold)
    return ImageFont.truetype(path, size) if path else ImageFont.load_default()

def get_text_colors(brightness):
    if brightness > 145:
        return {"main": (0, 0, 0, 230), "dim": (0, 0, 0, 140), "line": (0, 0, 0, 40)}
    return {"main": (255, 255, 255, 255), "dim": (255, 255, 255, 160), "line": (255, 255, 255, 40)}

def paste_icon(img, icon_img, x, y, size=ICON_DISPLAY_SIZE):
    if icon_img:
        resized = icon_img.resize((size, size), Image.Resampling.LANCZOS)
        img.paste(resized, (int(x), int(y)), resized)

def draw_weather_widget(img, weather, icon_img, feel_icon_img,
                        wind_icon_img, para_icon_img,
                        forecast_icons, sunrise_icon_img, sunset_icon_img,
                        namedays, tz_offset):
    from logic_weather import get_day_hu

    bx, by, bw, bh = OFFSET_LEFT, WIDGET_Y, WIDGET_WIDTH, WIDGET_HEIGHT
    region = img.crop((bx, by, bx + bw, by + bh)).convert("L")
    colors = get_text_colors(ImageStat.Stat(region).mean[0])
    draw = ImageDraw.Draw(img)
    
    f_t, f_h, f_v, f_s = get_f(FONT_TEMP, True), get_f(FONT_HEADER), get_f(FONT_VALUE, True), get_f(FONT_SMALL)
    f_dt, f_n, f_fd, f_fv = get_f(FONT_DATETIME), get_f(FONT_NAME), get_f(FONT_FORECAST_DAY), get_f(FONT_FORECAST_TEMP, True)

    mid_y = by + (bh // 2)
    curr_x = bx + INNER_MARGIN

    # ── SZEKCIÓ 1: AKTUÁLIS (Baseline Tuning) ─────────────────────────────
    SEC1_W = 620 # Picit szélesebb a nagy szám miatt
    sec1_mid = curr_x + (SEC1_W // 2)
    
    day_txt, desc_txt = get_day_hu(weather["now_dt"]).upper(), weather["weather_hu"].upper()
    temp_txt, feel_txt = f"{weather['temp']}°C", f"{weather['feels_like']}°C"

    t_bbox = draw.textbbox((0, 0), temp_txt, font=f_t)
    t_w, t_h = t_bbox[2], t_bbox[3]
    f_w = draw.textbbox((0, 0), feel_txt, font=f_s)[2]
    
    main_w = ICON_DISPLAY_SIZE + 40 + t_w + 35 + FEEL_ICON_SIZE + 10 + f_w
    start_x = sec1_mid - (main_w // 2)

    if icon_img:
        paste_icon(img, icon_img, start_x, mid_y - ICON_DISPLAY_SIZE // 2)
    
    tx = start_x + ICON_DISPLAY_SIZE + 40
    
    # Kiszámoljuk a nagy szám pozícióját, hogy függőlegesen középen legyen
    temp_y = mid_y - (t_h // 2) - 10
    
    # Fejléc - igazítva a temp felé
    draw.text((tx, temp_y - 45), f"{day_txt}  {desc_txt}", font=f_h, fill=colors["dim"])
    
    # Nagy hőfok kirajzolása
    draw.text((tx, temp_y), temp_txt, font=f_t, fill=colors["main"])
    
    # --- BASELINE IGAZÍTÁS ---
    # Megkeressük a nagy szám alapvonalát (temp_y + t_h)
    target_baseline = temp_y + t_h
    
    feel_x = tx + t_w + 35
    # A kis számot és az ikont ehhez a vonalhoz húzzuk le
    if feel_icon_img:
        paste_icon(img, feel_icon_img, feel_x, target_baseline - FEEL_ICON_SIZE - 5, size=FEEL_ICON_SIZE)
    
    # A kis szöveg y koordinátáját úgy állítjuk be, hogy az alja a target_baseline legyen
    feel_txt_h = draw.textbbox((0, 0), feel_txt, font=f_s)[3]
    draw.text((feel_x + FEEL_ICON_SIZE + 10, target_baseline - feel_txt_h - 2), feel_txt, font=f_s, fill=colors["dim"])

    curr_x += SEC1_W
    draw.line([(curr_x, by + 50), (curr_x, by + bh - 50)], fill=colors["line"], width=2)

    # ── SZEKCIÓ 2 & 3: ADATOK ────────────────────────────────────────
    for data_w, items in [(260, [(weather['wind_kmh'], " km/h", wind_icon_img), (weather['humidity'], "%", para_icon_img)]),
                         (240, [(weather['sunrise'], "", sunrise_icon_img), (weather['sunset'], "", sunset_icon_img)])]:
        sec_mid = curr_x + (data_w // 2)
        for i, (val, unit, icon) in enumerate(items):
            txt = f"{val}{unit}"
            v_w = draw.textbbox((0, 0), txt, font=f_v)[2]
            item_x = sec_mid - ((WIND_ICON_SIZE + 12 + v_w) // 2)
            y_pos = mid_y - 65 if i == 0 else mid_y + 10
            if icon: paste_icon(img, icon, item_x, y_pos + 5, size=WIND_ICON_SIZE)
            draw.text((item_x + WIND_ICON_SIZE + 12, y_pos), txt, font=f_v, fill=colors["main"])
        curr_x += data_w
        draw.line([(curr_x, by + 50), (curr_x, by + bh - 50)], fill=colors["line"], width=2)

    # ── SZEKCIÓ 4: FORECAST ─────────────────────────────────────────────
    SEC4_W = 520
    slot_w = SEC4_W // 3
    for i, day_entry in enumerate(weather["forecast"]):
        slot_mid = curr_x + (i * slot_w) + (slot_w // 2)
        d_name = get_day_hu(datetime.fromtimestamp(day_entry["dt"])).upper()[:3]
        f_val = f"{round(day_entry['main']['temp'])}°C"
        
        if i < len(forecast_icons):
            paste_icon(img, forecast_icons[i], slot_mid - (FORECAST_ICON_SIZE // 2), mid_y - 85, size=FORECAST_ICON_SIZE)
        
        nw = draw.textbbox((0, 0), d_name, font=f_fd)[2]
        vw = draw.textbbox((0, 0), f_val, font=f_fv)[2]
        draw.text((slot_mid - nw // 2, mid_y - 22), d_name, font=f_fd, fill=colors["dim"])
        draw.text((slot_mid - vw // 2, mid_y + 8), f_val, font=f_fv, fill=colors["main"])

    curr_x += SEC4_W
    draw.line([(curr_x, by + 50), (curr_x, by + bh - 50)], fill=colors["line"], width=2)

    # ── SZEKCIÓ 5: NÉVNAP ────────────────────────────────────────────────────
    curr_x += 50
    nameday_value = ", ".join(n.strip() for n in namedays)
    draw.text((curr_x, mid_y - 50), "NÉVNAP", font=f_h, fill=colors["dim"])
    draw.text((curr_x, mid_y - 10), nameday_value, font=f_n, fill=colors["main"])

    # ── DÁTUM + IDŐ ──────────────────────────────────────────────────────────
    datetime_txt = weather["now_dt"].strftime("%Y.%m.%d  %H:%M")
    dt_w = draw.textbbox((0, 0), datetime_txt, font=f_dt)[2]
    draw.text((bx + bw - dt_w - 60, by + 15), datetime_txt, font=f_dt, fill=(160, 160, 160, 200))
