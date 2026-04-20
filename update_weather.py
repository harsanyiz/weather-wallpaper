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
WIDGET_WIDTH = 380
WIDGET_X = 1500      # vízszintes pozíció (0-1920)
WIDGET_Y = 340       # függőleges pozíció (0-1080)
CORNER_RADIUS = 30
INNER_MARGIN = 40
COLUMNS = 2          # 1 vagy 2 oszlop
FORECAST_DAYS = 1    # 0, 1, 2, 3 nap előrejelzés

# Betűméretek
FONT_TEMP = 90
FONT_LABEL = 20
FONT_VALUE = 22
FONT_FOOTER = 16
FONT_FORECAST = 14

# Megjelenítendő adatok (sorrendben!)
VISIBLE_FIELDS = ["temp", "feels", "weather", "rain_chance", "humidity", "wind"]

# Üveglap stílus: "auto", "dark", "light", "custom"
GLASS_STYLE = "auto"
# Egyéni szín (HSL) - csak ha GLASS_STYLE = "custom"
CUSTOM_GLASS_HSL = None  # (hue, saturation, lightness, opacity) pl: (220, 70, 25, 55)
# ============================================================

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
    mapping = {800: "Derült", 801: "Enyhén felhős", 802: "Enyhén felhős",
               803: "Felhős", 804: "Felhős", 511: "Jégeső"}
    if weather_id in mapping: return mapping[weather_id]
    if weather_id in range(600, 623): return "Havazás"
    if weather_id in range(200, 233): return "Zivatar"
    if weather_id in range(500, 532): return "Eső"
    if weather_id in range(300, 322): return "Szitálás"
    return "Változékony"

def get_rain_chance(weather_id):
    if weather_id in range(200, 233): return 80
    if weather_id in range(500, 532): return 70
    if weather_id == 800: return 0
    return 20

