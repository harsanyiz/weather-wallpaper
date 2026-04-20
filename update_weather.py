import requests
import json
import os
from datetime import datetime, timezone, timedelta
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageStat

API_KEY = os.environ.get("OWM_API_KEY")
CITY = "Budapest"
GITHUB_USER = "harsanyiz"
GITHUB_REPO = "weather-wallpaper"
BRANCH = "main"
BASE_URL = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/{BRANCH}/images"

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

    # Soronkent 65px * 5 sor = 325, + homerseklet 135, + padding + footer
    row_h  = 65
    n_rows = 5
    bw = 360
    bh = 40 + 135 + (row_h * n_rows) + 30 + 60  # top + temp + rows + sep_space + footer
    bx = W - bw - 70
    by = (H - bh) // 2

    region = img.crop((bx, by, bx + bw, by + bh)).convert("L")
    avg_brightness = ImageStat.Stat(region).mean[0]

    if avg_brightness > 145:
        glass_c = (255, 255, 255, 140)
        t_main  = (0, 0, 0, 230)
        t_dim   = (0, 0, 0, 130)
        l_color = (0, 0, 0, 40)
    else:
        glass_c = (0, 0, 0, 110)
        t_main  = (255, 255, 255, 255)
        t_dim   = (255, 255, 255, 140)
        l_color = (255, 255, 255, 30)

    card = create_blurred_card(img, bx, by, bw, bh, glass_c)
    img  = img.convert("RGBA")
    img.paste(card, (bx, by), card)
    draw = ImageDraw.Draw(img)

    def get_f(s, b=False):
        p = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if b else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
        if os.path.exists(p): return ImageFont.truetype(p, s)
        return ImageFont.load_default()

    f_t = get_f(90, True)
    f_l = get_f(22)
    f_v = get_f(24, True)
    f_f = get_f(18)

    m  = 40
    cy = by + 40

    # Nagy homerseklet - kozepen
    txt = f"{temp}\u00b0"
    tw  = draw.textbbox((0, 0), txt, font=f_t)[2]
    draw.text((bx + (bw - tw) // 2, cy), txt, font=f_t, fill=t_main)
    cy += 135

    # Adatsorok - minden sor vegén vonal, SZIMMETRIKUSAN
    rows = [
        ("\u00c9RZET",      f"{feels} \u00b0C"),
        ("ID\u0150J\u00c1R\u00c1S", weather_hu.upper()),
        ("CSAPAD\u00c9K",   f"{rain_chance}%"),
        ("P\u00c1RA",       f"{humidity}%"),
        ("SZ\u00c9L",       f"{wind} km/h"),
    ]

    for i, (lab, val) in enumerate(rows):
        draw.text((bx + m, cy), lab, font=f_l, fill=t_dim)
        vw = draw.textbbox((0, 0), val, font=f_v)[2]
        draw.text((bx + bw - m - vw, cy), val, font=f_v, fill=t_main)
        # Vonal minden sor utan, azonos tavolsagra a szoveg alatt
        line_y = cy + 45
        draw.line([(bx + m, line_y), (bx + bw - m, line_y)], fill=l_color, width=1)
        cy += row_h

    # Footer - a SZEL utani vonaltol 20px-rel lejjebb a varos
    # cy most a SZEL sor vege utan van
    footer_y = cy + 20   # ~20px a SZEL vonal alatt

    now_str = now_dt.strftime("%Y.%m.%d.  %H:%M")
    ftxt = f"{CITY.upper()}  \u2022  {now_str}"
    fw   = draw.textbbox((0, 0), ftxt, font=f_f)[2]
    draw.text((bx + (bw - fw) // 2, footer_y), ftxt, font=f_f, fill=t_dim)

    img.convert("RGB").save(dst, "JPEG", quality=95)
    print(f"current.jpg mentve")

    image_url    = f"{BASE_URL}/current.jpg"
    weather_json = [{"location": "Budapest", "title": f"{weather_hu} {temp}C",
                     "author": "OpenWeatherMap", "url_img": image_url}]
    with open("weather.json", "w", encoding="utf-8") as f:
        json.dump(weather_json, f, ensure_ascii=False, indent=2)
    print("weather.json kesz")

if __name__ == "__main__":
    main()
