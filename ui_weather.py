from PIL import Image, ImageDraw, ImageFont, ImageStat
from datetime import datetime

# ============================================================
# XIAOMI PREMIUM WIDGET - TISZTÁBB DESIGN, NINCS FELESLEGES SZÖVEG
# ============================================================
WIDGET_WIDTH  = 2400
WIDGET_HEIGHT = 180
WIDGET_Y      = 80
OFFSET_LEFT   = 135
INNER_MARGIN  = 50

# Betűméretek
FONT_TEMP     = 72
FONT_HEADER   = 24
FONT_VALUE    = 32      # Nagyobb, mert nincs mellette felirat
FONT_SMALL    = 24
FONT_DATETIME = 22
FONT_NAME     = 28
FONT_FORECAST_DAY = 20
FONT_FORECAST_TEMP = 28
FONT_SUN_TIME = 28

# Ikon méretek
ICON_DISPLAY_SIZE  = 120
FEEL_ICON_SIZE     = 30
WIND_ICON_SIZE     = 36      # Nagyobb, mert nincs szöveg mellette
HUMIDITY_ICON_SIZE = 36
SUN_ICON_SIZE      = 32
FORECAST_ICON_SIZE = 42

# Távolságok
SECTION_GAP = 45
# ============================================================

def paste_icon(img, icon_img, x, y, size):
    if icon_img is None:
        return
    resized = icon_img.resize((size, size), Image.Resampling.LANCZOS)
    img.paste(resized, (int(x), int(y)), resized)


