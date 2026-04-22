from PIL import Image, ImageDraw, ImageFont, ImageStat
from datetime import datetime, timezone, timedelta

# ============================================================
# 4K-S HORIZONTÁLIS DESIGN - GEMINI EDITION (FINAL)
# ============================================================
WIDGET_WIDTH  = 2400
WIDGET_HEIGHT = 200
WIDGET_Y      = 100
OFFSET_LEFT   = 135
INNER_MARGIN  = 80

# Tipográfia és méretek
FONT_TEMP     = 105  # Domináns fő hőmérséklet
FONT_HEADER   = 24   # Elegáns fejléc (SZERDA, DERÜLT)
FONT_VALUE    = 36   # Adat értékek (km/h, %)
FONT_SMALL    = 34   # Érzet hőfok száma
FONT_DATETIME = 24
FONT_NAME     = 28
FONT_FORECAST_DAY = 22
FONT_FORECAST_TEMP = 32

ICON_DISPLAY_SIZE  = 160
FEEL_ICON_SIZE     = 34
WIND_ICON_SIZE     = 36
PARA_ICON_SIZE     = 36
FORECAST_ICON_SIZE = 58   
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

    # ── SZEKCIÓ 1: AKTUÁLIS (Helyrerakott feliratok és baseline) ───────────
    SEC1_W = 650 
    sec1_mid = curr_x + (SEC1_W // 2)
    
    day_txt = get_day_hu(weather["now_dt"]).upper()
    desc_txt = weather["weather_hu"].upper()
    temp_txt, feel_txt = f"{weather['temp']}°C", f"{weather['feels_like']}°C"

    t_bbox = draw.textbbox((0, 0), temp_txt, font=f_t)
    t_w, t_h = t_bbox[2], t_bbox[3]
    f_bbox = draw.textbbox((0, 0), feel_txt, font=f_s)
    f_w, f_h_text = f_bbox[2], f_bbox[3]
    
    main_w = ICON_DISPLAY_SIZE + 45 + t_w + 35 + FEEL_ICON_SIZE + 12 + f_w
    start_x = sec1_mid - (main_w // 2)

    if icon_img:
        paste_icon(img, icon_img, start_x, mid_y - ICON_DISPLAY_SIZE // 2)
    
    tx = start_x + ICON_DISPLAY_SIZE + 45
    temp_y = mid_y - (t_h // 2) + 5

    # --- FEJLÉC IGAZÍTÁSA (8 km/h magasságához) ---
    header_y = mid_y - 62 
    draw.text((tx, header_y), day_txt, font=f_h, fill=colors["dim"])
    day_w_header = draw.textbbox((0, 0), day_txt, font=f_h)[2]
    draw.text((tx + day_w_header + 30, header_y), desc_txt, font=f_h, fill=colors["dim"])

    # FŐ HŐFOK
    draw.text((tx, temp_y), temp_txt, font=f_t, fill=colors["main"])
    
    # PIXEL PERFECT BASELINE
    base_line_y = temp_y + t_h
    feel_x = tx + t_w + 35
    if feel_icon_img:
        paste_icon(img, feel_icon_img, feel_x, base_line_y - FEEL_ICON_SIZE - 5, size=FEEL_ICON_SIZE)
    draw.text((feel_x + FEEL_ICON_SIZE + 12, base_line_y - f_h_text - 3), feel_txt, font=f_s, fill=colors["dim"])

    curr_x += SEC1_W
    draw.line([(curr_x, by + 50), (curr_x, by + bh - 50)], fill=colors["line"], width=2)

    # ── SZEKCIÓ 2 & 3: ADATOK (Szél, Pára, Nap) ───────────────────────────
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

    # ── SZEKCIÓ 4: FORECAST ──────────────────────────────────────────────
    SEC4_W = 540
    slot_w = SEC4_W // 3
    for i, day_entry in enumerate(weather["forecast"]):
        slot_mid = curr_x + (i * slot_w) + (slot_w // 2)
        d_name = get_day_hu(datetime.fromtimestamp(day_entry["dt"])).upper()[:3]
        f_val = f"{round(day_entry['main']['temp'])}°C"
        
        if i < len(forecast_icons):
            paste_icon(img, forecast_icons[i], slot_mid - (FORECAST_ICON_SIZE // 2), mid_y - 88, size=FORECAST_ICON_SIZE)
        
        nw = draw.textbbox((0, 0), d_name, font=f_fd)[2]
        vw = draw.textbbox((0, 0), f_val, font=f_fv)[2]
        draw.text((slot_mid - nw // 2, mid_y - 20), d_name, font=f_fd, fill=colors["dim"])
        draw.text((slot_mid - vw // 2, mid_y + 12), f_val, font=f_fv, fill=colors["main"])

    curr_x += SEC4_W
    draw.line([(curr_x, by + 50), (curr_x, by + bh - 50)], fill=colors["line"], width=2)

    # ── SZEKCIÓ 5: NÉVNAP ──────────────────────────────────────────────────
    curr_x += 50
    nameday_value = ", ".join(n.strip().rstrip("\\") for n in namedays)
    draw.text((curr_x, mid_y - 50), "NÉVNAP", font=f_h, fill=colors["dim"])
    draw.text((curr_x, mid_y - 10), nameday_value, font=f_n, fill=colors["main"])

    # ── DÁTUM + IDŐ ────────────────────────────────────────────────────────
    datetime_txt = weather["now_dt"].strftime("%Y.%m.%d  %H:%M")
    dt_w = draw.textbbox((0, 0), datetime_txt, font=f_dt)[2]
    draw.text((bx + bw - dt_w - INNER_MARGIN, by + 15), datetime_txt, font=f_dt, fill=(160, 160, 160, 200))
