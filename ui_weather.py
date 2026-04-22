from PIL import Image, ImageDraw, ImageFont, ImageStat
from datetime import datetime

# --- KONFIGURÁCIÓ & MÉRETEK (4K HORIZONTÁLIS) - LUXUS KÍNAI EV STYLE ---
WIDGET_WIDTH, WIDGET_HEIGHT, WIDGET_Y, OFFSET_LEFT, INNER_MARGIN = 2400, 200, 100, 135, 80
FONT_TEMP, FONT_HEADER, FONT_VALUE, FONT_SMALL, FONT_DATETIME, FONT_NAME = 105, 24, 36, 30, 22, 28
FONT_FORECAST_DAY, FONT_FORECAST_TEMP = 22, 32
ICON_DISPLAY_SIZE, WIND_ICON_SIZE, PARA_ICON_SIZE, FORECAST_ICON_SIZE, SUN_ICON_SIZE = 160, 36, 36, 50, 40

def find_font(bold=False):
    for p in ["/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]:
        import os
        if os.path.exists(p): return p
    return None

def get_f(size, bold=False):
    path = find_font(bold)
    return ImageFont.truetype(path, size) if path else ImageFont.load_default()

def paste_icon(img, icon_img, x, y, size=ICON_DISPLAY_SIZE):
    if icon_img:
        resized = icon_img.resize((size, size), Image.Resampling.LANCZOS)
        img.paste(resized, (int(x), int(y)), resized)

def draw_rounded_rect(draw, xy, radius, fill, outline=None, outline_width=1):
    x1, y1, x2, y2 = xy
    draw.rectangle([x1+radius, y1, x2-radius, y2], fill=fill)
    draw.rectangle([x1, y1+radius, x2, y2-radius], fill=fill)
    draw.pieslice([x1, y1, x1+radius*2, y1+radius*2], 180, 270, fill=fill)
    draw.pieslice([x2-radius*2, y1, x2, y1+radius*2], 270, 360, fill=fill)
    draw.pieslice([x1, y2-radius*2, x1+radius*2, y2], 90, 180, fill=fill)
    draw.pieslice([x2-radius*2, y2-radius*2, x2, y2], 0, 90, fill=fill)
    if outline:
        draw.arc([x1, y1, x1+radius*2, y1+radius*2], 180, 270, fill=outline, width=outline_width)
        draw.arc([x2-radius*2, y1, x2, y1+radius*2], 270, 360, fill=outline, width=outline_width)
        draw.arc([x1, y2-radius*2, x1+radius*2, y2], 90, 180, fill=outline, width=outline_width)
        draw.arc([x2-radius*2, y2-radius*2, x2, y2], 0, 90, fill=outline, width=outline_width)
        draw.line([x1+radius, y1, x2-radius, y1], fill=outline, width=outline_width)
        draw.line([x1+radius, y2, x2-radius, y2], fill=outline, width=outline_width)
        draw.line([x1, y1+radius, x1, y2-radius], fill=outline, width=outline_width)
        draw.line([x2, y1+radius, x2, y2-radius], fill=outline, width=outline_width)

def draw_weather_widget(img, weather, icon_img, feel_icon_img, rainq_icon_img, wind1_icon_img, para_icon_img, forecast_icons, sunrise_icon_img, sunset_icon_img, namedays, tz_offset):
    from logic_weather import get_day_hu
    bx, by, bw, bh = OFFSET_LEFT, WIDGET_Y, WIDGET_WIDTH, WIDGET_HEIGHT
    
    # Automatikus sötét/világos mód - LUXUS KÍNAI EV színek
    brightness = ImageStat.Stat(img.crop((bx, by, bx + bw, by + bh)).convert("L")).mean[0]
    
    if brightness > 145:
        # Világos mód - prémium fehér/arany
        colors = {
            "main": (20, 20, 35, 255),      # Mély sötétkék szöveg
            "dim": (120, 110, 140, 200),    # Lilaesszenciájú szürke
            "line": (0, 0, 0, 12),          # Finom elválasztó
            "accent": (255, 100, 50, 255),  # Narancs/vörös akcentus (NIO style)
            "accent2": (0, 200, 180, 255),  # Türkiz (BYD style)
            "bg_start": (255, 255, 245, 220),  # Elefántcsont fehér
            "bg_end": (245, 240, 255, 220)     # Levendulás árnyalat
        }
    else:
        # Sötét mód - luxus kínai EV night mode (NIO/Xpeng stílus)
        colors = {
            "main": (255, 255, 255, 255),   # Tiszta fehér
            "dim": (150, 155, 180, 200),    # Szürkéskék
            "line": (100, 150, 255, 30),    # Kékes neon vonal
            "accent": (0, 230, 200, 255),   # Neon türkiz (Xpeng G9 style)
            "accent2": (180, 100, 255, 255), # Lila (Li Auto style)
            "bg_start": (18, 18, 28, 210),   # Mély sötétkék
            "bg_end": (28, 18, 38, 210)      # Lilás mélység
        }
    
    draw = ImageDraw.Draw(img)
    
    # GRADIENT HATÁSÚ LUXUS HÁTTÉR (színátmenet szimuláció)
    bg_gradient = []
    for y in range(by, by + bh):
        ratio = (y - by) / bh
        r = int(colors["bg_start"][0] * (1 - ratio) + colors["bg_end"][0] * ratio)
        g = int(colors["bg_start"][1] * (1 - ratio) + colors["bg_end"][1] * ratio)
        b = int(colors["bg_start"][2] * (1 - ratio) + colors["bg_end"][2] * ratio)
        a = colors["bg_start"][3]
        bg_gradient.append((r, g, b, a))
    
    # Gradient vonalak rajzolása
    for i, y in enumerate(range(by, by + bh)):
        draw.line([(bx, y), (bx + bw, y)], fill=bg_gradient[i], width=1)
    
    # Lekerekített keret neon glow effektussal
    corner_radius = 32
    glow_color = colors["accent"] if brightness < 145 else colors["accent2"]
    draw_rounded_rect(draw, [bx+2, by+2, bx+bw-2, by+bh-2], corner_radius, fill=(0,0,0,0), outline=glow_color, outline_width=1)
    draw_rounded_rect(draw, [bx, by, bx+bw, by+bh], corner_radius, fill=(0,0,0,0), outline=colors["line"], outline_width=2)
    
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

    # 1. AKTUÁLIS BLOKK (HŐFOK + ESŐ/ÉRZET EGYMÁS FELETT)
    SEC1_W = 820
    temp_txt, feel_txt, rain_txt = f"{weather['temp']}°C", f"{weather['feels_like']}°C", f"{weather.get('pop', 0)}%"
    
    t_bbox = draw.textbbox((0, 0), temp_txt, font=f_t)
    t_w = t_bbox[2]
    
    main_content_w = ICON_DISPLAY_SIZE + 40 + t_w + 60 + 110
    start_x = (curr_x + SEC1_W // 2) - (main_content_w // 2)
    
    paste_icon(img, icon_img, start_x, mid_y - ICON_DISPLAY_SIZE // 2)
    tx, ty = start_x + ICON_DISPLAY_SIZE + 40, mid_y - (t_bbox[3] // 2) + 5
    
    # Fejléc - nap akcentus2, állapot akcentus
    day_str = get_day_hu(weather["now_dt"]).upper()
    draw.text((tx + 20, mid_y - 65), day_str, font=f_h, fill=colors["accent2"])
    day_w = draw.textbbox((0, 0), day_str, font=f_h)[2]
    draw.text((tx + 20 + day_w + 30, mid_y - 65), weather["weather_hu"].upper(), font=f_h, fill=colors["accent"])
    
    # Fő Hőfok - extra glow hatás (kétszer rajzolva)
    draw.text((tx-1, ty-1), temp_txt, font=f_t, fill=(colors["accent"][0], colors["accent"][1], colors["accent"][2], 60))
    draw.text((tx, ty), temp_txt, font=f_t, fill=colors["main"])
    
    # INFÓ OSZLOP (Eső esélye fent, Érzet lent)
    info_x = tx + t_w + 60
    
    if rainq_icon_img: 
        paste_icon(img, rainq_icon_img, info_x, mid_y - 42, size=42)
    draw.text((info_x + 52, mid_y - 42), rain_txt, font=f_s, fill=colors["dim"])
    
    if feel_icon_img: 
        paste_icon(img, feel_icon_img, info_x + 4, mid_y + 8, size=36)
    draw.text((info_x + 52, mid_y + 8), feel_txt, font=f_s, fill=colors["dim"])
    
    curr_x += SEC1_W
    draw.line([(curr_x, by + 50), (curr_x, by + bh - 50)], fill=colors["line"], width=2)

    # 2. SZÉL & PÁRA
    SEC2_W, ix = 300, curr_x + 70
    for i, (val, unit, icon, sz) in enumerate([(weather['wind_kmh'], " km/h", wind1_icon_img, WIND_ICON_SIZE), (weather['humidity'], "%", para_icon_img, PARA_ICON_SIZE)]):
        y_pos = mid_y - 68 if i == 0 else mid_y + 12
        if icon: paste_icon(img, icon, ix, y_pos + 4, size=sz)
        draw.text((ix + 58, y_pos), f"{val}{unit}", font=f_v, fill=colors["main"])
    curr_x += SEC2_W
    draw.line([(curr_x, by + 50), (curr_x, by + bh - 50)], fill=colors["line"], width=2)

    # 3. NAPKELTE / NAPNYUGTA
    SEC3_W, sx = 260, curr_x + 70
    for i, (val, icon) in enumerate([(weather['sunrise'], sunrise_icon_img), (weather['sunset'], sunset_icon_img)]):
        y_pos = mid_y - 65 if i == 0 else mid_y + 10
        if icon: paste_icon(img, icon, sx, y_pos + 6, size=SUN_ICON_SIZE)
        draw.text((sx + 58, y_pos), val, font=f_v, fill=colors["main"])
    curr_x += SEC3_W
    draw.line([(curr_x, by + 50), (curr_x, by + bh - 50)], fill=colors["line"], width=2)

    # 4. ELŐREJELZÉS (3 NAP) - neonos napok
    SEC4_W, slot_w = 540, 180
    for i, day_entry in enumerate(weather["forecast"]):
        sm = curr_x + (i * slot_w) + (slot_w // 2)
        dn = get_day_hu(datetime.fromtimestamp(day_entry["dt"])).upper()[:3]
        fv = f"{round(day_entry['main']['temp'])}°C"
        
        if i < len(forecast_icons): 
            paste_icon(img, forecast_icons[i], sm - 25, mid_y - 75, size=50)
        
        # Nap neve neonos akcentussal
        draw.text((sm - draw.textbbox((0, 0), dn, font=f_fd)[2] // 2, mid_y - 15), dn, font=f_fd, fill=colors["accent2"])
        draw.text((sm - draw.textbbox((0, 0), fv, font=f_fv)[2] // 2, mid_y + 15), fv, font=f_fv, fill=colors["main"])
        
        # Eső esély az előrejelzésben
        pop_val = day_entry.get('pop', 0)
        if pop_val > 0:
            pop_txt = f"{round(pop_val * 100)}%"
            draw.text((sm - draw.textbbox((0, 0), pop_txt, font=f_s)[2] // 2, mid_y + 45), pop_txt, font=f_s, fill=colors["accent"])
    
    curr_x += SEC4_W
    draw.line([(curr_x, by + 50), (curr_x, by + bh - 50)], fill=colors["line"], width=2)

    # 5. NÉVNAP & IDŐ
    draw.text((curr_x + 50, mid_y - 50), "NÉVNAP", font=f_h, fill=colors["accent2"])
    draw.text((curr_x + 50, mid_y - 2), ", ".join(namedays), font=f_n, fill=colors["main"])
    
    dt_txt = weather["now_dt"].strftime("%Y.%m.%d  %H:%M")
    draw.text((bx + bw - draw.textbbox((0, 0), dt_txt, font=f_dt)[2] - 20, by + 15), dt_txt, font=f_dt, fill=colors["dim"])
