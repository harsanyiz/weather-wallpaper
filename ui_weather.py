from PIL import Image, ImageDraw, ImageFont, ImageStat
from datetime import datetime, timezone, timedelta

# ============================================================
# 4K-S HORIZONTÁLIS DESIGN - GEMINI "ULTIMATE PIXEL" EDITION
# FINAL INTEGRATED CODE - 2026.04.22.
# ============================================================
WIDGET_WIDTH  = 2400
WIDGET_HEIGHT = 200
WIDGET_Y      = 100
OFFSET_LEFT   = 135
INNER_MARGIN  = 80

# Tipográfia - Arányok a 4K felbontáshoz
FONT_TEMP     = 105
FONT_HEADER   = 24
FONT_VALUE    = 36
FONT_SMALL    = 34
FONT_DATETIME = 24
FONT_NAME     = 28
FONT_FORECAST_DAY = 22
FONT_FORECAST_TEMP = 32

# Ikon méretek - Tűpontos skálázás
ICON_DISPLAY_SIZE  = 160
FEEL_ICON_SIZE     = 34
WIND_ICON_SIZE     = 36
PARA_ICON_SIZE     = 36
FORECAST_ICON_SIZE = 50   # Kisebb, hogy ne érjen a feliratokhoz
SUN_ICON_SIZE      = 40

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
    # Automatikus kontraszt a háttérhez (sötét vs világos mód)
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

    # Régió elemzése a színválasztáshoz
    bx, by, bw, bh = OFFSET_LEFT, WIDGET_Y, WIDGET_WIDTH, WIDGET_HEIGHT
    region = img.crop((bx, by, bx + bw, by + bh)).convert("L")
    colors = get_text_colors(ImageStat.Stat(region).mean[0])
    draw = ImageDraw.Draw(img)
    
    # Fontok betöltése
    f_t, f_h, f_v, f_s = get_f(FONT_TEMP, True), get_f(FONT_HEADER), get_f(FONT_VALUE, True), get_f(FONT_SMALL)
    f_dt, f_n, f_fd, f_fv = get_f(FONT_DATETIME), get_f(FONT_NAME), get_f(FONT_FORECAST_DAY), get_f(FONT_FORECAST_TEMP, True)

    mid_y = by + (bh // 2)
    curr_x = bx + INNER_MARGIN

    # ── SZEKCIÓ 1: AKTUÁLIS (Hőfok + Fő ikon + Fejléc) ───────────────────────────
    SEC1_W = 720 
    sec1_mid = curr_x + (SEC1_W // 2)
    
    day_txt = get_day_hu(weather["now_dt"]).upper()
    desc_txt = weather["weather_hu"].upper()
    temp_txt, feel_txt = f"{weather['temp']}°C", f"{weather['feels_like']}°C"

    t_bbox = draw.textbbox((0, 0), temp_txt, font=f_t)
    t_w, t_h = t_bbox[2], t_bbox[3]
    
    # Csoportszélesség kiszámítása a középre igazításhoz
    main_w = ICON_DISPLAY_SIZE + 45 + t_w + 35 + FEEL_ICON_SIZE + 12 + draw.textbbox((0, 0), feel_txt, font=f_s)[2]
    start_x = sec1_mid - (main_w // 2)

    # Fő ikon
    if icon_img:
        paste_icon(img, icon_img, start_x, mid_y - ICON_DISPLAY_SIZE // 2)
    
    tx = start_x + ICON_DISPLAY_SIZE + 45
    temp_y = mid_y - (t_h // 2) + 5

    # FEJLÉC IGAZÍTÁSA (+25px optikai eltolás jobbra a nagy számtól)
    header_y = mid_y - 65 
    header_x = tx + 25 
    draw.text((header_x, header_y), day_txt, font=f_h, fill=colors["dim"])
    day_w_header = draw.textbbox((0, 0), day_txt, font=f_h)[2]
    draw.text((header_x + day_w_header + 35, header_y), desc_txt, font=f_h, fill=colors["dim"])

    # Fő hőfok rajzolása
    draw.text((tx, temp_y), temp_txt, font=f_t, fill=colors["main"])
    
    # Érzet hőfok (Feel-like) igazítása a hőfok aljához
    base_line_y = temp_y + t_h
    feel_x = tx + t_w + 35
    if feel_icon_img:
        paste_icon(img, feel_icon_img, feel_x, base_line_y - FEEL_ICON_SIZE - 5, size=FEEL_ICON_SIZE)
    draw.text((feel_x + FEEL_ICON_SIZE + 12, base_line_y - draw.textbbox((0, 0), feel_txt, font=f_s)[3] - 3), feel_txt, font=f_s, fill=colors["dim"])

    curr_x += SEC1_W
    draw.line([(curr_x, by + 50), (curr_x, by + bh - 50)], fill=colors["line"], width=2)

    # ── SZEKCIÓ 2: ADATOK (Szél és Pára - Tűpontos oszlop) ──────────────────
    SEC2_W = 300 
    sec2_mid = curr_x + (SEC2_W // 2)
    icon_x_fix = sec2_mid - 65 # Fix X tengely az ikonoknak

    # Szél (Felső sor)
    y_pos_wind = mid_y - 68
    if wind_icon_img:
        paste_icon(img, wind_icon_img, icon_x_fix, y_pos_wind + 8, size=WIND_ICON_SIZE)
    draw.text((icon_x_fix + WIND_ICON_SIZE + 20, y_pos_wind), f"{weather['wind_kmh']} km/h", font=f_v, fill=colors["main"])

    # Pára (Alsó sor)
    y_pos_para = mid_y + 12
    if para_icon_img:
        paste_icon(img, para_icon_img, icon_x_fix, y_pos_para + 8, size=PARA_ICON_SIZE)
    draw.text((icon_x_fix + PARA_ICON_SIZE + 20, y_pos_para), f"{weather['humidity']}%", font=f_v, fill=colors["main"])

    curr_x += SEC2_W
    draw.line([(curr_x, by + 50), (curr_x, by + bh - 50)], fill=colors["line"], width=2)

    # ── SZEKCIÓ 3: NAPKELTE / NAPNYUGTA ───────────────────────────────────────
    SEC3_W = 260 
    sec3_mid = curr_x + (SEC3_W // 2)
    icon_x_sun = sec3_mid - 45
    
    # Napkelte
    if sunrise_icon_img:
        paste_icon(img, sunrise_icon_img, icon_x_sun, mid_y - 65 + 8, size=SUN_ICON_SIZE)
    draw.text((icon_x_sun + SUN_ICON_SIZE + 15, mid_y - 65), weather['sunrise'], font=f_v, fill=colors["main"])
    
    # Napnyugta
    if sunset_icon_img:
        paste_icon(img, sunset_icon_img, icon_x_sun, mid_y + 10 + 8, size=SUN_ICON_SIZE)
    draw.text((icon_x_sun + SUN_ICON_SIZE + 15, mid_y + 10), weather['sunset'], font=f_v, fill=colors["main"])

    curr_x += SEC3_W
    draw.line([(curr_x, by + 50), (curr_x, by + bh - 50)], fill=colors["line"], width=2)

    # ── SZEKCIÓ 4: ELŐREJELZÉS (Levegős, nem lóg ki) ───────────────────────────
    SEC4_W = 540
    slot_w = SEC4_W // 3
    for i, day_entry in enumerate(weather["forecast"]):
        slot_mid = curr_x + (i * slot_w) + (slot_w // 2)
        d_name = get_day_hu(datetime.fromtimestamp(day_entry["dt"])).upper()[:3]
        f_val = f"{round(day_entry['main']['temp'])}°C"
        
        if i < len(forecast_icons):
            # Ikon elhelyezése feljebb, kisebb méretben (50px) a zsúfoltság ellen
            paste_icon(img, forecast_icons[i], slot_mid - 25, mid_y - 98, size=50)
        
        # Nap neve és hőfoka szimmetrikusan
        draw.text((slot_mid - draw.textbbox((0, 0), d_name, font=f_fd)[2] // 2, mid_y - 15), d_name, font=f_fd, fill=colors["dim"])
        draw.text((slot_mid - draw.textbbox((0, 0), f_val, font=f_fv)[2] // 2, mid_y + 15), f_val, font=f_fv, fill=colors["main"])

    curr_x += SEC4_W
    draw.line([(curr_x, by + 50), (curr_x, by + bh - 50)], fill=colors["line"], width=2)

    # ── SZEKCIÓ 5: NÉVNAP ÉS DÁTUM (Jobb szél) ─────────────────────────────────
    curr_x += 50
    nameday_value = ", ".join(n.strip().rstrip("\\") for n in namedays)
    draw.text((curr_x, mid_y - 50), "NÉVNAP", font=f_h, fill=colors["dim"])
    draw.text((curr_x, mid_y - 10), nameday_value, font=f_n, fill=colors["main"])

    # Dátum azonosítása a jobb felső sarokban
    datetime_txt = weather["now_dt"].strftime("%Y.%m.%d  %H:%M")
    dt_w = draw.textbbox((0, 0), datetime_txt, font=f_dt)[2]
    draw.text((bx + bw - dt_w - INNER_MARGIN, by + 15), datetime_txt, font=f_dt, fill=(160, 160, 160, 200))
