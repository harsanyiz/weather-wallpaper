from PIL import Image, ImageDraw, ImageFont, ImageStat
from datetime import datetime

# --- KONFIGURÁCIÓ & MÉRETEK (4K HORIZONTÁLIS) ---
WIDGET_WIDTH, WIDGET_HEIGHT, WIDGET_Y, OFFSET_LEFT, INNER_MARGIN = 2400, 200, 100, 135, 80
FONT_TEMP, FONT_HEADER, FONT_VALUE, FONT_SMALL, FONT_DATETIME, FONT_NAME = 105, 24, 36, 34, 24, 28
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

def draw_weather_widget(img, weather, icon_img, feel_icon_img, rainq_icon_img, wind1_icon_img, para_icon_img, forecast_icons, sunrise_icon_img, sunset_icon_img, namedays, tz_offset):
    from logic_weather import get_day_hu
    bx, by, bw, bh = OFFSET_LEFT, WIDGET_Y, WIDGET_WIDTH, WIDGET_HEIGHT
    
    # Dinamikus színválasztás a háttér fényereje alapján
    brightness = ImageStat.Stat(img.crop((bx, by, bx + bw, by + bh)).convert("L")).mean[0]
    colors = {"main": (255, 255, 255, 255), "dim": (255, 255, 255, 160), "line": (255, 255, 255, 40)}
    if brightness > 145: colors = {"main": (0, 0, 0, 230), "dim": (0, 0, 0, 140), "line": (0, 0, 0, 40)}
    
    draw, mid_y, curr_x = ImageDraw.Draw(img), by + (bh // 2), bx + INNER_MARGIN
    f_t, f_h, f_v, f_s, f_dt, f_n, f_fd, f_fv = get_f(FONT_TEMP, True), get_f(FONT_HEADER), get_f(FONT_VALUE, True), get_f(FONT_SMALL), get_f(FONT_DATETIME), get_f(FONT_NAME), get_f(FONT_FORECAST_DAY), get_f(FONT_FORECAST_TEMP, True)

    # 1. AKTUÁLIS + ESŐ ESÉLY + FEEL (SZIMMETRIKUS BLOKK)
    SEC1_W = 880 
    temp_txt, feel_txt = f"{weather['temp']}°C", f"{weather['feels_like']}°C"
    # Az eső esélyét százalékra váltjuk (ha az API 0-1 között adja, szorozni kell 100-zal a logikában)
    rain_txt = f"{weather.get('pop', 0)}%" 
    
    t_w = draw.textbbox((0, 0), temp_txt, font=f_t)[2]
    f_w = draw.textbbox((0, 0), feel_txt, font=f_s)[2]
    r_w = draw.textbbox((0, 0), rain_txt, font=f_s)[2]
    
    main_w = ICON_DISPLAY_SIZE + 45 + t_w + 50 + (34 + 12 + r_w) + 40 + (34 + 12 + f_w)
    start_x = (curr_x + SEC1_W // 2) - (main_w // 2)
    
    paste_icon(img, icon_img, start_x, mid_y - ICON_DISPLAY_SIZE // 2)
    tx, ty = start_x + ICON_DISPLAY_SIZE + 45, mid_y - (draw.textbbox((0, 0), temp_txt, font=f_t)[3] // 2) + 5
    
    draw.text((tx + 25, mid_y - 65), get_day_hu(weather["now_dt"]).upper(), font=f_h, fill=colors["dim"])
    day_w = draw.textbbox((0, 0), get_day_hu(weather["now_dt"]).upper(), font=f_h)[2]
    draw.text((tx + 25 + day_w + 35, mid_y - 65), weather["weather_hu"].upper(), font=f_h, fill=colors["dim"])
    draw.text((tx, ty), temp_txt, font=f_t, fill=colors["main"])
    
    # Eső valószínűsége ikon + szöveg
    rain_x = tx + t_w + 50
    if rainq_icon_img: paste_icon(img, rainq_icon_img, rain_x, mid_y + 12, size=34)
    draw.text((rain_x + 46, mid_y + 10), rain_txt, font=f_s, fill=colors["dim"])
    
    # Érzet ikon + szöveg
    feel_x = rain_x + (34 + 12 + r_w) + 40
    if feel_icon_img: paste_icon(img, feel_icon_img, feel_x, mid_y + 12, size=34)
    draw.text((feel_x + 46, mid_y + 10), feel_txt, font=f_s, fill=colors["dim"])
    
    curr_x += SEC1_W
    draw.line([(curr_x + 5, by + 50), (curr_x + 5, by + bh - 50)], fill=colors["line"], width=2)

    # 2. ADATOK (WIND1 + PÁRA)
    SEC2_W, ix = 300, curr_x + 72
    for i, (val, unit, icon, sz) in enumerate([(weather['wind_kmh'], " km/h", wind1_icon_img, WIND_ICON_SIZE), (weather['humidity'], "%", para_icon_img, PARA_ICON_SIZE)]):
        y_txt = mid_y - 68 if i == 0 else mid_y + 12
        if icon: paste_icon(img, icon, ix, y_txt + 4, size=sz)
        draw.text((ix + 58, y_txt), f"{val}{unit}", font=f_v, fill=colors["main"])
    curr_x += SEC2_W
    draw.line([(curr_x, by + 50), (curr_x, by + bh - 50)], fill=colors["line"], width=2)

    # 3. NAP (SUNRISE, SUNSET)
    SEC3_W, sx = 260, curr_x + 72
    for i, (val, icon) in enumerate([(weather['sunrise'], sunrise_icon_img), (weather['sunset'], sunset_icon_img)]):
        y_txt = mid_y - 65 if i == 0 else mid_y + 10
        if icon: paste_icon(img, icon, sx, y_txt + 6, size=SUN_ICON_SIZE)
        draw.text((sx + 58, y_txt), val, font=f_v, fill=colors["main"])
    curr_x += SEC3_W
    draw.line([(curr_x, by + 50), (curr_x, by + bh - 50)], fill=colors["line"], width=2)

    # 4. ELŐREJELZÉS
    SEC4_W, slot_w = 540, 180
    for i, day_entry in enumerate(weather["forecast"]):
        sm = curr_x + (i * slot_w) + (slot_w // 2)
        dn, fv = get_day_hu(datetime.fromtimestamp(day_entry["dt"])).upper()[:3], f"{round(day_entry['main']['temp'])}°C"
        if i < len(forecast_icons): paste_icon(img, forecast_icons[i], sm - 25, mid_y - 72, size=50)
        draw.text((sm - draw.textbbox((0, 0), dn, font=f_fd)[2] // 2, mid_y - 12), dn, font=f_fd, fill=colors["dim"])
        draw.text((sm - draw.textbbox((0, 0), fv, font=f_fv)[2] // 2, mid_y + 18), fv, font=f_fv, fill=colors["main"])
    curr_x += SEC4_W
    draw.line([(curr_x, by + 50), (curr_x, by + bh - 50)], fill=colors["line"], width=2)

    # 5. NÉVNAP & IDŐBÉLYEG
    draw.text((curr_x + 50, mid_y - 50), "NÉVNAP", font=f_h, fill=colors["dim"])
    draw.text((curr_x + 50, mid_y - 2), ", ".join(n.strip() for n in namedays), font=f_n, fill=colors["main"])
    dt_txt = weather["now_dt"].strftime("%Y.%m.%d  %H:%M")
    draw.text((bx + bw - draw.textbbox((0, 0), dt_txt, font=f_dt)[2] - 80, by + 15), dt_txt, font=f_dt, fill=(160, 160, 160, 200))
