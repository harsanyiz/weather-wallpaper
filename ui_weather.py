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
FONT_DATETIME = 24   # Dátum+idő jobb felső sarok
FONT_NAME     = 28   # Névnap felirat

# Ikon megjelenítési méret (80px-es PNG → felnagyítva)
ICON_DISPLAY_SIZE    = 160   # px – aktuális időjárás ikon
FEEL_ICON_SIZE       = 44    # feel.png – érzet ikon, az érték mellett balra
FORECAST_ICON_SIZE   = 60    # előrejelzés ikonok a nap neve felett

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


def draw_weather_widget(img, weather, icon_img, feel_icon_img, forecast_icons, namedays, tz_offset):
    """
    Rárajzolja a widget összes elemét a 4K-s képre.

    Paraméterek:
        img            : PIL Image (RGBA, 3840x2160)
        weather        : dict – logic_weather.get_weather_data() eredménye
        icon_img       : PIL Image (RGBA) – aktuális időjárás ikonja
        feel_icon_img  : PIL Image (RGBA) – feel.png, érzet hőfok mellé balra
        forecast_icons : list[PIL Image | None] – 3 napos előrejelzés ikonjai
        namedays       : list[str] – mai névnapok
        tz_offset      : int – timezone offset másodpercben
    """
    from logic_weather import get_day_hu

    bx = OFFSET_LEFT
    by = WIDGET_Y
    bw = WIDGET_WIDTH
    bh = WIDGET_HEIGHT

    # Háttér brightness → szövegszín
    region = img.crop((bx, by, bx + bw, by + bh)).convert("L")
    avg_brightness = ImageStat.Stat(region).mean[0]
    colors = get_text_colors(avg_brightness)

    draw = ImageDraw.Draw(img)

    # Betűtípusok
    f_t  = get_f(FONT_TEMP,     bold=True)
    f_d  = get_f(FONT_DESC)
    f_l  = get_f(FONT_LABEL)
    f_v  = get_f(FONT_VALUE,    bold=True)
    f_dt = get_f(FONT_DATETIME)
    f_n  = get_f(FONT_NAME)

    curr_x = int(bx + INNER_MARGIN)
    mid_y  = int(by + (bh // 2))

    now_dt     = weather["now_dt"]
    temp       = weather["temp"]
    weather_hu = weather["weather_hu"]

    # ── SZEKCIÓ 1: IKON + NAP+LEÍRÁS egy sorban + HŐFOK ─────────────────────
    day_txt  = get_day_hu(now_dt).upper()
    desc_txt = weather_hu.upper()
    temp_txt = f"{temp}°C"

    day_w  = draw.textbbox((0, 0), day_txt,  font=f_l)[2]
    desc_w = draw.textbbox((0, 0), desc_txt, font=f_d)[2]
    temp_w = draw.textbbox((0, 0), temp_txt, font=f_t)[2]

    day_desc_gap = 18
    day_desc_w   = day_w + day_desc_gap + desc_w
    text_block_w = max(day_desc_w, temp_w)

    icon_gap = ICON_DISPLAY_SIZE + 30 if icon_img else 0
    block_w  = icon_gap + text_block_w

    if icon_img:
        icon_y = mid_y - ICON_DISPLAY_SIZE // 2
        paste_icon(img, icon_img, curr_x + ICON_OFFSET_X, icon_y)

    tx = curr_x + icon_gap
    header_y = int(mid_y - 75)
    draw.text((tx, header_y), day_txt,  font=f_l, fill=colors["dim"])
    draw.text((tx + day_w + day_desc_gap, header_y), desc_txt, font=f_d, fill=colors["dim"])
    draw.text((int(tx + (text_block_w - temp_w) / 2), int(mid_y - 40)), temp_txt, font=f_t, fill=colors["main"])

    curr_x += block_w + 70
    draw.line([(curr_x, by + 40), (curr_x, by + bh - 40)], fill=colors["line"], width=3)
    curr_x += 60

    # ── SZEKCIÓ 2: ÉRZET (feel.png bal oldalt) + SZÉL + PÁRA ────────────────
    #   Érzet: [feel ikon] [érték]  egymás mellett egy sorban, középre igazítva
    feel_val = f"{weather['feels_like']}°C"
    feel_vw  = draw.textbbox((0, 0), feel_val, font=f_v)[2]

    # feel ikon + rés + érték szélessége összesen
    feel_gap      = 10 if feel_icon_img else 0
    feel_total_w  = (FEEL_ICON_SIZE + feel_gap if feel_icon_img else 0) + feel_vw

    feel_icon_y = mid_y - FEEL_ICON_SIZE // 2   # vertikálisan középre
    if feel_icon_img:
        paste_icon(img, feel_icon_img, curr_x, feel_icon_y, size=FEEL_ICON_SIZE)

    draw.text((curr_x + (FEEL_ICON_SIZE + feel_gap if feel_icon_img else 0), mid_y - feel_vw // 4),
              feel_val, font=f_v, fill=colors["main"])
    curr_x += feel_total_w + 80

    # Szél, Pára – szöveges label fölül, érték alul
    for label, val in [("Szél", f"{weather['wind_kmh']} km/h"), ("Pára", f"{weather['humidity']}%")]:
        draw.text((curr_x, mid_y - 45), label.upper(), font=f_l, fill=colors["dim"])
        draw.text((curr_x, mid_y),      val,            font=f_v, fill=colors["main"])
        lw = draw.textbbox((0, 0), label.upper(), font=f_l)[2]
        vw = draw.textbbox((0, 0), val,            font=f_v)[2]
        curr_x += max(lw, vw) + 80

    # ── SZEKCIÓ 3: 3 NAPOS ELŐREJELZÉS ikonnal ───────────────────────────────
    draw.line([(curr_x, by + 40), (curr_x, by + bh - 40)], fill=colors["line"], width=3)
    curr_x += 60

    for i, day_entry in enumerate(weather["forecast"]):
        d_name = get_day_hu(
            datetime.fromtimestamp(day_entry["dt"])
        ).upper()[:3]
        f_val  = f"{round(day_entry['main']['temp'])}°C"
        d_name_w = draw.textbbox((0, 0), d_name, font=f_l)[2]
        f_val_w  = draw.textbbox((0, 0), f_val,  font=f_v)[2]
        col_w    = max(d_name_w, f_val_w, FORECAST_ICON_SIZE)

        # Ikon a nap neve fölé, középre igazítva az oszlopon belül
        fc_icon = forecast_icons[i] if i < len(forecast_icons) else None
        if fc_icon:
            icon_x = curr_x + (col_w - FORECAST_ICON_SIZE) // 2
            icon_y = mid_y - FORECAST_ICON_SIZE - d_name_w - 8
            paste_icon(img, fc_icon, icon_x, icon_y, size=FORECAST_ICON_SIZE)

        draw.text((curr_x + (col_w - d_name_w) // 2, mid_y - 45), d_name, font=f_l, fill=colors["dim"])
        draw.text((curr_x + (col_w - f_val_w)  // 2, mid_y),      f_val,  font=f_v, fill=colors["main"])
        curr_x += col_w + 30

    # ── SZEKCIÓ 4: NÉVNAP ────────────────────────────────────────────────────
    draw.line([(curr_x, by + 40), (curr_x, by + bh - 40)], fill=colors["line"], width=3)
    curr_x += 40

    nameday_label = "NÉVNAP"
    # Névnapok vesszővel elválasztva (\ helyett)
    nameday_value = ", ".join(n.strip().rstrip("\\") for n in namedays)
    draw.text((curr_x, mid_y - 45), nameday_label, font=f_l, fill=colors["dim"])
    draw.text((curr_x, mid_y),      nameday_value, font=f_n, fill=colors["main"])

    # ── DÁTUM + IDŐ – widget jobb felső sarka ────────────────────────────────
    # Formátum: 26.04.22  11:41  (YY.MM.DD  HH:MM)
    datetime_txt = now_dt.strftime("%y.%m.%d  %H:%M")
    dt_w  = draw.textbbox((0, 0), datetime_txt, font=f_dt)[2]
    dt_x  = bx + bw - dt_w
    dt_y  = by + 10
    # Szürke szín a brightness-től függetlenül (izléses, visszafogott)
    grey  = (160, 160, 160, 200)
    draw.text((dt_x, dt_y), datetime_txt, font=f_dt, fill=grey)
