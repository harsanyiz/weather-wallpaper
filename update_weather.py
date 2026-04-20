import requests
import json
import os
import time  # <--- Hozzáadva az időbélyeghez
from datetime import datetime, timezone, timedelta
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageStat

API_KEY = os.environ.get("OWM_API_KEY")
GITHUB_USER = "harsanyiz"
GITHUB_REPO = "weather-wallpaper"
BRANCH = "main"
BASE_URL = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/{BRANCH}/images"

# ============================================================
# KONFIGURÁCIÓ - EZT A RÉSZT FRISSÍTI A DESIGNER
# ============================================================
CITY = "Budapest"
WIDGET_WIDTH = 300
WIDGET_X = 1555
WIDGET_Y = 265
CORNER_RADIUS = 24
INNER_MARGIN = 30
COLUMNS = 1
FORECAST_DAYS = 3

# Betűméretek
FONT_TEMP = 68
FONT_LABEL = 15
FONT_VALUE = 17
FONT_FOOTER = 12
FONT_FORECAST = 14

# Megjelenítendő adatok (sorrendben!)
VISIBLE_FIELDS = ["feels","weather","clouds","rain_chance","humidity","wind"]

# Üveglap stílus: "auto", "dark", "light", "custom"
GLASS_STYLE = "auto"
# Egyéni szín (HSL) - csak ha GLASS_STYLE = "custom"
CUSTOM_GLASS_HSL = None
# ============================================================

