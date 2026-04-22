from PIL import Image, ImageDraw, ImageFont, ImageStat
from datetime import datetime, timezone, timedelta

# ============================================================
# 4K-S HORIZONTÁLIS DESIGN KONFIGURÁCIÓ (FIXÁLT)
# ============================================================
WIDGET_WIDTH  = 2400
WIDGET_HEIGHT = 200
WIDGET_Y      = 100
OFFSET_LEFT   = 135
INNER_MARGIN  = 80

# Betűméretek
FONT_TEMP     = 90
FONT_HEADER   = 24
FONT_LABEL    = 28
FONT_VALUE    = 36
FONT_SMALL    = 30
FONT_DATETIME = 24
FONT_NAME     = 28
FONT_FORECAST_DAY = 22
FONT_FORECAST_TEMP = 30

# Ikon méretek
ICON_DISPLAY_SIZE  = 160
FEEL_ICON_SIZE     = 36
WIND_ICON_SIZE     = 36
PARA_ICON_SIZE     = 36
FORECAST_ICON_SIZE = 44
SUN_ICON_SIZE      = 40
ICON_GAP           = 10

def find_font(bold=False):
    paths = [
        "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf"    if bold else "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for p in paths:
        import os
        if os.path.exists(p):
            return p
    return None

def get_f(size, bold=False):
    path = find_font(bold)
    if path:
        return ImageFont.truetype(path, size)
    return ImageFont.load_default()

def get_text_colors(brightness):
    if brightness > 145:
        return {
            "main": (0, 0, 0, 230),
            "dim":  (0, 0, 0, 140),
            "line": (0, 0, 0, 40),
        }
    return {
        "main": (255, 255, 255, 255),
        "dim":  (255, 255, 255, 160),
        "line": (255, 255, 255, 40),
    }

def paste_icon(img, icon_img, x, y, size=ICON_DISPLAY_SIZE):
    if icon_img is None:
        return
    resized = icon_img.resize((size, size), Image.Resampling.LANCZOS)
    img.paste(resized, (int(x), int(y)), resized)

def draw_weather_widget(img, weather, icon_img, feel_icon_img,
                        wind_icon_img, para_icon_img,
                        forecast_icons, sunrise_icon_img, sunset_icon_img,
                        namedays, tz_offset):
    from logic_weather import get_day_hu

    bx, by = OFFSET_LEFT, WIDGET_Y
    bw, bh = WIDGET_WIDTH, WIDGET_HEIGHT

    # Háttér elemzése a színekhez
    region = img.crop((bx, by, bx + bw, by + bh)).convert("L")
    colors = get_text_colors(ImageStat.Stat(region).mean[0])
    draw = ImageDraw.Draw(img)
    
    # Betűk betöltése
    f_t = get_f(FONT_TEMP, True)
    f_h = get_f(FONT_HEADER)
    f_l = get_f(FONT_LABEL)
    f_v = get_f(FONT_VALUE, True)
    f_s = get_f(FONT_SMALL)
    f_dt = get_f(FONT_DATETIME)
    f_n = get_f(FONT_NAME)
    f_fd = get_f(FONT_FORECAST_DAY)
    f_fv = get_f(FONT_FORECAST_TEMP, True)

    mid_y = int(by + (bh // 2))
    curr_x = int(bx + INNER_MARGIN)

    # ── SZEKCIÓ 1: AKTUÁLIS (Középre zárt blokk) ─────────────────────────────
    SEC1_W = 580
    sec1_center_x = curr_x + (SEC1_W // 2)
    
    day_txt = get_day_hu(weather["now_dt"]).upper()
    desc_txt = weather["weather_hu"].upper()
    temp_txt = f"{weather['temp']}°C"
    feel_txt = f"{weather['feels_like']}°C"

    temp_w = draw.textbbox((0, 0), temp_txt, font=f_t)[2]
    feel_w = draw.textbbox((0, 0), feel_txt, font=f_s)[2]
    header_full_w = draw.textbbox((0, 0), f"{day_txt}  {desc_txt}", font=f_h)[2]
    
    main_block_w = ICON_DISPLAY_SIZE + 35 + max(header_full_w, temp_w + 25 + FEEL_ICON_SIZE + feel_w)
    start_x = sec1_center_x - (main_block_w // 2)

    if icon_img:
        paste_icon(img, icon_img, start_x, mid_y - ICON_DISPLAY_SIZE // 2)
    
    tx = start_x + ICON_DISPLAY_SIZE + 35
    draw.text((tx, mid_y - 65), f"{day_txt}  {desc_txt}", font=f_h, fill=colors["dim"])
    draw.text((tx, mid_y - 25), temp_txt, font=f_t, fill=colors["main"])
    
    feel_x = tx + temp_w + 20
    if feel_icon_img:
        paste_icon(img, feel_icon_img, feel_x, mid_y + 15, size=FEEL_ICON_SIZE)
    draw.text((feel_x + FEEL_ICON_SIZE + 8, mid_y + 12), feel_txt, font=f_s, fill=colors["dim"])

    curr_x += SEC1_W
    draw.line([(curr_x, by + 40), (curr_x, by + bh - 40)], fill=colors["line"], width=2)

    # ── SZEKCIÓ 2: SZÉL & PÁRA ──────────────────────────────────────────────
    SEC2_W = 280
    sec2_center_x = curr_x + (SEC2_W // 2)
    
    wind_val, hum_val = f"{weather['wind_kmh']} km/h", f"{weather['humidity']}%"
    for val, icon, y_off in [(wind_val, wind_icon_img, -55), (hum_val, para_icon_img, 10)]:
        v_w = draw.textbbox((0, 0), val, font=f_v)[2]
        item_w = WIND_ICON_SIZE + 15 + v_w
        ix = sec2_center_x - (item_w // 2)
        if icon: paste_icon(img, icon, ix, mid_y + y_off + 5, size=WIND_ICON_SIZE)
        draw.text((ix + WIND_ICON_SIZE + 15, mid_y + y_off), val, font=f_v, fill=colors["main"])

    curr_x += SEC2_W
    draw.line([(curr_x, by + 40), (curr_x, by + bh - 40)], fill=colors["line"], width=2)

    # ── SZEKCIÓ 3: NAP ──────────────────────────────────────────────────────
    SEC3_W = 220
    sec3_center_x = curr_x + (SEC3_W // 2)
    
    for val, icon, y_off in [(weather["sunrise"], sunrise_icon_img, -55), (weather["sunset"], sunset_icon_img, 10)]:
        v_w = draw.textbbox((0, 0), val, font=f_v)[2]
        item_w = SUN_ICON_SIZE + 15 + v_w
        ix = sec3_center_x - (item_w // 2)
        if icon: paste_icon(img, icon, ix, mid_y + y_off + 2, size=SUN_ICON_SIZE)
        draw.text((ix + SUN_ICON_SIZE + 15, mid_y + y_off), val, font=f_v, fill=colors["main"])

    curr_x += SEC3_W
    draw.line([(curr_x, by + 40), (curr_x, by + bh - 40)], fill=colors["line"], width=2)

    # ── SZEKCIÓ 4: FORECAST (3 napos szimmetria) ────────────────────────────
    SEC4_W = 480
    f_offset = 15
    slot_w = SEC4_W // 3

    for i, day_entry in enumerate(weather["forecast"]):
        slot_x = curr_x + (i * slot_w) + (slot_w // 2)
        d_name = get_day_hu(datetime.fromtimestamp(day_entry["dt"])).upper()[:3]
        f_val = f"{round(day_entry['main']['temp'])}°C"
        
        if i < len(forecast_icons) and forecast_icons[i]:
            paste_icon(img, forecast_icons[i], slot_x - (FORECAST_ICON_SIZE // 2), mid_y - 75 + f_offset, size=FORECAST_ICON_SIZE)
        
        nw = draw.textbbox((0, 0), d_name, font=f_fd)[2]
        vw = draw.textbbox((0, 0), f_val, font=f_fv)[2]
        draw.text((slot_x - nw // 2, mid_y - 25 + f_offset), d_name, font=f_fd, fill=colors["dim"])
        draw.text((slot_x - vw // 2, mid_y + 5 + f_offset), f_val, font=f_fv, fill=colors["main"])

    curr_x += SEC4_W
    draw.line([(curr_x, by + 40), (curr_x, by + bh - 40)], fill=colors["line"], width=2)

    # ── SZEKCIÓ 5: NÉVNAP ────────────────────────────────────────────────────
    curr_x += 45
    nameday_value = ", ".join(n.strip() for n in namedays)
    draw.text((curr_x, mid_y - 45), "NÉVNAP", font=f_l, fill=colors["dim"])
    draw.text((curr_x, mid_y - 5), nameday_value, font=f_n, fill=colors["main"])

    # ── DÁTUM + IDŐ ──────────────────────────────────────────────────────────
    datetime_txt = weather["now_dt"].strftime("%y.%m.%d  %H:%M")
    dt_w = draw.textbbox((0, 0), datetime_txt, font=f_dt)[2]
    draw.text((bx + bw - dt_w - 20, by + 15), datetime_txt, font=f_dt, fill=(160, 160, 160, 200))
