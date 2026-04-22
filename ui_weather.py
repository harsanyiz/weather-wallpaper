from PIL import Image, ImageDraw, ImageFont, ImageStat
from datetime import datetime

# --- KONFIGURÁCIÓ & MÉRETEK (4K HORIZONTÁLIS) - XIAOMI STYLE ---
WIDGET_WIDTH, WIDGET_HEIGHT, WIDGET_Y = 2400, 240, 60
OFFSET_LEFT, INNER_MARGIN = 80, 50

# XIAOMI színek és stílusok
GLASS_BG = (255, 255, 255, 35)          # Áttetsző fehér alap
GLASS_BORDER = (255, 255, 255, 80)      # Világosabb keret
GLASS_BLUR_BG = (30, 30, 45, 180)       # Sötét üveghátlap éjszakára

# Modern színpaletta
COLOR_ACCENT = (0, 200, 255, 255)       # Cian akcentus
COLOR_TEMP = (255, 255, 255, 255)       # Fehér hőmérséklet
COLOR_LABEL = (200, 200, 210, 200)      # Halvány szürkés-fehér
COLOR_VALUE = (255, 255, 255, 220)      # Értékek
COLOR_DIVIDER = (255, 255, 255, 25)     # Elválasztó vonalak

# Betűméretek
FONT_TEMP = 96
FONT_UNIT = 36
FONT_HEADER = 22
FONT_VALUE = 32
FONT_SMALL = 26
FONT_DATETIME = 20
FONT_NAME = 24
FONT_FORECAST_DAY = 22
FONT_FORECAST_TEMP = 28

# Ikonméretek
ICON_DISPLAY_SIZE = 120
WIND_ICON_SIZE = 32
PARA_ICON_SIZE = 32
FORECAST_ICON_SIZE = 44
SUN_ICON_SIZE = 32
SMALL_ICON_SIZE = 36

def find_font(bold=False):
    import os
    fonts = [
        "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/System/Library/Fonts/SF-Pro-Text-Regular.otf" if not bold else "/System/Library/Fonts/SF-Pro-Text-Bold.otf"
    ]
    for p in fonts:
        if os.path.exists(p):
            return p
    return None

def get_f(size, bold=False):
    path = find_font(bold)
    return ImageFont.truetype(path, size) if path else ImageFont.load_default()