FONT_PATHS_REGULAR = [
    "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
    "/usr/share/fonts/truetype/noto/NotoSans[wdth,wght].ttf",
    "/usr/share/fonts/noto/NotoSans-Regular.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
]
FONT_PATHS_BOLD = [
    "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf",
    "/usr/share/fonts/truetype/noto/NotoSans[wdth,wght].ttf",
    "/usr/share/fonts/noto/NotoSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]
FONT_PATHS_EMOJI = [
    "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf",
    "/usr/share/fonts/noto/NotoColorEmoji.ttf",
    "/usr/share/fonts/truetype/noto/NotoEmoji-Regular.ttf",
]

def find_font(bold=False):
    paths = FONT_PATHS_BOLD if bold else FONT_PATHS_REGULAR
    for p in paths:
        if os.path.exists(p): return p
    return None

def find_emoji_font():
    for p in FONT_PATHS_EMOJI:
        if os.path.exists(p): return p
    return None

def get_f(size, bold=False):
    path = find_font(bold)
    if path: return ImageFont.truetype(path, size)
    return ImageFont.load_default()

def get_emoji_f(size):
    path = find_emoji_font()
    if path:
        try: return ImageFont.truetype(path, size)
        except: pass
    return None

def draw_text_with_emoji(draw, pos, text, font, emoji_font, fill):
    """Szöveget rajzol – ha van emoji font, azzal rajzolja az emoji karaktereket"""
    if emoji_font is None:
        draw.text(pos, text, font=font, fill=fill)
        return
    x, y = pos
    for char in text:
        if ord(char) > 127 and emoji_font:
            try:
                draw.text((x, y), char, font=emoji_font, fill=fill, embedded_color=True)
                bb = draw.textbbox((0, 0), char, font=emoji_font)
                x += bb[2] - bb[0]
            except:
                draw.text((x, y), char, font=font, fill=fill)
                bb = draw.textbbox((0, 0), char, font=font)
                x += bb[2] - bb[0]
        else:
            draw.text((x, y), char, font=font, fill=fill)
            bb = draw.textbbox((0, 0), char, font=font)
            x += bb[2] - bb[0]

def get_image_name(weather_id, is_night):
    suffix = "night" if is_night else "day"
    if weather_id in [611, 612, 613, 615, 616]: return f"sleet_{suffix}"
    elif weather_id in [620, 621, 622, 600, 601, 602]: return f"snow_{suffix}"
    elif weather_id in [511]: return f"hail_{suffix}"
    elif weather_id in [781, 771, 762, 761, 751, 731, 721, 711, 701]: return f"foggy_{suffix}"
    elif weather_id in range(200, 233): return f"hail_{suffix}"
    elif weather_id in range(500, 532): return f"rainy_{suffix}"
    elif weather_id in range(300, 322): return f"rainy_{suffix}"
    elif weather_id == 800: return f"sunny_{suffix}"
    else: return f"cloudy_{suffix}"

def get_weather_hu(weather_id):
    mapping = {800: "Der\u00fclt", 801: "Enyh\u00e9n felh\u0151s", 802: "Enyh\u00e9n felh\u0151s",
               803: "Felh\u0151s", 804: "Felh\u0151s", 511: "J\u00e9ges\u0151"}
    if weather_id in mapping: return mapping[weather_id]
    if weather_id in range(600, 623): return "Havaz\u00e1s"
    if weather_id in range(200, 233): return "Zivatar"
    if weather_id in range(500, 532): return "Es\u0151"
    if weather_id in range(300, 322): return "Szit\u00e1l\u00e1s"
    return "V\u00e1ltoz\u00e9kony"

def get_weather_icon(weather_id, is_night):
    if weather_id in [611, 612, 613, 615, 616]: return "\U0001f328\ufe0f"
    elif weather_id in [620, 621, 622, 600, 601, 602]: return "\u2744\ufe0f"
    elif weather_id == 511: return "\U0001f9ca"
    elif weather_id in [781, 771, 762, 761, 751, 731, 721, 711, 701]: return "\U0001f32b\ufe0f"
    elif weather_id in range(200, 233): return "\u26c8\ufe0f"
    elif weather_id in range(500, 532): return "\U0001f327\ufe0f"
    elif weather_id in range(300, 322): return "\U0001f326\ufe0f"
    elif weather_id == 800: return "\U0001f319" if is_night else "\u2600\ufe0f"
    elif weather_id in [801, 802]: return "\U0001f31c" if is_night else "\u26c5"
    else: return "\u2601\ufe0f"

def get_forecast_icon(d):
    icons = ["\u2600\ufe0f", "\u26c5", "\u2601\ufe0f", "\U0001f327\ufe0f", "\u26c8\ufe0f"]
    return icons[(d-1) % len(icons)]

def get_rain_chance(weather_id):
    if weather_id in range(200, 233): return 80
    if weather_id in range(500, 532): return 70
    if weather_id == 800: return 0
    return 20

def hsl_to_rgba(h, s, l, a):
    s /= 100; l /= 100
    c = (1 - abs(2 * l - 1)) * s
    hp = h / 60
    x = c * (1 - abs((hp % 2) - 1))
    if hp <= 1: r1, g1, b1 = c, x, 0
    elif hp <= 2: r1, g1, b1 = x, c, 0
    elif hp <= 3: r1, g1, b1 = 0, c, x
    elif hp <= 4: r1, g1, b1 = 0, x, c
    elif hp <= 5: r1, g1, b1 = x, 0, c
    else: r1, g1, b1 = c, 0, x
    m = l - c / 2
    return (round((r1+m)*255), round((g1+m)*255), round((b1+m)*255), round(a*2.55))

def get_glass_color(brightness):
    if GLASS_STYLE == "custom" and CUSTOM_GLASS_HSL and len(CUSTOM_GLASS_HSL) == 4:
        return hsl_to_rgba(*CUSTOM_GLASS_HSL)
    elif GLASS_STYLE == "dark": return (0, 0, 0, 140)
    elif GLASS_STYLE == "light": return (255, 255, 255, 140)
    else: return (255, 255, 255, 140) if brightness > 145 else (0, 0, 0, 110)

def get_text_colors(brightness):
    is_light = (
        GLASS_STYLE == "light" or
        (GLASS_STYLE == "custom" and CUSTOM_GLASS_HSL and len(CUSTOM_GLASS_HSL) == 4 and CUSTOM_GLASS_HSL[2] > 50) or
        (GLASS_STYLE == "auto" and brightness > 145)
    )
    if is_light:
        return {"main": (0,0,0,230), "dim": (0,0,0,130), "line": (0,0,0,40)}
    else:
        return {"main": (255,255,255,255), "dim": (255,255,255,140), "line": (255,255,255,30)}

def create_blurred_card(image, box_x, box_y, box_width, box_height, glass_color, radius=30, blur_strength=18):
    box_area = image.crop((box_x, box_y, box_x + box_width, box_y + box_height))
    blurred = box_area.filter(ImageFilter.GaussianBlur(blur_strength))
    mask = Image.new("L", (box_width, box_height), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, box_width, box_height), radius=radius, fill=255)
    glass = Image.new("RGBA", (box_width, box_height), glass_color)
    blurred = blurred.convert("RGBA")
    blurred.putalpha(mask)
    result = Image.alpha_composite(blurred, glass)
    border_color = (255, 255, 255, 50) if glass_color[0] < 128 else (0, 0, 0, 30)
    border = Image.new("RGBA", (box_width, box_height), (0, 0, 0, 0))
    ImageDraw.Draw(border).rounded_rectangle((1, 1, box_width-1, box_height-1), radius=radius, outline=border_color, width=1)
    border.putalpha(mask)
    return Image.alpha_composite(result, border)