def draw_weather_widget_clean(img, weather, icon_img, feel_icon_img,
                               wind_icon_img, para_icon_img,
                               forecast_icons, sunrise_icon_img, sunset_icon_img,
                               namedays, tz_offset):
    from logic_weather import get_day_hu

    bx = OFFSET_LEFT
    by = WIDGET_Y
    bw = WIDGET_WIDTH
    bh = WIDGET_HEIGHT

    # Szín meghatározás
    region = img.crop((bx, by, bx + bw, by + bh)).convert("L")
    brightness = ImageStat.Stat(region).mean[0]
    
    if brightness > 145:
        colors = {
            "main": (28, 28, 30, 255),
            "dim": (110, 110, 115, 230),
            "accent": (0, 122, 255, 255),
            "line": (200, 200, 200, 50),
        }
    else:
        colors = {
            "main": (255, 255, 255, 255),
            "dim": (180, 180, 185, 230),
            "accent": (0, 150, 255, 255),
            "line": (80, 80, 90, 60),
        }

    draw = ImageDraw.Draw(img)
    
    # Betűk
    f_t = ImageFont.truetype("/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf", FONT_TEMP)
    f_h = ImageFont.truetype("/usr/share/fonts/truetype/noto/NotoSans-Light.ttf", FONT_HEADER)
    f_v = ImageFont.truetype("/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf", FONT_VALUE)
    f_s = ImageFont.truetype("/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf", FONT_SMALL)
    f_dt = ImageFont.truetype("/usr/share/fonts/truetype/noto/NotoSans-Light.ttf", FONT_DATETIME)
    f_n = ImageFont.truetype("/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf", FONT_NAME)
    f_fd = ImageFont.truetype("/usr/share/fonts/truetype/noto/NotoSans-Light.ttf", FONT_FORECAST_DAY)
    f_fv = ImageFont.truetype("/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf", FONT_FORECAST_TEMP)
    f_sun = ImageFont.truetype("/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf", FONT_SUN_TIME)

    curr_x = int(bx + INNER_MARGIN)
    mid_y = int(by + (bh // 2))
    now_dt = weather["now_dt"]

    # ── SZEKCIÓ 1: Ikon + időjárás ──────────────────────────────────────────
    day_txt = get_day_hu(now_dt).upper()
    desc_txt = weather["weather_hu"].upper()
    temp_txt = f"{weather['temp']}°"
    feel_txt = f"{weather['feels_like']}°"

    if icon_img:
        paste_icon(img, icon_img, curr_x, mid_y - ICON_DISPLAY_SIZE//2, ICON_DISPLAY_SIZE)

    tx = curr_x + ICON_DISPLAY_SIZE + 30
    
    # Fejléc
    draw.text((tx, mid_y - 45), day_txt, font=f_h, fill=colors["dim"])
    draw.text((tx + draw.textbbox((0, 0), day_txt, font=f_h)[2] + 10, mid_y - 45), 
              desc_txt, font=f_h, fill=colors["accent"])
    
    # Hőmérséklet
    draw.text((tx, mid_y - 5), temp_txt, font=f_t, fill=colors["main"])
    
    # Érzet hőmérséklet (csak ikon + érték, nincs "ÉRZET" felirat)
    feel_x = tx + draw.textbbox((0, 0), temp_txt, font=f_t)[2] + 15
    if feel_icon_img:
        paste_icon(img, feel_icon_img, feel_x, mid_y - 10, FEEL_ICON_SIZE)
    draw.text((feel_x + FEEL_ICON_SIZE + 8, mid_y - 8), feel_txt, font=f_s, fill=colors["dim"])

    curr_x += ICON_DISPLAY_SIZE + 30 + draw.textbbox((0, 0), temp_txt, font=f_t)[2] + 15 + FEEL_ICON_SIZE + 8 + draw.textbbox((0, 0), feel_txt, font=f_s)[2] + SECTION_GAP
    draw.line([(curr_x, by + 25), (curr_x, by + bh - 25)], fill=colors["line"], width=2)
    curr_x += 35

    # ── SZEKCIÓ 2: SZÉL + PÁRA (CSAK IKON + ÉRTÉK) ──────────────────────────
    wind_val = f"{weather['wind_kmh']} km/h"
    hum_val = f"{weather['humidity']}%"
    
    # Szélesség számítás
    wind_w = draw.textbbox((0, 0), wind_val, font=f_v)[2]
    hum_w = draw.textbbox((0, 0), hum_val, font=f_v)[2]
    col_w = max(WIND_ICON_SIZE + 10 + wind_w, HUMIDITY_ICON_SIZE + 10 + hum_w)

    # Szél (ikon + érték)
    if wind_icon_img:
        paste_icon(img, wind_icon_img, curr_x, mid_y - 30, WIND_ICON_SIZE)
    draw.text((curr_x + WIND_ICON_SIZE + 10, mid_y - 28), wind_val, font=f_v, fill=colors["main"])
    
    # Pára (ikon + érték)
    if para_icon_img:
        paste_icon(img, para_icon_img, curr_x, mid_y + 10, HUMIDITY_ICON_SIZE)
    draw.text((curr_x + HUMIDITY_ICON_SIZE + 10, mid_y + 12), hum_val, font=f_v, fill=colors["main"])

    curr_x += col_w + SECTION_GAP
    draw.line([(curr_x, by + 25), (curr_x, by + bh - 25)], fill=colors["line"], width=2)
    curr_x += 35

    # ── SZEKCIÓ 3: NAPKELTE + NAPNYUGTA ──────────────────────────────────────
    sunrise_txt = weather["sunrise"]
    sunset_txt = weather["sunset"]
    
    sr_w = draw.textbbox((0, 0), sunrise_txt, font=f_sun)[2]
    ss_w = draw.textbbox((0, 0), sunset_txt, font=f_sun)[2]
    sun_w = max(SUN_ICON_SIZE + 10 + sr_w, SUN_ICON_SIZE + 10 + ss_w)

    # Napkelte
    if sunrise_icon_img:
        paste_icon(img, sunrise_icon_img, curr_x, mid_y - 30, SUN_ICON_SIZE)
    draw.text((curr_x + SUN_ICON_SIZE + 10, mid_y - 28), sunrise_txt, font=f_sun, fill=colors["main"])
    
    # Napnyugta
    if sunset_icon_img:
        paste_icon(img, sunset_icon_img, curr_x, mid_y + 10, SUN_ICON_SIZE)
    draw.text((curr_x + SUN_ICON_SIZE + 10, mid_y + 12), sunset_txt, font=f_sun, fill=colors["main"])

    curr_x += sun_w + SECTION_GAP
    draw.line([(curr_x, by + 25), (curr_x, by + bh - 25)], fill=colors["line"], width=2)
    curr_x += 35

    # ── SZEKCIÓ 4: 3 NAPOS ELŐREJELZÉS ───────────────────────────────────────
    for i, day_entry in enumerate(weather["forecast"][:3]):
        d_name = get_day_hu(datetime.fromtimestamp(day_entry["dt"])).upper()[:3]
        f_val = f"{round(day_entry['main']['temp'])}°"
        
        d_w = draw.textbbox((0, 0), d_name, font=f_fd)[2]
        f_w = draw.textbbox((0, 0), f_val, font=f_fv)[2]
        col_w = max(d_w, f_w, FORECAST_ICON_SIZE)

        fc_icon = forecast_icons[i] if i < len(forecast_icons) else None
        if fc_icon:
            paste_icon(img, fc_icon, curr_x + (col_w - FORECAST_ICON_SIZE)//2, mid_y - 40, FORECAST_ICON_SIZE)

        draw.text((curr_x + (col_w - d_w)//2, mid_y + 5), d_name, font=f_fd, fill=colors["dim"])
        draw.text((curr_x + (col_w - f_w)//2, mid_y + 32), f_val, font=f_fv, fill=colors["main"])
        
        curr_x += col_w + 20

    draw.line([(curr_x, by + 25), (curr_x, by + bh - 25)], fill=colors["line"], width=2)
    curr_x += 35

    # ── SZEKCIÓ 5: NÉVNAP ────────────────────────────────────────────────────
    nameday_value = ", ".join(n.strip().rstrip("\\") for n in namedays[:2])  # Csak 2 név, hogy ne csússzon ki
    if len(namedays) > 2:
        nameday_value += f" +{len(namedays)-2}"
    
    draw.text((curr_x, mid_y - 10), "NÉVNAP", font=f_l, fill=colors["accent"])
    draw.text((curr_x, mid_y + 15), nameday_value, font=f_n, fill=colors["main"])

    # ── DÁTUM + IDŐ (jobb felső) ────────────────────────────────────────────
    datetime_txt = now_dt.strftime("%Y.%m.%d  •  %H:%M")
    dt_w = draw.textbbox((0, 0), datetime_txt, font=f_dt)[2]
    draw.text((bx + bw - dt_w - INNER_MARGIN, by + 15), datetime_txt, font=f_dt, fill=colors["dim"])