def paste_icon(img, icon_img, x, y, size=ICON_DISPLAY_SIZE, opacity=255):
    if icon_img:
        resized = icon_img.resize((size, size), Image.Resampling.LANCZOS)
        if opacity < 255:
            alpha = resized.split()[3]
            alpha = alpha.point(lambda p: p * opacity // 255)
            resized.putalpha(alpha)
        img.paste(resized, (int(x), int(y)), resized)

def draw_rounded_rect(draw, xy, radius, fill, outline=None, width=1):
    """Lekerekített téglalap rajzolása"""
    x1, y1, x2, y2 = xy
    draw.rectangle([x1+radius, y1, x2-radius, y2], fill=fill)
    draw.rectangle([x1, y1+radius, x2, y2-radius], fill=fill)
    draw.pieslice([x1, y1, x1+radius*2, y1+radius*2], 180, 270, fill=fill)
    draw.pieslice([x2-radius*2, y1, x2, y1+radius*2], 270, 360, fill=fill)
    draw.pieslice([x1, y2-radius*2, x1+radius*2, y2], 90, 180, fill=fill)
    draw.pieslice([x2-radius*2, y2-radius*2, x2, y2], 0, 90, fill=fill)
    
    if outline:
        draw.arc([x1, y1, x1+radius*2, y1+radius*2], 180, 270, fill=outline, width=width)
        draw.arc([x2-radius*2, y1, x2, y1+radius*2], 270, 360, fill=outline, width=width)
        draw.arc([x1, y2-radius*2, x1+radius*2, y2], 90, 180, fill=outline, width=width)
        draw.arc([x2-radius*2, y2-radius*2, x2, y2], 0, 90, fill=outline, width=width)
        draw.line([x1+radius, y1, x2-radius, y1], fill=outline, width=width)
        draw.line([x1+radius, y2, x2-radius, y2], fill=outline, width=width)
        draw.line([x1, y1+radius, x1, y2-radius], fill=outline, width=width)
        draw.line([x2, y1+radius, x2, y2-radius], fill=outline, width=width)

def draw_weather_widget(img, weather, icon_img, feel_icon_img, rainq_icon_img, 
                        wind1_icon_img, para_icon_img, forecast_icons, 
                        sunrise_icon_img, sunset_icon_img, namedays, tz_offset):
    from logic_weather import get_day_hu
    
    bx, by, bw, bh = OFFSET_LEFT, WIDGET_Y, WIDGET_WIDTH, WIDGET_HEIGHT
    
    # Automatikus világos/sötét mód
    brightness = ImageStat.Stat(img.crop((bx, by, bx + bw, by + bh)).convert("L")).mean[0]
    is_dark = brightness < 145
    
    # Színek dinamikusan
    if is_dark:
        bg_color = GLASS_BLUR_BG
        text_primary = (255, 255, 255, 255)
        text_secondary = (180, 180, 200, 200)
        accent_color = (0, 200, 255, 255)
        divider_color = (255, 255, 255, 20)
    else:
        bg_color = (255, 255, 255, 200)
        text_primary = (30, 30, 45, 255)
        text_secondary = (100, 100, 120, 220)
        accent_color = (0, 150, 210, 255)
        divider_color = (0, 0, 0, 15)
    
    draw = ImageDraw.Draw(img)
    
    # Üveghátlap lekerekített doboz
    draw_rounded_rect(draw, [bx, by, bx + bw, by + bh], 24, bg_color, outline=divider_color, width=1)
    
    mid_y = by + (bh // 2)
    curr_x = bx + INNER_MARGIN
    
    # Betűtípusok
    f_temp = get_f(FONT_TEMP, True)
    f_unit = get_f(FONT_UNIT, False)
    f_header = get_f(FONT_HEADER, True)
    f_value = get_f(FONT_VALUE, True)
    f_small = get_f(FONT_SMALL, False)
    f_dt = get_f(FONT_DATETIME, False)
    f_name = get_f(FONT_NAME, False)
    f_fday = get_f(FONT_FORECAST_DAY, True)
    f_ftemp = get_f(FONT_FORECAST_TEMP, True)
    
    # ========== 1. BAL OLDAL - NAGY IDŐJÁRÁS IKON + HŐFOK ==========
    SEC1_W = 500
    
    # Fő időjárás ikon
    paste_icon(img, icon_img, curr_x, mid_y - ICON_DISPLAY_SIZE//2, size=ICON_DISPLAY_SIZE)
    icon_right = curr_x + ICON_DISPLAY_SIZE + 25
    
    # Hőmérséklet nagyban
    temp_str = f"{weather['temp']}"
    temp_bbox = draw.textbbox((0, 0), temp_str, font=f_temp)
    temp_w = temp_bbox[2] - temp_bbox[0]
    
    draw.text((icon_right, mid_y - 50), temp_str, font=f_temp, fill=text_primary)
    draw.text((icon_right + temp_w + 5, mid_y - 42), "°C", font=f_unit, fill=text_secondary)
    
    # Időjárás állapot szöveggel
    draw.text((icon_right, mid_y - 8), weather["weather_hu"].upper(), font=f_header, fill=accent_color)
    
    curr_x += SEC1_W
    draw.line([(curr_x, by + 15), (curr_x, by + bh - 15)], fill=divider_color, width=1)
    
    # ========== 2. KÖZÉPSŐ BLOKK - ÉRZET, SZÉL, PÁRA ==========
    SEC2_W = 440
    curr_x += 30
    
    # Érzet
    if feel_icon_img:
        paste_icon(img, feel_icon_img, curr_x, mid_y - 40, size=SMALL_ICON_SIZE)
    draw.text((curr_x + SMALL_ICON_SIZE + 12, mid_y - 40), "ÉRZET", font=f_small, fill=text_secondary)
    draw.text((curr_x + SMALL_ICON_SIZE + 12, mid_y - 12), f"{weather['feels_like']}°C", font=f_value, fill=text_primary)
    
    # Szél
    y_wind = mid_y + 15
    if wind1_icon_img:
        paste_icon(img, wind1_icon_img, curr_x, y_wind - 15, size=WIND_ICON_SIZE)
    draw.text((curr_x + WIND_ICON_SIZE + 12, y_wind - 18), "SZÉL", font=f_small, fill=text_secondary)
    draw.text((curr_x + WIND_ICON_SIZE + 12, y_wind + 5), f"{weather['wind_kmh']} km/h", font=f_value, fill=text_primary)
    
    # Páratartalom
    curr_x += 170
    if para_icon_img:
        paste_icon(img, para_icon_img, curr_x, mid_y - 40, size=SMALL_ICON_SIZE)
    draw.text((curr_x + SMALL_ICON_SIZE + 12, mid_y - 40), "PÁRA", font=f_small, fill=text_secondary)
    draw.text((curr_x + SMALL_ICON_SIZE + 12, mid_y - 12), f"{weather['humidity']}%", font=f_value, fill=text_primary)
    
    # Eső esély
    if rainq_icon_img:
        paste_icon(img, rainq_icon_img, curr_x, mid_y + 15, size=SMALL_ICON_SIZE)
    draw.text((curr_x + SMALL_ICON_SIZE + 12, mid_y + 10), "ESŐ", font=f_small, fill=text_secondary)
    draw.text((curr_x + SMALL_ICON_SIZE + 12, mid_y + 38), f"{weather.get('pop', 0)}%", font=f_value, fill=text_primary)
    
    curr_x = bx + SEC1_W + SEC2_W + 30
    draw.line([(curr_x, by + 15), (curr_x, by + bh - 15)], fill=divider_color, width=1)
    
    # ========== 3. NAPKELTE / NAPNYUGTA ==========
    SEC3_W = 300
    curr_x += 30
    
    # Napkelte
    if sunrise_icon_img:
        paste_icon(img, sunrise_icon_img, curr_x, mid_y - 30, size=SUN_ICON_SIZE)
    draw.text((curr_x + SUN_ICON_SIZE + 12, mid_y - 35), "NAPkelte", font=f_small, fill=text_secondary)
    draw.text((curr_x + SUN_ICON_SIZE + 12, mid_y - 10), weather['sunrise'], font=f_value, fill=text_primary)
    
    # Napnyugta
    y_sunset = mid_y + 20
    if sunset_icon_img:
        paste_icon(img, sunset_icon_img, curr_x, y_sunset - 15, size=SUN_ICON_SIZE)
    draw.text((curr_x + SUN_ICON_SIZE + 12, y_sunset - 20), "NAPnyugta", font=f_small, fill=text_secondary)
    draw.text((curr_x + SUN_ICON_SIZE + 12, y_sunset + 5), weather['sunset'], font=f_value, fill=text_primary)
    
    curr_x += SEC3_W
    draw.line([(curr_x, by + 15), (curr_x, by + bh - 15)], fill=divider_color, width=1)
    
    # ========== 4. ELŐREJELZÉS (3 NAP) ==========
    SEC4_W = 580
    curr_x += 20
    slot_w = 180
    slot_gap = 15
    
    for i, day_entry in enumerate(weather["forecast"]):
        slot_x = curr_x + i * (slot_w + slot_gap)
        slot_center = slot_x + slot_w // 2
        
        # Nap neve
        day_name = get_day_hu(datetime.fromtimestamp(day_entry["dt"])).upper()[:3]
        draw.text((slot_center - draw.textbbox((0, 0), day_name, font=f_fday)[2] // 2, 
                   mid_y - 45), day_name, font=f_fday, fill=accent_color)
        
        # Ikon
        if i < len(forecast_icons) and forecast_icons[i]:
            paste_icon(img, forecast_icons[i], slot_center - FORECAST_ICON_SIZE//2, 
                      mid_y - 30, size=FORECAST_ICON_SIZE)
        
        # Hőmérséklet
        temp_f = f"{round(day_entry['main']['temp'])}°"
        draw.text((slot_center - draw.textbbox((0, 0), temp_f, font=f_ftemp)[2] // 2, 
                   mid_y + 20), temp_f, font=f_ftemp, fill=text_primary)
        
        # Eső esély ha van
        pop = day_entry.get('pop', 0)
        if pop > 0:
            pop_str = f"{round(pop * 100)}%"
            pop_bbox = draw.textbbox((0, 0), pop_str, font=f_small)
            draw.text((slot_center - pop_bbox[2] // 2, mid_y + 50), pop_str, 
                     font=f_small, fill=text_secondary)
    
    # ========== 5. JOBB SZÉL - NÉVNAP + DÁTUM ==========
    curr_x += SEC4_W + 20
    draw.line([(curr_x, by + 15), (curr_x, by + bh - 15)], fill=divider_color, width=1)
    curr_x += 25
    
    # Névnap fejléc
    draw.text((curr_x, mid_y - 40), "NÉVNAP", font=f_header, fill=text_secondary)
    
    # Névnapok listája
    names_str = ", ".join(namedays[:3])  # Max 3 névnap
    draw.text((curr_x, mid_y - 10), names_str, font=f_name, fill=text_primary)
    
    # Dátum és idő (Xiaomi stílusban, lentebb)
    dt_str = weather["now_dt"].strftime("%Y.%m.%d  •  %H:%M")
    draw.text((curr_x, mid_y + 45), dt_str, font=f_dt, fill=text_secondary)
