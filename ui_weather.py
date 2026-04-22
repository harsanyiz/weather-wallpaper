from PIL import Image, ImageDraw, ImageFont, ImageStat
from datetime import datetime

# --- KONFIGURÁCIÓ & MÉRETEK (4K HORIZONTÁLIS) ---
WIDGET_WIDTH, WIDGET_HEIGHT, WIDGET_Y, OFFSET_LEFT, INNER_MARGIN = 2400, 200, 100, 135, 80

# XIAOMI STYLE - Modern színek és betűméretek
FONT_TEMP = 105
FONT_HEADER = 24
FONT_VALUE = 36
FONT_SMALL = 30
FONT_DATETIME = 22
FONT_NAME = 28
FONT_FORECAST_DAY = 22
FONT_FORECAST_TEMP = 32

# Ikonméretek (változatlanul hagyva a stabil elhelyezéshez)
ICON_DISPLAY_SIZE = 160
WIND_ICON_SIZE = 36
PARA_ICON_SIZE = 36
FORECAST_ICON_SIZE = 50
SUN_ICON_SIZE = 40
SMALL_ICON_SIZE = 36

def find_font(bold=False):
    import os
    fonts = [
        "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for p in fonts:
        if os.path.exists(p):
            return p
    return None

def get_f(size, bold=False):
    path = find_font(bold)
    return ImageFont.truetype(path, size) if path else ImageFont.load_default()

def paste_icon(img, icon_img, x, y, size=ICON_DISPLAY_SIZE):
    if icon_img:
        resized = icon_img.resize((size, size), Image.Resampling.LANCZOS)
        img.paste(resized, (int(x), int(y)), resized)

def draw_weather_widget(img, weather, icon_img, feel_icon_img, rainq_icon_img, 
                        wind1_icon_img, para_icon_img, forecast_icons, 
                        sunrise_icon_img, sunset_icon_img, namedays, tz_offset):
    from logic_weather import get_day_hu
    
    bx, by, bw, bh = OFFSET_LEFT, WIDGET_Y, WIDGET_WIDTH, WIDGET_HEIGHT
    
    # Automatikus sötét/világos mód a háttér alapján - XIAOMI színekkel
    brightness = ImageStat.Stat(img.crop((bx, by, bx + bw, by + bh)).convert("L")).mean[0]
    
    if brightness > 145:
        # Világos mód (Xiaomi fehér kártya)
        colors = {
            "main": (30, 30, 45, 255),      # Sötétszürke szöveg
            "dim": (100, 100, 120, 220),    # Halvány szürke
            "line": (0, 0, 0, 20),          # Áttetsző fekete vonal
            "bg": (255, 255, 255, 230),     # Fehér háttér
            "accent": (0, 150, 210, 255)    # Xiaomi kék akcentus
        }
    else:
        # Sötét mód (Xiaomi sötét kártya)
        colors = {
            "main": (255, 255, 255, 255),   # Fehér szöveg
            "dim": (180, 180, 200, 200),    # Halvány szürkés-fehér
            "line": (255, 255, 255, 25),    # Áttetsző fehér vonal
            "bg": (30, 30, 45, 210),        # Sötét üveghátlap
            "accent": (0, 200, 255, 255)    # Világos kék akcentus
        }
    
    draw = ImageDraw.Draw(img)
    
    # Lekerekített háttér rajzolása (Xiaomi stílus)
    corner_radius = 28
    draw.rectangle([bx + corner_radius, by, bx + bw - corner_radius, by + bh], fill=colors["bg"])
    draw.rectangle([bx, by + corner_radius, bx + bw, by + bh - corner_radius], fill=colors["bg"])
    draw.pieslice([bx, by, bx + corner_radius * 2, by + corner_radius * 2], 180, 270, fill=colors["bg"])
    draw.pieslice([bx + bw - corner_radius * 2, by, bx + bw, by + corner_radius * 2], 270, 360, fill=colors["bg"])
    draw.pieslice([bx, by + bh - corner_radius * 2, bx + corner_radius * 2, by + bh], 90, 180, fill=colors["bg"])
    draw.pieslice([bx + bw - corner_radius * 2, by + bh - corner_radius * 2, bx + bw, by + bh], 0, 90, fill=colors["bg"])
    
    mid_y = by + (bh // 2)
    curr_x = bx + INNER_MARGIN
    
    f_t = get_f(FONT_TEMP, True)
    f_h = get_f(FONT_HEADER)
    f_v = get_f(FONT_VALUE, True)
    f_s = get_f(FONT_SMALL)
    f_dt = get_f(FONT_DATETIME)
    f_n = get_f(FONT_NAME)
    f_fd = get_f(FONT_FORECAST_DAY)
    f_fv = get_f(FONT_FORECAST_TEMP, True)

    # ========== 1. AKTUÁLIS BLOKK (HŐFOK + ESŐ/ÉRZET EGYMÁS FELETT) ==========
    SEC1_W = 820
    temp_txt = f"{weather['temp']}°C"
    feel_txt = f"{weather['feels_like']}°C"
    rain_txt = f"{weather.get('pop', 0)}%"
    
    t_bbox = draw.textbbox((0, 0), temp_txt, font=f_t)
    t_w = t_bbox[2] - t_bbox[0]
    
    # Fő ikon és Hőmérséklet
    main_content_w = ICON_DISPLAY_SIZE + 40 + t_w + 60 + 110
    start_x = (curr_x + SEC1_W // 2) - (main_content_w // 2)
    
    paste_icon(img, icon_img, start_x, mid_y - ICON_DISPLAY_SIZE // 2)
    tx = start_x + ICON_DISPLAY_SIZE + 40
    ty = mid_y - (t_bbox[3] // 2) + 5
    
    # Fejléc (NAP + ÁLLAPOT)
    day_str = get_day_hu(weather["now_dt"]).upper()
    draw.text((tx + 20, mid_y - 65), day_str, font=f_h, fill=colors["dim"])
    day_w = draw.textbbox((0, 0), day_str, font=f_h)[2]
    draw.text((tx + 20 + day_w + 30, mid_y - 65), weather["weather_hu"].upper(), font=f_h, fill=colors["accent"])
    
    # Fő Hőfok
    draw.text((tx, ty), temp_txt, font=f_t, fill=colors["main"])
    
    # INFÓ OSZLOP (Eső esélye fent, Érzet lent)
    info_x = tx + t_w + 60
    
    # Eső (Fent)
    if rainq_icon_img:
        paste_icon(img, rainq_icon_img, info_x, mid_y - 42, size=42)
    draw.text((info_x + 52, mid_y - 42), rain_txt, font=f_s, fill=colors["dim"])
    
    # Érzet (Lent)
    if feel_icon_img:
        paste_icon(img, feel_icon_img, info_x + 4, mid_y + 8, size=36)
    draw.text((info_x + 52, mid_y + 8), feel_txt, font=f_s, fill=colors["dim"])
    
    curr_x += SEC1_W
    draw.line([(curr_x, by + 50), (curr_x, by + bh - 50)], fill=colors["line"], width=2)

    # ========== 2. SZÉL & PÁRA ==========
    SEC2_W = 300
    ix = curr_x + 70
    
    # Szél
    if wind1_icon_img:
        paste_icon(img, wind1_icon_img, ix, mid_y - 68 + 4, size=WIND_ICON_SIZE)
    draw.text((ix + 58, mid_y - 68), f"{weather['wind_kmh']} km/h", font=f_v, fill=colors["main"])
    draw.text((ix + 58, mid_y - 45), "SZÉL", font=f_s, fill=colors["dim"])
    
    # Páratartalom
    if para_icon_img:
        paste_icon(img, para_icon_img, ix, mid_y + 12 + 4, size=PARA_ICON_SIZE)
    draw.text((ix + 58, mid_y + 12), f"{weather['humidity']}%", font=f_v, fill=colors["main"])
    draw.text((ix + 58, mid_y + 35), "PÁRA", font=f_s, fill=colors["dim"])
    
    curr_x += SEC2_W
    draw.line([(curr_x, by + 50), (curr_x, by + bh - 50)], fill=colors["line"], width=2)

    # ========== 3. NAPKELTE / NAPNYUGTA ==========
    SEC3_W = 260
    sx = curr_x + 70
    
    # Napkelte
    if sunrise_icon_img:
        paste_icon(img, sunrise_icon_img, sx, mid_y - 65 + 6, size=SUN_ICON_SIZE)
    draw.text((sx + 58, mid_y - 65), weather['sunrise'], font=f_v, fill=colors["main"])
    draw.text((sx + 58, mid_y - 42), "NAPkelte", font=f_s, fill=colors["dim"])
    
    # Napnyugta
    if sunset_icon_img:
        paste_icon(img, sunset_icon_img, sx, mid_y + 10 + 6, size=SUN_ICON_SIZE)
    draw.text((sx + 58, mid_y + 10), weather['sunset'], font=f_v, fill=colors["main"])
    draw.text((sx + 58, mid_y + 33), "NAPnyugta", font=f_s, fill=colors["dim"])
    
    curr_x += SEC3_W
    draw.line([(curr_x, by + 50), (curr_x, by + bh - 50)], fill=colors["line"], width=2)

    # ========== 4. ELŐREJELZÉS (3 NAP) ==========
    SEC4_W = 540
    slot_w = 180
    
    for i, day_entry in enumerate(weather["forecast"]):
        sm = curr_x + (i * slot_w) + (slot_w // 2)
        dn = get_day_hu(datetime.fromtimestamp(day_entry["dt"])).upper()[:3]
        fv = f"{round(day_entry['main']['temp'])}°C"
        
        if i < len(forecast_icons):
            paste_icon(img, forecast_icons[i], sm - 25, mid_y - 75, size=50)
        
        draw.text((sm - draw.textbbox((0, 0), dn, font=f_fd)[2] // 2, mid_y - 15), dn, font=f_fd, fill=colors["dim"])
        draw.text((sm - draw.textbbox((0, 0), fv, font=f_fv)[2] // 2, mid_y + 15), fv, font=f_fv, fill=colors["main"])
        
        # Eső esély az előrejelzésben (Xiaomi extra infó)
        pop_val = day_entry.get('pop', 0)
        if pop_val > 0:
            pop_txt = f"{round(pop_val * 100)}%"
            draw.text((sm - draw.textbbox((0, 0), pop_txt, font=f_s)[2] // 2, mid_y + 45), pop_txt, font=f_s, fill=colors["dim"])
    
    curr_x += SEC4_W
    draw.line([(curr_x, by + 50), (curr_x, by + bh - 50)], fill=colors["line"], width=2)

    # ========== 5. NÉVNAP & IDŐ ==========
    draw.text((curr_x + 50, mid_y - 50), "NÉVNAP", font=f_h, fill=colors["dim"])
    draw.text((curr_x + 50, mid_y - 2), ", ".join(namedays), font=f_n, fill=colors["main"])
    
    # Frissítési idő a jobb felső sarokba
    dt_txt = weather["now_dt"].strftime("%Y.%m.%d  %H:%M")
    draw.text((bx + bw - draw.textbbox((0, 0), dt_txt, font=f_dt)[2] - 20, by + 15), dt_txt, font=f_dt, fill=colors["dim"])
