from PIL import Image, ImageDraw, ImageFont, ImageStat
from datetime import datetime
import os

# --- KONFIGURÁCIÓ & MÉRETEK (4K HORIZONTÁLIS) ---
WIDGET_WIDTH   = 2270
WIDGET_HEIGHT  = 200
WIDGET_Y       = 100
OFFSET_LEFT    = 200
INNER_MARGIN   = 80

FONT_TEMP         = 104
FONT_HEADER       = 24
FONT_VALUE        = 36
FONT_SMALL        = 30
FONT_DATETIME     = 22
FONT_NAME         = 28
FONT_FORECAST_DAY = 22
FONT_FORECAST_TEMP = 32

ICON_DISPLAY_SIZE  = 160
WIND_ICON_SIZE     = 36
PARA_ICON_SIZE     = 36
FORECAST_ICON_SIZE = 50
SUN_ICON_SIZE      = 40

GRADIENT_OFFSET = 10  # háttér jobbra tolás pixelben


def find_font(bold=False, heavy=False):
    font_dir = os.path.join(os.path.dirname(__file__), "Data", "Fonts")

    if heavy:
        name = "SFProText-Heavy.ttf"
    elif bold:
        name = "SFProText-Bold.ttf"
    else:
        name = "SFProText-Regular.ttf"

    path = os.path.join(font_dir, name)
    if os.path.exists(path):
        return path

    fallbacks = [
        os.path.join(font_dir, "SFProText-Medium.ttf"),
        os.path.join(font_dir, "SFProText-Semibold.ttf"),
        "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf"    if bold else "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    return next((f for f in fallbacks if os.path.exists(f)), None)


def get_f(size, bold=False, heavy=False):
    path = find_font(bold=bold, heavy=heavy)
    if not path:
        return ImageFont.load_default()
    size = size if size % 2 == 0 else size + 1
    font = ImageFont.truetype(path, size)
    try:
        font.fontmode = "RGB"
    except Exception:
        pass
    return font


def paste_icon(img, icon_img, x, y, size=ICON_DISPLAY_SIZE):
    if not icon_img:
        return
    resized = icon_img.resize((size, size), Image.Resampling.LANCZOS)
    img.paste(resized, (int(x), int(y)), resized)


def draw_weather_widget(
    img, weather,
    icon_img, feel_icon_img, rainq_icon_img,
    wind1_icon_img, para_icon_img,
    forecast_icons,
    sunrise_icon_img, sunset_icon_img,
    namedays, tz_offset
):
    from logic_weather import get_day_hu

    bx, by, bw, bh = OFFSET_LEFT, WIDGET_Y, WIDGET_WIDTH, WIDGET_HEIGHT

    # Automatikus sötét / világos mód
    brightness = ImageStat.Stat(img.crop((bx, by, bx + bw, by + bh)).convert("L")).mean[0]

    if brightness > 145:
        colors = {
            "main":     (20,  20,  35,  255),
            "dim":      (120, 110, 140, 200),
            "line":     (0,   0,   0,   12),
            "accent":   (255, 100, 50,  255),
            "accent2":  (0,   200, 180, 255),
            "bg_start": (255, 255, 245, 220),
            "bg_end":   (245, 240, 255, 220),
        }
    else:
        colors = {
            "main":     (255, 255, 255, 255),
            "dim":      (150, 155, 180, 200),
            "line":     (100, 150, 255, 30),
            "accent":   (0,   230, 200, 255),
            "accent2":  (180, 100, 255, 255),
            "bg_start": (18,  18,  28,  210),
            "bg_end":   (28,  18,  38,  210),
        }

    draw = ImageDraw.Draw(img)

    # GRADIENT HÁTTÉR
    gx = bx + GRADIENT_OFFSET
    bs, be = colors["bg_start"], colors["bg_end"]
    for y in range(by, by + bh):
        t = (y - by) / bh
        r = int(bs[0] + (be[0] - bs[0]) * t)
        g = int(bs[1] + (be[1] - bs[1]) * t)
        b = int(bs[2] + (be[2] - bs[2]) * t)
        draw.line([(gx, y), (gx + bw - GRADIENT_OFFSET, y)], fill=(r, g, b, bs[3]), width=1)

    mid_y  = by + bh // 2
    curr_x = bx + INNER_MARGIN

    # Betűtípusok
    f_t  = get_f(FONT_TEMP,          heavy=True)
    f_h  = get_f(FONT_HEADER,        bold=True)
    f_v  = get_f(FONT_VALUE,         heavy=True)
    f_s  = get_f(FONT_SMALL)
    f_dt = get_f(FONT_DATETIME)
    f_n  = get_f(FONT_NAME,          bold=True)
    f_fd = get_f(FONT_FORECAST_DAY,  bold=True)
    f_fv = get_f(FONT_FORECAST_TEMP, heavy=True)

    # ── 1. AKTUÁLIS BLOKK ──────────────────────────────────────────────
    SEC1_W   = 820
    temp_txt = f"{weather['temp']}°C"
    feel_txt = f"{weather['feels_like']}°C"
    rain_txt = f"{weather.get('pop', 0)}%"

    t_bbox = draw.textbbox((0, 0), temp_txt, font=f_t)
    t_w    = t_bbox[2]

    main_content_w = ICON_DISPLAY_SIZE + 40 + t_w + 60 + 110
    start_x        = (curr_x + SEC1_W // 2) - main_content_w // 2

    paste_icon(img, icon_img, start_x, mid_y - ICON_DISPLAY_SIZE // 2)
    tx = start_x + ICON_DISPLAY_SIZE + 40
    ty = mid_y - t_bbox[3] // 2 + 5

    day_str = get_day_hu(weather["now_dt"]).upper()
    draw.text((tx + 20, mid_y - 65), day_str, font=f_h, fill=colors["accent2"])
    day_w = draw.textbbox((0, 0), day_str, font=f_h)[2]
    draw.text((tx + 20 + day_w + 30, mid_y - 65), weather["weather_hu"].upper(), font=f_h, fill=colors["accent"])

    draw.text((tx, ty), temp_txt, font=f_t, fill=colors["main"])

    info_x = tx + t_w + 60
    if rainq_icon_img:
        paste_icon(img, rainq_icon_img, info_x, mid_y - 42, size=42)
    draw.text((info_x + 52, mid_y - 42), rain_txt, font=f_s, fill=colors["dim"])

    if feel_icon_img:
        paste_icon(img, feel_icon_img, info_x + 4, mid_y + 8, size=36)
    draw.text((info_x + 52, mid_y + 8), feel_txt, font=f_s, fill=colors["dim"])

    curr_x += SEC1_W
    draw.line([(curr_x, by + 50), (curr_x, by + bh - 50)], fill=colors["line"], width=2)

    # ── 2. SZÉL & PÁRA ────────────────────────────────────────────────
    SEC2_W = 300
    ix     = curr_x + 70
    for i, (val, unit, icon, sz) in enumerate([
        (weather["wind_kmh"], " km/h", wind1_icon_img, WIND_ICON_SIZE),
        (weather["humidity"], "%",     para_icon_img,  PARA_ICON_SIZE),
    ]):
        y_pos = mid_y - 68 if i == 0 else mid_y + 12
        if icon:
            paste_icon(img, icon, ix, y_pos + 4, size=sz)
        draw.text((ix + 58, y_pos), f"{val}{unit}", font=f_v, fill=colors["main"])

    curr_x += SEC2_W
    draw.line([(curr_x, by + 50), (curr_x, by + bh - 50)], fill=colors["line"], width=2)

    # ── 3. NAPKELTE / NAPNYUGTA ───────────────────────────────────────
    SEC3_W = 260
    sx     = curr_x + 70
    for i, (val, icon) in enumerate([
        (weather["sunrise"], sunrise_icon_img),
        (weather["sunset"],  sunset_icon_img),
    ]):
        y_pos = mid_y - 65 if i == 0 else mid_y + 10
        if icon:
            paste_icon(img, icon, sx, y_pos + 6, size=SUN_ICON_SIZE)
        draw.text((sx + 58, y_pos), val, font=f_v, fill=colors["main"])

    curr_x += SEC3_W
    draw.line([(curr_x, by + 50), (curr_x, by + bh - 50)], fill=colors["line"], width=2)

    # ── 4. ELŐREJELZÉS (3 NAP) ────────────────────────────────────────
    SEC4_W = 540
    slot_w = 180
    for i, day_entry in enumerate(weather["forecast"]):
        sm = curr_x + i * slot_w + slot_w // 2
        dn = get_day_hu(datetime.fromtimestamp(day_entry["dt"])).upper()[:3]
        fv = f"{round(day_entry['main']['temp'])}°C"

        if i < len(forecast_icons):
            paste_icon(img, forecast_icons[i], sm - 25, mid_y - 75, size=50)

        draw.text((sm - draw.textbbox((0, 0), dn, font=f_fd)[2] // 2, mid_y - 15), dn, font=f_fd, fill=colors["accent2"])
        draw.text((sm - draw.textbbox((0, 0), fv, font=f_fv)[2] // 2, mid_y + 15), fv, font=f_fv, fill=colors["main"])

        pop_val = day_entry.get("pop", 0)
        if pop_val > 0:
            pop_txt = f"{round(pop_val * 100)}%"
            draw.text((sm - draw.textbbox((0, 0), pop_txt, font=f_s)[2] // 2, mid_y + 45), pop_txt, font=f_s, fill=colors["accent"])

    curr_x += SEC4_W
    draw.line([(curr_x, by + 50), (curr_x, by + bh - 50)], fill=colors["line"], width=2)

    # ── 5. NÉVNAP & IDŐ ──────────────────────────────────────────────
    draw.text((curr_x + 50, mid_y - 50), "NÉVNAP",           font=f_h, fill=colors["accent2"])
    draw.text((curr_x + 50, mid_y - 2),  ", ".join(namedays), font=f_n, fill=colors["main"])

    dt_txt = weather["now_dt"].strftime("%Y.%m.%d  %H:%M")
    dt_w   = draw.textbbox((0, 0), dt_txt, font=f_dt)[2]
    draw.text((bx + bw - dt_w - 20, by + 15), dt_txt, font=f_dt, fill=colors["dim"])