def create_blurred_card(image, box_x, box_y, box_width, box_height, glass_color, radius=30, blur_strength=18):
    box_area = image.crop((box_x, box_y, box_x + box_width, box_y + box_height))
    blurred = box_area.filter(ImageFilter.GaussianBlur(blur_strength))
    mask = Image.new("L", (box_width, box_height), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle((0, 0, box_width, box_height), radius=radius, fill=255)
    glass = Image.new("RGBA", (box_width, box_height), glass_color)
    blurred = blurred.convert("RGBA")
    blurred.putalpha(mask)
    result = Image.alpha_composite(blurred, glass)
    border_color = (255, 255, 255, 50) if glass_color[0] < 128 else (0, 0, 0, 30)
    border = Image.new("RGBA", (box_width, box_height), (0, 0, 0, 0))
    ImageDraw.Draw(border).rounded_rectangle((0, 0, box_width, box_height), radius=radius, outline=border_color, width=1)
    return Image.alpha_composite(result, border)

def hsl_to_rgba(h, s, l, a):
    """HSL színkonvertálás RGBA-vé (s és a százalékban)"""
    s = s / 100
    l = l / 100
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
    return (round((r1 + m) * 255), round((g1 + m) * 255), round((b1 + m) * 255), round(a * 2.55))

def get_glass_color(brightness):
    """Visszaadja az üveg színét a konfiguráció alapján"""
    if GLASS_STYLE == "custom" and CUSTOM_GLASS_HSL:
        h, s, l, a = CUSTOM_GLASS_HSL
        return hsl_to_rgba(h, s, l, a)
    elif GLASS_STYLE == "dark":
        return (0, 0, 0, 140)
    elif GLASS_STYLE == "light":
        return (255, 255, 255, 140)
    else:  # auto
        if brightness > 145:
            return (255, 255, 255, 140)
        else:
            return (0, 0, 0, 110)

def get_text_colors(brightness):
    """Visszaadja a szöveg színeit a háttér fényereje alapján"""
    if GLASS_STYLE == "light":
        return {"main": (0, 0, 0, 230), "dim": (0, 0, 0, 130), "line": (0, 0, 0, 40)}
    elif GLASS_STYLE == "custom" and CUSTOM_GLASS_HSL and CUSTOM_GLASS_HSL[2] > 40:
        return {"main": (0, 0, 0, 230), "dim": (0, 0, 0, 130), "line": (0, 0, 0, 40)}
    else:  # auto vagy dark
        if brightness > 145:
            return {"main": (0, 0, 0, 230), "dim": (0, 0, 0, 130), "line": (0, 0, 0, 40)}
        else:
            return {"main": (255, 255, 255, 255), "dim": (255, 255, 255, 140), "line": (255, 255, 255, 30)}

def main():
    try:
        resp = requests.get(f"https://api.openweathermap.org/data/2.5/weather?q={CITY}&appid={API_KEY}&units=metric")
        data = resp.json()
        temp      = round(data["main"]["temp"])
        feels     = round(data["main"]["feels_like"])
        humidity  = data["main"]["humidity"]
        wind      = round(data["wind"]["speed"] * 3.6)
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

    # Dinamikus magasság számítás
    active_fields = [f for f in VISIBLE_FIELDS if f != "temp"]
    row_h = 55
    n_rows = len(active_fields)
    rows_in_display = (n_rows + COLUMNS - 1) // COLUMNS if COLUMNS > 1 else n_rows
    
    forecast_height = 70 + (FORECAST_DAYS * 50) if FORECAST_DAYS > 0 else 0
    bh = 40 + (FONT_TEMP + 28 if "temp" in VISIBLE_FIELDS else 0) + (rows_in_display * row_h) + forecast_height + 50
    bw = WIDGET_WIDTH
    bx = WIDGET_X
    by = WIDGET_Y

    region = img.crop((bx, by, bx + bw, by + bh)).convert("L")
    avg_brightness = ImageStat.Stat(region).mean[0]

    glass_c = get_glass_color(avg_brightness)
    colors = get_text_colors(avg_brightness)

    card = create_blurred_card(img, bx, by, bw, bh, glass_c, CORNER_RADIUS)
    img = img.convert("RGBA")
    img.paste(card, (bx, by), card)
    draw = ImageDraw.Draw(img)

    def get_f(s, b=False):
        p = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if b else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
        if os.path.exists(p): return ImageFont.truetype(p, s)
        return ImageFont.load_default()

    f_t = get_f(FONT_TEMP, True)
    f_l = get_f(FONT_LABEL)
    f_v = get_f(FONT_VALUE, True)
    f_f = get_f(FONT_FOOTER)
    f_fc = get_f(FONT_FORECAST)

    m = INNER_MARGIN
    cy = by + 35

    # Hőmérséklet
    if "temp" in VISIBLE_FIELDS:
        txt = f"{temp}°C"
        tw = draw.textbbox((0, 0), txt, font=f_t)[2]
        draw.text((bx + (bw - tw) // 2, cy), txt, font=f_t, fill=colors["main"])
        cy += FONT_TEMP + 28

    # Adatmezők
    field_labels = {
        "feels": "ÉRZET", "weather": "IDŐJÁRÁS", "rain_chance": "CSAPADÉK",
        "humidity": "PÁRA", "wind": "SZÉL", "pressure": "LÉGNYOMÁS",
        "uv": "UV", "visibility": "LÁTÓTÁV", "gust": "SZÉLLÖKÉS", "clouds": "FELHŐZET"
    }
    field_values = {
        "feels": f"{feels} °C", "weather": weather_hu.upper(), "rain_chance": f"{rain_chance}%",
        "humidity": f"{humidity}%", "wind": f"{wind} km/h", "pressure": f"{data['main']['pressure']} hPa",
        "uv": "3", "visibility": f"{data.get('visibility', 10000)//1000} km",
        "gust": f"{round(data['wind'].get('gust', data['wind']['speed']) * 3.6)} km/h",
        "clouds": f"{data.get('clouds', {}).get('all', 45)}%"
    }

    col_width = (bw - m * 2) // COLUMNS if COLUMNS == 2 else bw - m * 2

    if COLUMNS == 1:
        for field in active_fields:
            draw.text((bx + m, cy), field_labels.get(field, field), font=f_l, fill=colors["dim"])
            val = field_values.get(field, "")
            vw = draw.textbbox((0, 0), val, font=f_v)[2]
            draw.text((bx + bw - m - vw, cy), val, font=f_v, fill=colors["main"])
            cy += row_h
    else:
        half = (len(active_fields) + 1) // 2
        left = active_fields[:half]
        right = active_fields[half:]
        for i in range(max(len(left), len(right))):
            if i < len(left):
                draw.text((bx + m, cy), field_labels.get(left[i], left[i]), font=f_l, fill=colors["dim"])
                val = field_values.get(left[i], "")
                vw = draw.textbbox((0, 0), val, font=f_v)[2]
                draw.text((bx + m + col_width - 10, cy), val, font=f_v, fill=colors["main"])
            if i < len(right):
                x2 = bx + m + col_width + 20
                draw.text((x2, cy), field_labels.get(right[i], right[i]), font=f_l, fill=colors["dim"])
                val = field_values.get(right[i], "")
                vw = draw.textbbox((0, 0), val, font=f_v)[2]
                draw.text((x2 + col_width - 10, cy), val, font=f_v, fill=colors["main"])
            cy += row_h

    # Előrejelzés
    if FORECAST_DAYS > 0:
        cy += 10
        draw.line([(bx + m, cy), (bx + bw - m, cy)], fill=colors["line"], width=1)
        cy += 15
        draw.text((bx + bw // 2, cy), "🔮 ELŐREJELZÉS", font=f_fc, fill=colors["dim"], anchor="mm")
        cy += FONT_FORECAST + 10
        icons = ["☀️", "⛅", "☁️", "🌧️", "⛈️"]
        for d in range(1, FORECAST_DAYS + 1):
            day_name = "HOLNAP" if d == 1 else "HOLNAPUTÁN" if d == 2 else f"+{d} NAP"
            temp_forecast = temp - d * 2
            draw.text((bx + m + 10, cy), day_name, font=f_fc, fill=colors["dim"])
            draw.text((bx + bw - m - 10, cy), f"{temp_forecast}°C", font=f_fc, fill=colors["main"], anchor="ra")
            draw.text((bx + bw // 2, cy), icons[(d - 1) % 5], font=f_fc, fill=colors["dim"], anchor="mm")
            cy += 42

    # Footer
    cy += 15
    now_str = now_dt.strftime("%Y.%m.%d.  %H:%M")
    ftxt = f"{CITY.upper()}  •  {now_str}"
    fw = draw.textbbox((0, 0), ftxt, font=f_f)[2]
    draw.text((bx + (bw - fw) // 2, cy), ftxt, font=f_f, fill=colors["dim"])

    img.convert("RGB").save(dst, "JPEG", quality=95)
    print(f"current.jpg mentve")

    image_url = f"{BASE_URL}/current.jpg"
    weather_json = [{"location": CITY, "title": f"{weather_hu} {temp}C",
                     "author": "OpenWeatherMap", "url_img": image_url}]
    with open("weather.json", "w", encoding="utf-8") as f:
        json.dump(weather_json, f, ensure_ascii=False, indent=2)
    print("weather.json kesz")

if __name__ == "__main__":
    main()
