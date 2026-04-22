from PIL import Image, ImageDraw, ImageFont, ImageStat
from datetime import datetime, timezone, timedelta

# ============================================================
# 4K-S HORIZONTÁLIS DESIGN KONFIGURÁCIÓ
# ============================================================
WIDGET_WIDTH  = 2400
WIDGET_HEIGHT = 200
WIDGET_Y      = 100
OFFSET_LEFT   = 135
INNER_MARGIN  = 80

# 4K-s betűméretek
FONT_TEMP     = 90
FONT_HEADER   = 24
FONT_LABEL    = 28
FONT_VALUE    = 36
FONT_SMALL    = 30
FONT_DATETIME = 24
FONT_NAME     = 28
FONT_FORECAST_DAY = 22
FONT_FORECAST_TEMP = 30

# Ikon megjelenítési méretek
ICON_DISPLAY_SIZE  = 160
FEEL_ICON_SIZE     = 36
WIND_ICON_SIZE     = 36
PARA_ICON_SIZE     = 36
FORECAST_ICON_SIZE = 44
SUN_ICON_SIZE      = 40
ICON_GAP           = 10

ICON_OFFSET_X = 0
# ============================================================


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

    bx = OFFSET_LEFT
    by = WIDGET_Y
    bw = WIDGET_WIDTH
    bh = WIDGET_HEIGHT

    region = img.crop((bx, by, bx + bw, by + bh)).convert("L")
    colors = get_text_colors(ImageStat.Stat(region).mean[0])

    draw   = ImageDraw.Draw(img)
    f_t    = get_f(FONT_TEMP,     bold=True)
    f_h    = get_f(FONT_HEADER)
    f_l    = get_f(FONT_LABEL)
    f_v    = get_f(FONT_VALUE,    bold=True)
    f_s    = get_f(FONT_SMALL)
    f_dt   = get_f(FONT_DATETIME)
    f_n    = get_f(FONT_NAME)
    f_fd   = get_f(FONT_FORECAST_DAY)
    f_fv   = get_f(FONT_FORECAST_TEMP, bold=True)

    curr_x = int(bx + INNER_MARGIN)
    mid_y  = int(by + (bh // 2))
    now_dt = weather["now_dt"]

    # ── SZEKCIÓ 1 ────────────────────────────────────────────────────────────
    day_txt  = get_day_hu(now_dt).upper()
    desc_txt = weather["weather_hu"].upper()
    temp_txt = f"{weather['temp']}°C"
    feel_txt = f"{weather['feels_like']}°C"

    day_w    = draw.textbbox((0, 0), day_txt,  font=f_h)[2]
    desc_w   = draw.textbbox((0, 0), desc_txt, font=f_h)[2]
    temp_w   = draw.textbbox((0, 0), temp_txt, font=f_t)[2]
    feel_w   = draw.textbbox((0, 0), feel_txt, font=f_s)[2]

    header_gap   = 14
    header_w     = day_w + header_gap + desc_w
    feel_row_w   = FEEL_ICON_SIZE + ICON_GAP + feel_w
    temp_row_w   = temp_w + 14 + feel_row_w
    text_block_w = max(header_w, temp_row_w)

    icon_gap_px  = ICON_DISPLAY_SIZE + 30 if icon_img else 0

    if icon_img:
        paste_icon(img, icon_img, curr_x + ICON_OFFSET_X,
                   mid_y - ICON_DISPLAY_SIZE // 2)

    tx = curr_x + icon_gap_px

    header_h = draw.textbbox((0, 0), day_txt, font=f_h)[3]
    temp_h   = draw.textbbox((0, 0), temp_txt, font=f_t)[3]
    spacing  = 8
    total_h  = header_h + spacing + temp_h
    header_y = mid_y - total_h // 2
    temp_y   = header_y + header_h + spacing

    # ── PONTOS IGAZÍTÁSOK ───────────────────────────────────────────────────
    # "SZERDA RÉSZBEN FELHŐS" 3 pixellel LEJJEBB
    draw.text((tx, header_y + 3), day_txt, font=f_h, fill=colors["dim"])
    draw.text((tx + day_w + header_gap, header_y + 3), desc_txt, font=f_h, fill=colors["dim"])
    
    # Hőfok 1 pixellel FELJEBB
    draw.text((tx, temp_y - 1), temp_txt, font=f_t, fill=colors["main"])

    temp_bottom  = temp_y - 1 + temp_h
    feel_icon_y  = temp_bottom - FEEL_ICON_SIZE
    feel_text_y  = temp_bottom - draw.textbbox((0, 0), feel_txt, font=f_s)[3]
    feel_x       = tx + temp_w + 14

    if feel_icon_img:
        paste_icon(img, feel_icon_img, feel_x, feel_icon_y, size=FEEL_ICON_SIZE)
    draw.text((feel_x + FEEL_ICON_SIZE + ICON_GAP, feel_text_y),
              feel_txt, font=f_s, fill=colors["dim"])

    curr_x += icon_gap_px + text_block_w + 60
    draw.line([(curr_x, by + 40), (curr_x, by + bh - 40)], fill=colors["line"], width=3)
    curr_x += 50

    # ── SZEKCIÓ 2 ────────────────────────────────────────────────────────────
    wind_val = f"{weather['wind_kmh']} km/h"
    hum_val  = f"{weather['humidity']}%"
    wind_vw  = draw.textbbox((0, 0), wind_val, font=f_v)[2]
    hum_vw   = draw.textbbox((0, 0), hum_val,  font=f_v)[2]
    col2_w   = max(WIND_ICON_SIZE + ICON_GAP + wind_vw,
                   PARA_ICON_SIZE + ICON_GAP + hum_vw)

    top_y  = mid_y - 52
    bot_y  = mid_y + 10

    wval_h = draw.textbbox((0, 0), wind_val, font=f_v)[3]
    hval_h = draw.textbbox((0, 0), hum_val,  font=f_v)[3]

    if wind_icon_img:
        paste_icon(img, wind_icon_img, curr_x,
                   top_y + (wval_h - WIND_ICON_SIZE) // 2, size=WIND_ICON_SIZE)
    draw.text((curr_x + WIND_ICON_SIZE + ICON_GAP, top_y), wind_val, font=f_v, fill=colors["main"])

    if para_icon_img:
        paste_icon(img, para_icon_img, curr_x,
                   bot_y + (hval_h - PARA_ICON_SIZE) // 2, size=PARA_ICON_SIZE)
    draw.text((curr_x + PARA_ICON_SIZE + ICON_GAP, bot_y), hum_val, font=f_v, fill=colors["main"])

    curr_x += col2_w + 50
    draw.line([(curr_x, by + 40), (curr_x, by + bh - 40)], fill=colors["line"], width=3)
    curr_x += 50

    # ── SZEKCIÓ 3 ────────────────────────────────────────────────────────────
    sunrise_txt = weather["sunrise"]
    sunset_txt  = weather["sunset"]
    sr_vw = draw.textbbox((0, 0), sunrise_txt, font=f_v)[2]
    ss_vw = draw.textbbox((0, 0), sunset_txt,  font=f_v)[2]
    sun_col_w = max(SUN_ICON_SIZE + ICON_GAP + sr_vw,
                    SUN_ICON_SIZE + ICON_GAP + ss_vw)

    if sunrise_icon_img:
        paste_icon(img, sunrise_icon_img, curr_x, top_y, size=SUN_ICON_SIZE)
    draw.text((curr_x + SUN_ICON_SIZE + ICON_GAP, top_y),
              sunrise_txt, font=f_v, fill=colors["main"])

    if sunset_icon_img:
        paste_icon(img, sunset_icon_img, curr_x, bot_y, size=SUN_ICON_SIZE)
    draw.text((curr_x + SUN_ICON_SIZE + ICON_GAP, bot_y),
              sunset_txt, font=f_v, fill=colors["main"])

    curr_x += sun_col_w + 50
    draw.line([(curr_x, by + 40), (curr_x, by + bh - 40)], fill=colors["line"], width=3)
    curr_x += 50

    # ── SZEKCIÓ 4: FORECAST (4 PIXELLEL BALRA) ───────────────────────────────
    forecast_offset_y = 18
    forecast_offset_x = -4   # 4 pixel balra
    
    for i, day_entry in enumerate(weather["forecast"]):
        d_name   = get_day_hu(datetime.fromtimestamp(day_entry["dt"])).upper()[:3]
        f_val    = f"{round(day_entry['main']['temp'])}°C"
        d_name_w = draw.textbbox((0, 0), d_name, font=f_fd)[2]
        f_val_w  = draw.textbbox((0, 0), f_val,  font=f_fv)[2]
        col_w    = max(d_name_w, f_val_w, FORECAST_ICON_SIZE)

        fc_icon = forecast_icons[i] if i < len(forecast_icons) else None
        if fc_icon:
            paste_icon(img, fc_icon,
                       curr_x + forecast_offset_x + (col_w - FORECAST_ICON_SIZE) // 2,
                       mid_y - 45 - FORECAST_ICON_SIZE + forecast_offset_y,
                       size=FORECAST_ICON_SIZE)

        draw.text((curr_x + forecast_offset_x + (col_w - d_name_w) // 2, mid_y - 40 + forecast_offset_y),
                  d_name, font=f_fd, fill=colors["dim"])
        draw.text((curr_x + forecast_offset_x + (col_w - f_val_w)  // 2, mid_y - 8 + forecast_offset_y),
                  f_val,  font=f_fv, fill=colors["main"])
        curr_x += col_w + 14

    # ── SZEKCIÓ 5 ────────────────────────────────────────────────────────────
    draw.line([(curr_x, by + 40), (curr_x, by + bh - 40)], fill=colors["line"], width=3)
    curr_x += 40

    nameday_value = ", ".join(n.strip().rstrip("\\") for n in namedays)
    draw.text((curr_x, mid_y - 45), "NÉVNAP",      font=f_l, fill=colors["dim"])
    draw.text((curr_x, mid_y),      nameday_value, font=f_n, fill=colors["main"])

    # ── DÁTUM + IDŐ ──────────────────────────────────────────────────────────
    datetime_txt = now_dt.strftime("%y.%m.%d  %H:%M")
    dt_w = draw.textbbox((0, 0), datetime_txt, font=f_dt)[2]
    draw.text((bx + bw - dt_w, by + 10), datetime_txt, font=f_dt,
              fill=(160, 160, 160, 200))
