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
FONT_TEMP   = 90   # Fő hőmérséklet
FONT_DESC   = 32   # Időjárás megnevezése (pl. DERÜLT)
FONT_LABEL  = 28   # Címkék és a Nap neve (pl. ÉRZET, HÉTFŐ)
FONT_VALUE  = 36   # Értékek (pl. 10 km/h)
FONT_UPDATE = 24   # Frissítve felirat
FONT_NAME   = 28   # Névnap felirat

# Ikon megjelenítési méret (80px-es PNG → felnagyítva)
ICON_DISPLAY_SIZE = 160   # px, 4K-n jól látható

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


def draw_weather_widget(img, weather, icon_img, namedays, tz_offset):
    """
    Rárajzolja a widget összes elemét a 4K-s képre.

    Paraméterek:
        img        : PIL Image (RGBA, 3840x2160)
        weather    : dict a logic_weather.get_weather_data() eredménye
        icon_img   : PIL Image (RGBA) – az aktuális időjárás ikonja
        namedays   : list[str] – mai névnapok
        tz_offset  : int – timezone offset másodpercben
    """
    from logic_weather import get_day_hu

    W, H = img.size
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
    f_t = get_f(FONT_TEMP,   bold=True)
    f_d = get_f(FONT_DESC)
    f_l = get_f(FONT_LABEL)
    f_v = get_f(FONT_VALUE,  bold=True)
    f_u = get_f(FONT_UPDATE)
    f_n = get_f(FONT_NAME)

    curr_x = int(bx + INNER_MARGIN)
    mid_y  = int(by + (bh // 2))

    now_dt     = weather["now_dt"]
    temp       = weather["temp"]
    weather_hu = weather["weather_hu"]

    # ── SZEKCIÓ 1: IKON + NAP + HŐFOK + LEÍRÁS ──────────────────────────────
    day_txt  = get_day_hu(now_dt).upper()
    temp_txt = f"{temp}°C"
    desc_txt = weather_hu.upper()

    day_w  = draw.textbbox((0, 0), day_txt,  font=f_l)[2]
    temp_w = draw.textbbox((0, 0), temp_txt, font=f_t)[2]
    desc_w = draw.textbbox((0, 0), desc_txt, font=f_d)[2]
    text_block_w = max(day_w, temp_w, desc_w)

    icon_gap = ICON_DISPLAY_SIZE + 30 if icon_img else 0
    block_w  = icon_gap + text_block_w

    # Ikon rajzolása (vertikálisan középre)
    if icon_img:
        icon_y = mid_y - ICON_DISPLAY_SIZE // 2
        paste_icon(img, icon_img, curr_x + ICON_OFFSET_X, icon_y)

    tx = curr_x + icon_gap
    draw.text((int(tx + (text_block_w - day_w)  / 2), int(mid_y - 85)), day_txt,  font=f_l, fill=colors["dim"])
    draw.text((int(tx + (text_block_w - temp_w) / 2), int(mid_y - 60)), temp_txt, font=f_t, fill=colors["main"])
    draw.text((int(tx + (text_block_w - desc_w) / 2), int(mid_y + 35)), desc_txt, font=f_d, fill=colors["dim"])

    curr_x += block_w + 70
    draw.line([(curr_x, by + 40), (curr_x, by + bh - 40)], fill=colors["line"], width=3)
    curr_x += 60

    # ── SZEKCIÓ 2: ÉRZET / SZÉL / PÁRA ──────────────────────────────────────
    fields = [
        ("Érzet", f"{weather['feels_like']}°C"),
        ("Szél",  f"{weather['wind_kmh']} km/h"),
        ("Pára",  f"{weather['humidity']}%"),
    ]
    for label, val in fields:
        draw.text((curr_x, mid_y - 45), label.upper(), font=f_l, fill=colors["dim"])
        draw.text((curr_x, mid_y),      val,            font=f_v, fill=colors["main"])
        lw = draw.textbbox((0, 0), label.upper(), font=f_l)[2]
        vw = draw.textbbox((0, 0), val,            font=f_v)[2]
        curr_x += max(lw, vw) + 80

    # ── SZEKCIÓ 3: 3 NAPOS ELŐREJELZÉS ───────────────────────────────────────
    draw.line([(curr_x, by + 40), (curr_x, by + bh - 40)], fill=colors["line"], width=3)
    curr_x += 60

    for day_entry in weather["forecast"]:
        d_name = get_day_hu(
            datetime.fromtimestamp(day_entry["dt"])
        ).upper()[:3]
        f_val = f"{round(day_entry['main']['temp'])}°C"
        draw.text((curr_x, mid_y - 45), d_name, font=f_l, fill=colors["dim"])
        draw.text((curr_x, mid_y),      f_val,  font=f_v, fill=colors["main"])
        curr_x += 140

    # ── SZEKCIÓ 4: FRISSÍTÉS ─────────────────────────────────────────────────
    draw.line([(curr_x, by + 40), (curr_x, by + bh - 40)], fill=colors["line"], width=3)
    curr_x += 40

    update_txt = f"FRISSÍTVE: {weather['update_time']}"
    draw.text((curr_x, mid_y - 12), update_txt, font=f_u, fill=colors["dim"])
    curr_x += draw.textbbox((0, 0), update_txt, font=f_u)[2] + 60

    # ── SZEKCIÓ 5: NÉVNAP ────────────────────────────────────────────────────
    draw.line([(curr_x, by + 40), (curr_x, by + bh - 40)], fill=colors["line"], width=3)
    curr_x += 40

    nameday_label = "NÉVNAP"
    nameday_value = ", ".join(namedays)

    draw.text((curr_x, mid_y - 45), nameday_label, font=f_l, fill=colors["dim"])
    draw.text((curr_x, mid_y),      nameday_value, font=f_n, fill=colors["main"])
