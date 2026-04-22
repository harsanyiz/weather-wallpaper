from PIL import Image, ImageDraw, ImageFont, ImageStat
from datetime import datetime, timezone, timedelta

# ============================================================
# 4K-S HORIZONTÁLIS DESIGN KONFIGURÁCIÓ
# ============================================================
WIDGET_WIDTH  = 2200
WIDGET_HEIGHT = 200
WIDGET_Y      = 100
OFFSET_LEFT   = 135    # A Media ikon feletti fehér jelölőhöz igazítva
INNER_MARGIN  = 80

# 4K-s betűméretek
FONT_TEMP     = 90   # Fő hőmérséklet
FONT_DESC     = 32   # Időjárás megnevezése (pl. DERÜLT) – a nap neve mellé
FONT_LABEL    = 28   # Címkék (pl. HÉTFŐ, SZÉL)
FONT_VALUE    = 36   # Értékek (pl. 10 km/h)
FONT_SMALL    = 30   # Kis érzet érték a hőfok mellett
FONT_DATETIME = 24   # Dátum+idő jobb felső sarok
FONT_NAME     = 28   # Névnap felirat

# Ikon megjelenítési méretek
ICON_DISPLAY_SIZE  = 160   # px – aktuális időjárás ikon
FEEL_ICON_SIZE     = 36    # feel.png – érzet ikon a hőfok mellett
FORECAST_ICON_SIZE = 56    # előrejelzés ikonok a nap neve felett (kisebb, ne lógjon ki)
SUN_ICON_SIZE      = 44    # napkelte/napnyugta ikon mérete

# Ikonok bal oldali eltolása a szekción belül (opcionális finomhangolás)
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
    """
    Beilleszti az ikont az img-be adott x,y pozícióba.
    Az ikont felnagyítja ICON_DISPLAY_SIZE-ra, megtartja az alfa csatornát.
    """
    if icon_img is None:
        return
    resized = icon_img.resize((size, size), Image.Resampling.LANCZOS)
    img.paste(resized, (int(x), int(y)), resized)


