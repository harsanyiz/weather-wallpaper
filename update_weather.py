import requests
import json
import os
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
WIDGET_WIDTH = 325
WIDGET_X = 1560
WIDGET_Y = 205
CORNER_RADIUS = 26
INNER_MARGIN = 34
COLUMNS = 1
FORECAST_DAYS = 3

# Betűméretek
FONT_TEMP = 77
FONT_LABEL = 17
FONT_VALUE = 19
FONT_FOOTER = 14
FONT_FORECAST = 14

# Megjelenítendő adatok (sorrendben!)
VISIBLE_FIELDS = ["feels","clouds","weather","rain_chance","humidity","wind","gust"]

# Üveglap stílus: "auto", "dark", "light", "custom"
GLASS_STYLE = "auto"
# Egyéni szín (HSL) - csak ha GLASS_STYLE = "custom"
# Példa: CUSTOM_GLASS_HSL = (220, 70, 25, 55)  -> sötétkék, 55% átlátszóság
CUSTOM_GLASS_HSL = (220, 70, 25, 55)
# ============================================================

# Font keresési sorrend - Noto elsőként, DejaVu fallback
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

def find_font(bold=False):
    paths = FONT_PATHS_BOLD if bold else FONT_PATHS_REGULAR
    for p in paths:
        if os.path.exists(p):
            return p
    return None

def get_f(size, bold=False):
    path = find_font(bold)
    if path:
        return ImageFont.truetype(path, size)
    return ImageFont.load_default()

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
    elif GLASS_STYLE == "dark":
        return (0, 0, 0, 140)
    elif GLASS_STYLE == "light":
        return (255, 255, 255, 140)
    else:  # auto
        return (255, 255, 255, 140) if brightness > 145 else (0, 0, 0, 110)

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
    # Border maszkkal levagva hogy ne lucsogjunk ki a sarkokon
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

    active_fields  = [f for f in VISIBLE_FIELDS if f != "temp"]
    row_h          = 55
    forecast_height = (20 + FONT_FORECAST + 10 + FORECAST_DAYS * 48) if FORECAST_DAYS > 0 else 0
    bh = 40 + (FONT_TEMP + 28) + (len(active_fields) * row_h) + forecast_height + 50
    bw = WIDGET_WIDTH
    bx = min(WIDGET_X, W - bw - 5)
    by = min(WIDGET_Y, H - bh - 5)

    region         = img.crop((bx, by, bx + bw, by + bh)).convert("L")
    avg_brightness = ImageStat.Stat(region).mean[0]
    glass_c        = get_glass_color(avg_brightness)
    colors         = get_text_colors(avg_brightness)

    # Biztosan a kepen belul marad a blur crop
    bx = max(0, min(bx, W - bw))
    by = max(0, min(by, H - bh))
    card = create_blurred_card(img, bx, by, bw, bh, glass_c, CORNER_RADIUS)
    img  = img.convert("RGBA")
    img.paste(card, (bx, by), card)
    draw = ImageDraw.Draw(img)

    f_t  = get_f(FONT_TEMP, True)
    f_l  = get_f(FONT_LABEL)
    f_v  = get_f(FONT_VALUE, True)
    f_f  = get_f(FONT_FOOTER)
    f_fc = get_f(FONT_FORECAST)

    # Melyik fontot hasznaljuk
    font_path = find_font(False) or "default"
    print(f"Font: {font_path}")

    m  = INNER_MARGIN
    cy = by + 35

    # Homerseklet
    txt = f"{temp}\u00b0C"
    tw  = draw.textbbox((0, 0), txt, font=f_t)[2]
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

    for field in active_fields:
        draw.text((bx + m, cy), field_labels.get(field, field), font=f_l, fill=colors["dim"])
        val = field_values.get(field, "")
        vw  = draw.textbbox((0, 0), val, font=f_v)[2]
        draw.text((bx + bw - m - vw, cy), val, font=f_v, fill=colors["main"])
        line_y = cy + row_h - 8
        draw.line([(bx + m, line_y), (bx + bw - m, line_y)], fill=colors["line"], width=1)
        cy += row_h

    # Eloreljelzes
    if FORECAST_DAYS > 0:
        cy += 10
        draw.line([(bx + m, cy), (bx + bw - m, cy)], fill=colors["line"], width=1)
        cy += 15
        elore = "ELŐREJELZÉS"
        etw   = draw.textbbox((0, 0), elore, font=f_fc)[2]
        draw.text((bx + (bw - etw) // 2, cy), elore, font=f_fc, fill=colors["dim"])
        cy += FONT_FORECAST + 10
        fc_labels = ["HOLNAP", "HOLNAPUTÁN", "+3 NAP", "+4 NAP", "+5 NAP"]
        for d in range(1, FORECAST_DAYS + 1):
            day_name = fc_labels[d-1] if d <= len(fc_labels) else f"+{d} NAP"
            temp_fc  = temp - d * 2
            draw.text((bx + m, cy), day_name, font=f_fc, fill=colors["dim"])
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

    image_url    = f"{BASE_URL}/current.jpg"
    weather_json = [{"location": CITY, "title": f"{weather_hu} {temp}C",
                     "author": "OpenWeatherMap", "url_img": image_url}]
    with open("weather.json", "w", encoding="utf-8") as f:
        json.dump(weather_json, f, ensure_ascii=False, indent=2)
    print("weather.json kesz")

if __name__ == "__main__":
    main()