def main():
    try:
        resp = requests.get(f"https://api.openweathermap.org/data/2.5/weather?q={CITY}&appid={API_KEY}&units=metric")
        data = resp.json()
        temp       = round(data["main"]["temp"])
        feels      = round(data["main"]["feels_like"])
        humidity   = data["main"]["humidity"]
        wind       = round(data["wind"]["speed"] * 3.6)
        weather_id = data["weather"][0]["id"]
        tz_offset  = data.get("timezone", 3600)
        now_dt     = datetime.now(timezone(timedelta(seconds=tz_offset)))
        weather_hu  = get_weather_hu(weather_id)
        rain_chance = get_rain_chance(weather_id)
        is_night    = now_dt.timestamp() < data["sys"]["sunrise"] or now_dt.timestamp() > data["sys"]["sunset"]
        image_name  = get_image_name(weather_id, is_night)
    except Exception as e:
        print(f"Hiba: {e}")
        return

    src, dst = f"images/{image_name}.jpg", "images/current.jpg"
    img = Image.open(src).convert("RGB")
    W, H = img.size

    active_fields   = [f for f in VISIBLE_FIELDS if f != "temp"]
    row_h           = 55
    forecast_height = (20 + FONT_FORECAST + 10 + FORECAST_DAYS * 48) if FORECAST_DAYS > 0 else 0
    bh = 40 + (FONT_TEMP + 28) + (len(active_fields) * row_h) + forecast_height + 50
    bw = WIDGET_WIDTH
    bx = max(0, min(WIDGET_X, W - bw))
    by = max(0, min(WIDGET_Y, H - bh))

    region         = img.crop((bx, by, bx + bw, by + bh)).convert("L")
    avg_brightness = ImageStat.Stat(region).mean[0]
    glass_c        = get_glass_color(avg_brightness)
    colors         = get_text_colors(avg_brightness)

    card = create_blurred_card(img, bx, by, bw, bh, glass_c, CORNER_RADIUS)
    img  = img.convert("RGBA")
    img.paste(card, (bx, by), card)
    draw = ImageDraw.Draw(img)

    f_t      = get_f(FONT_TEMP, True)
    f_l      = get_f(FONT_LABEL)
    f_v      = get_f(FONT_VALUE, True)
    f_f      = get_f(FONT_FOOTER)
    f_fc     = get_f(FONT_FORECAST)
    f_emoji  = get_emoji_f(FONT_LABEL + 2)
    f_emoji_fc = get_emoji_f(FONT_FORECAST + 2)

    emoji_path = find_emoji_font()
    print(f"Font: {find_font(False) or 'default'}")
    print(f"Emoji font: {emoji_path or 'nincs - szoveg fallback'}")

    m  = INNER_MARGIN
    cy = by + 35

    # Homerseklet + ido ikon kozepen
    weather_icon = get_weather_icon(weather_id, is_night)
    txt = f"{temp}\u00b0C"
    tw  = draw.textbbox((0, 0), txt, font=f_t)[2]
    # Ikon a homerseklet fole kozepre
    if f_emoji:
        try:
            iw = draw.textbbox((0,0), weather_icon, font=f_emoji)[2]
            draw.text((bx + (bw - iw) // 2, cy), weather_icon, font=f_emoji, fill=colors["main"], embedded_color=True)
            cy += FONT_LABEL + 8
        except:
            pass
    draw.text((bx + (bw - tw) // 2, cy), txt, font=f_t, fill=colors["main"])
    cy += FONT_TEMP + 28

    field_labels = {
        "feels":      "\u00c9RZET",
        "weather":    "ID\u0150J\u00c1R\u00c1S",
        "rain_chance":"CSAPAD\u00c9K",
        "humidity":   "P\u00c1RA",
        "wind":       "SZ\u00c9L",
        "pressure":   "L\u00c9GNYOM\u00c1S",
        "uv":         "UV",
        "visibility": "L\u00c1T\u00d3T\u00c1V",
        "gust":       "SZ\u00c9LL\u00d6K\u00c9S",
        "clouds":     "FELH\u0150ZET"
    }
    field_icons = {
        "feels":      "\U0001f321\ufe0f",
        "weather":    weather_icon,
        "rain_chance":"\U0001f327\ufe0f",
        "humidity":   "\U0001f4a7",
        "wind":       "\U0001f32c\ufe0f",
        "pressure":   "\U0001f4cf",
        "uv":         "\u2600\ufe0f",
        "visibility": "\U0001f441\ufe0f",
        "gust":       "\U0001f300",
        "clouds":     "\u2601\ufe0f"
    }
    field_values = {
        "feels":      f"{feels} \u00b0C",
        "weather":    weather_hu.upper(),
        "rain_chance":f"{rain_chance}%",
        "humidity":   f"{humidity}%",
        "wind":       f"{wind} km/h",
        "pressure":   f"{data['main']['pressure']} hPa",
        "uv":         "3",
        "visibility": f"{data.get('visibility', 10000)//1000} km",
        "gust":       f"{round(data['wind'].get('gust', data['wind']['speed']) * 3.6)} km/h",
        "clouds":     f"{data.get('clouds', {}).get('all', 45)}%"
    }

    icon_size = FONT_LABEL + 2
    for field in active_fields:
        icon = field_icons.get(field, "")
        label = field_labels.get(field, field)
        val = field_values.get(field, "")

        # Ikon + label bal oldalon
        lx = bx + m
        if f_emoji and icon:
            try:
                draw.text((lx, cy), icon, font=f_emoji, fill=colors["dim"], embedded_color=True)
                iw = draw.textbbox((0,0), icon, font=f_emoji)[2]
                lx += iw + 6
            except:
                pass
        draw.text((lx, cy), label, font=f_l, fill=colors["dim"])

        # Ertek jobb oldalon
        vw = draw.textbbox((0, 0), val, font=f_v)[2]
        draw.text((bx + bw - m - vw, cy), val, font=f_v, fill=colors["main"])

        line_y = cy + row_h - 8
        draw.line([(bx + m, line_y), (bx + bw - m, line_y)], fill=colors["line"], width=1)
        cy += row_h

    # Eloreljelzes
    if FORECAST_DAYS > 0:
        cy += 10
        draw.line([(bx + m, cy), (bx + bw - m, cy)], fill=colors["line"], width=1)
        cy += 15
        elore = "EL\u0150REJELZ\u00c9S"
        etw   = draw.textbbox((0, 0), elore, font=f_fc)[2]
        draw.text((bx + (bw - etw) // 2, cy), elore, font=f_fc, fill=colors["dim"])
        cy += FONT_FORECAST + 10
        fc_labels = ["HOLNAP", "HOLNAPUTÁN", "+3 NAP", "+4 NAP", "+5 NAP"]
        for d in range(1, FORECAST_DAYS + 1):
            day_name = fc_labels[d-1] if d <= len(fc_labels) else f"+{d} NAP"
            temp_fc  = temp - d * 2
            draw.text((bx + m, cy), day_name, font=f_fc, fill=colors["dim"])
            # Ikon kozepen
            if f_emoji_fc:
                try:
                    fc_icon = get_forecast_icon(d)
                    iw = draw.textbbox((0,0), fc_icon, font=f_emoji_fc)[2]
                    draw.text((bx + (bw - iw) // 2, cy), fc_icon, font=f_emoji_fc, fill=colors["dim"], embedded_color=True)
                except:
                    pass
            fc_val = f"{temp_fc}\u00b0C"
            fvw    = draw.textbbox((0, 0), fc_val, font=f_fc)[2]
            draw.text((bx + bw - m - fvw, cy), fc_val, font=f_fc, fill=colors["main"])
            cy += 48

    # Footer
    cy += 10
    now_str = now_dt.strftime("%Y.%m.%d.  %H:%M")
    ftxt = f"{CITY.upper()}  \u2022  {now_str}"
    fw   = draw.textbbox((0, 0), ftxt, font=f_f)[2]
    draw.text((bx + (bw - fw) // 2, cy), ftxt, font=f_f, fill=colors["dim"])

    img.convert("RGB").save(dst, "JPEG", quality=95)
    print("current.jpg mentve")

    # ============================================================
    # MÓDOSÍTOTT RÉSZ: Dinamikus URL a cache ellen
    # ============================================================
    v_param = int(time.time())
    image_url = f"{BASE_URL}/current.jpg?v={v_param}"
    
    weather_json = {
        "location": CITY, 
        "title": f"{weather_hu} {temp}C",
        "author": "OpenWeatherMap", 
        "image_url": image_url
    }
    
    with open("weather.json", "w", encoding="utf-8") as f:
        json.dump(weather_json, f, ensure_ascii=False, indent=2)
    print(f"weather.json kesz (URL: {image_url})")

if __name__ == "__main__":
    main()