def draw_weather_widget(img, weather, icon_img, feel_icon_img, forecast_icons,
                        sunrise_icon_img, sunset_icon_img, namedays, tz_offset):
    """
    Rárajzolja a widget összes elemét a 4K-s képre.

    Szekciók:
      1. Időjárás ikon + NAP LEÍRÁS + nagy hőfok + kis érzet (feel ikon + °C)
      2. Szél / Pára egymás alatt egy oszlopban
      3. Napkelte (day_clear ikon + idő) / Napnyugta (night_clear ikon + idő) egymás alatt
      4. 3 napos előrejelzés ikonnal + nap + hőfok
      5. Névnap
      6. Dátum+idő jobb felső sarok
    """
    from logic_weather import get_day_hu

    bx = OFFSET_LEFT
    by = WIDGET_Y
    bw = WIDGET_WIDTH
    bh = WIDGET_HEIGHT

    region = img.crop((bx, by, bx + bw, by + bh)).convert("L")
    avg_brightness = ImageStat.Stat(region).mean[0]
    colors = get_text_colors(avg_brightness)

    draw = ImageDraw.Draw(img)

    f_t   = get_f(FONT_TEMP,     bold=True)
    f_d   = get_f(FONT_DESC)
    f_l   = get_f(FONT_LABEL)
    f_v   = get_f(FONT_VALUE,    bold=True)
    f_s   = get_f(FONT_SMALL)               # kis érzet érték
    f_dt  = get_f(FONT_DATETIME)
    f_n   = get_f(FONT_NAME)

    curr_x = int(bx + INNER_MARGIN)
    mid_y  = int(by + (bh // 2))

    now_dt     = weather["now_dt"]
    temp       = weather["temp"]
    weather_hu = weather["weather_hu"]

    # ── SZEKCIÓ 1: IKON + NAP LEÍRÁS + HŐFOK + kis érzet ────────────────────
    day_txt   = get_day_hu(now_dt).upper()
    desc_txt  = weather_hu.upper()
    temp_txt  = f"{temp}°C"
    feel_txt  = f"{weather['feels_like']}°C"

    day_w   = draw.textbbox((0, 0), day_txt,  font=f_l)[2]
    desc_w  = draw.textbbox((0, 0), desc_txt, font=f_d)[2]
    temp_w  = draw.textbbox((0, 0), temp_txt, font=f_t)[2]
    feel_w  = draw.textbbox((0, 0), feel_txt, font=f_s)[2]

    day_desc_gap  = 18
    day_desc_w    = day_w + day_desc_gap + desc_w

    # Érzet sor: feel ikon + szöveg a hőfok jobb oldalán alul
    feel_icon_gap = 8 if feel_icon_img else 0
    feel_row_w    = (FEEL_ICON_SIZE + feel_icon_gap if feel_icon_img else 0) + feel_w

    text_block_w  = max(day_desc_w, temp_w)

    icon_gap = ICON_DISPLAY_SIZE + 30 if icon_img else 0
    block_w  = icon_gap + text_block_w

    if icon_img:
        paste_icon(img, icon_img, curr_x + ICON_OFFSET_X,
                   mid_y - ICON_DISPLAY_SIZE // 2)

    tx = curr_x + icon_gap

    # SZERDA  DERÜLT fejléc
    header_y = int(mid_y - 75)
    draw.text((tx, header_y), day_txt,  font=f_l, fill=colors["dim"])
    draw.text((tx + day_w + day_desc_gap, header_y), desc_txt, font=f_d, fill=colors["dim"])

    # Nagy hőfok
    temp_x = int(tx + (text_block_w - temp_w) / 2)
    temp_y = int(mid_y - 40)
    draw.text((temp_x, temp_y), temp_txt, font=f_t, fill=colors["main"])

    # Kis érzet: feel ikon + érték, közvetlenül a hőfok után jobbra, alul igazítva
    temp_bottom = temp_y + draw.textbbox((0, 0), temp_txt, font=f_t)[3]
    feel_start_x = temp_x + temp_w + 16
    feel_icon_y  = temp_bottom - FEEL_ICON_SIZE
    feel_text_y  = temp_bottom - draw.textbbox((0, 0), feel_txt, font=f_s)[3]

    if feel_icon_img:
        paste_icon(img, feel_icon_img, feel_start_x, feel_icon_y, size=FEEL_ICON_SIZE)
    draw.text((feel_start_x + (FEEL_ICON_SIZE + feel_icon_gap if feel_icon_img else 0),
               feel_text_y), feel_txt, font=f_s, fill=colors["dim"])

    # Blokk szélessége: text_block_w + érzet sor ha kilóg
    total_s1_w = icon_gap + max(text_block_w, temp_w + 16 + feel_row_w)
    curr_x += total_s1_w + 70
    draw.line([(curr_x, by + 40), (curr_x, by + bh - 40)], fill=colors["line"], width=3)
    curr_x += 55

    # ── SZEKCIÓ 2: SZÉL + PÁRA egymás alatt ─────────────────────────────────
    wind_label = "SZÉL"
    wind_val   = f"{weather['wind_kmh']} km/h"
    hum_label  = "PÁRA"
    hum_val    = f"{weather['humidity']}%"

    wind_lw = draw.textbbox((0, 0), wind_label, font=f_l)[2]
    wind_vw = draw.textbbox((0, 0), wind_val,   font=f_v)[2]
    hum_lw  = draw.textbbox((0, 0), hum_label,  font=f_l)[2]
    hum_vw  = draw.textbbox((0, 0), hum_val,    font=f_v)[2]
    col2_w  = max(wind_lw, wind_vw, hum_lw, hum_vw)

    # Szél felül, Pára alul – egyenletesen elosztva a widget magasságán belül
    row_gap = 10
    top_y   = mid_y - 52
    bot_y   = mid_y + row_gap

    draw.text((curr_x, top_y),        wind_label, font=f_l, fill=colors["dim"])
    draw.text((curr_x, top_y + 26),   wind_val,   font=f_v, fill=colors["main"])
    draw.text((curr_x, bot_y),        hum_label,  font=f_l, fill=colors["dim"])
    draw.text((curr_x, bot_y + 26),   hum_val,    font=f_v, fill=colors["main"])

    curr_x += col2_w + 55
    draw.line([(curr_x, by + 40), (curr_x, by + bh - 40)], fill=colors["line"], width=3)
    curr_x += 55

    # ── SZEKCIÓ 3: NAPKELTE + NAPNYUGTA ikonnal egymás alatt ─────────────────
    #   [day_clear ikon]  06:12
    #   [night_clear ikon] 19:45
    sun_icon_size = SUN_ICON_SIZE
    sun_time_gap  = 12

    sunrise_txt = weather["sunrise"]
    sunset_txt  = weather["sunset"]
    sr_tw = draw.textbbox((0, 0), sunrise_txt, font=f_v)[2]
    ss_tw = draw.textbbox((0, 0), sunset_txt,  font=f_v)[2]
    sun_col_w = max(sun_icon_size + sun_time_gap + sr_tw,
                    sun_icon_size + sun_time_gap + ss_tw)

    sr_icon_y = top_y
    ss_icon_y = bot_y

    if sunrise_icon_img:
        paste_icon(img, sunrise_icon_img, curr_x, sr_icon_y, size=sun_icon_size)
    draw.text((curr_x + sun_icon_size + sun_time_gap,
               sr_icon_y + (sun_icon_size - draw.textbbox((0,0), sunrise_txt, font=f_v)[3]) // 2),
              sunrise_txt, font=f_v, fill=colors["main"])

    if sunset_icon_img:
        paste_icon(img, sunset_icon_img, curr_x, ss_icon_y, size=sun_icon_size)
    draw.text((curr_x + sun_icon_size + sun_time_gap,
               ss_icon_y + (sun_icon_size - draw.textbbox((0,0), sunset_txt, font=f_v)[3]) // 2),
              sunset_txt, font=f_v, fill=colors["main"])

    curr_x += sun_col_w + 55
    draw.line([(curr_x, by + 40), (curr_x, by + bh - 40)], fill=colors["line"], width=3)
    curr_x += 55

    # ── SZEKCIÓ 4: 3 NAPOS ELŐREJELZÉS ikonnal ───────────────────────────────
    for i, day_entry in enumerate(weather["forecast"]):
        d_name   = get_day_hu(datetime.fromtimestamp(day_entry["dt"])).upper()[:3]
        f_val    = f"{round(day_entry['main']['temp'])}°C"
        d_name_w = draw.textbbox((0, 0), d_name, font=f_l)[2]
        f_val_w  = draw.textbbox((0, 0), f_val,  font=f_v)[2]
        col_w    = max(d_name_w, f_val_w, FORECAST_ICON_SIZE)

        fc_icon = forecast_icons[i] if i < len(forecast_icons) else None
        if fc_icon:
            icon_x = curr_x + (col_w - FORECAST_ICON_SIZE) // 2
            # Ikon a nap rövidítése felett, szorosan
            icon_y = mid_y - 45 - FORECAST_ICON_SIZE - 6
            paste_icon(img, fc_icon, icon_x, icon_y, size=FORECAST_ICON_SIZE)

        draw.text((curr_x + (col_w - d_name_w) // 2, mid_y - 45), d_name, font=f_l, fill=colors["dim"])
        draw.text((curr_x + (col_w - f_val_w)  // 2, mid_y),      f_val,  font=f_v, fill=colors["main"])
        curr_x += col_w + 35

    # ── SZEKCIÓ 5: NÉVNAP ────────────────────────────────────────────────────
    draw.line([(curr_x, by + 40), (curr_x, by + bh - 40)], fill=colors["line"], width=3)
    curr_x += 40

    nameday_value = ", ".join(n.strip().rstrip("\\") for n in namedays)
    draw.text((curr_x, mid_y - 45), "NÉVNAP",      font=f_l, fill=colors["dim"])
    draw.text((curr_x, mid_y),      nameday_value, font=f_n, fill=colors["main"])

    # ── DÁTUM + IDŐ – widget jobb felső sarok ────────────────────────────────
    datetime_txt = now_dt.strftime("%y.%m.%d  %H:%M")
    dt_w = draw.textbbox((0, 0), datetime_txt, font=f_dt)[2]
    draw.text((bx + bw - dt_w, by + 10), datetime_txt, font=f_dt,
              fill=(160, 160, 160, 200))
