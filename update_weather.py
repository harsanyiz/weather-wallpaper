import requests
import json
import os
from datetime import datetime, timezone, timedelta
from PIL import Image, ImageDraw, ImageFont

# --- Konfig ---
API_KEY = os.environ.get("OWM_API_KEY")
CITY = "Budapest"
GITHUB_USER = "harsanyiz"
GITHUB_REPO = "weather-wallpaper"
BRANCH = "main"

BASE_URL = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/{BRANCH}/images"

def get_image_name(weather_id, is_night):
    suffix = "night" if is_night else "day"
    if weather_id in [611, 612, 613, 615, 616]:
        return f"sleet_{suffix}"
    elif weather_id in [620, 621, 622, 600, 601, 602]:
        return f"snow_{suffix}"
    elif weather_id in [511]:
        return f"hail_{suffix}"
    elif weather_id in [781, 771, 762, 761, 751, 731, 721, 711, 701]:
        return f"foggy_{suffix}"
    elif weather_id in [200, 201, 202, 210, 211, 212, 221, 230, 231, 232]:
        return f"hail_{suffix}"
    elif weather_id in range(500, 532):
        return f"rainy_{suffix}"
    elif weather_id in range(300, 322):
        return f"rainy_{suffix}"
    elif weather_id in [800]:
        return f"sunny_{suffix}"
    elif weather_id in [801, 802, 803, 804]:
        return f"cloudy_{suffix}"
    else:
        return f"cloudy_{suffix}"

def get_weather_hu(weather_id):
    if weather_id in [611, 612, 613, 615, 616]:
        return "Onos eso"
    elif weather_id in [620, 621, 622, 600, 601, 602]:
        return "Havazas"
    elif weather_id == 511:
        return "Jeg eso"
    elif weather_id in [781, 771, 762, 761, 751, 731, 721, 711, 701]:
        return "Kod"
    elif weather_id in range(200, 233):
        return "Zivatar"
    elif weather_id in range(500, 532):
        return "Eso"
    elif weather_id in range(300, 322): 
        return "Szitalas"
    elif weather_id == 800:
        return "Derult"
    elif weather_id in [801, 802]:
        return "Enyhén felhos"
    elif weather_id in [803, 804]:
        return "Felhos"
    else:
        return "Valtozekony"

def get_rain_chance(weather_id):
    if weather_id in range(200, 233): return 80
    elif weather_id in range(500, 532): return 70
    elif weather_id in range(300, 322): return 50
    elif weather_id in [611, 612, 613, 615, 616]: return 60
    elif weather_id in [801, 802]: return 20
    elif weather_id in [803, 804]: return 30
    elif weather_id == 800: return 0
    else: return 10

def get_weather_icon_text(weather_id):
    if weather_id in [611, 612, 613, 615, 616]: return "*"
    elif weather_id in [620, 621, 622, 600, 601, 602]: return "*"
    elif weather_id == 511: return "#"
    elif weather_id in [781, 771, 762, 761, 751, 731, 721, 711, 701]: return "~"
    elif weather_id in range(200, 233): return "!!"
    elif weather_id in range(500, 532): return "|"
    elif weather_id in range(300, 322): return "."
    elif weather_id == 800: return "o"
    elif weather_id in [801, 802]: return "o~"
    elif weather_id in [803, 804]: return "~~"
    else: return "?"

def draw_rounded_rectangle(draw, xy, radius, fill, outline=None, width=1):
    x1, y1, x2, y2 = xy
    draw.rectangle([(x1 + radius, y1), (x2 - radius, y2)], fill=fill)
    draw.rectangle([(x1, y1 + radius), (x2, y2 - radius)], fill=fill)
    draw.pieslice([(x1, y1), (x1 + radius*2, y1 + radius*2)], 180, 270, fill=fill)
    draw.pieslice([(x2 - radius*2, y1), (x2, y1 + radius*2)], 270, 360, fill=fill)
    draw.pieslice([(x1, y2 - radius*2), (x1 + radius*2, y2)], 90, 180, fill=fill)
    draw.pieslice([(x2 - radius*2, y2 - radius*2), (x2, y2)], 0, 90, fill=fill)
    if outline:
        draw.rectangle([(x1 + radius, y1), (x2 - radius, y1 + width)], fill=outline)
        draw.rectangle([(x1 + radius, y2 - width), (x2 - radius, y2)], fill=outline)
        draw.rectangle([(x1, y1 + radius), (x1 + width, y2 - radius)], fill=outline)
        draw.rectangle([(x2 - width, y1 + radius), (x2, y2 - radius)], fill=outline)

def main():
    url = f"https://api.openweathermap.org/data/2.5/weather?q={CITY}&appid={API_KEY}&units=metric"
    resp = requests.get(url)
    data = resp.json()

    temp        = round(data["main"]["temp"])
    feels_like  = round(data["main"]["feels_like"])
    humidity    = data["main"]["humidity"]
    wind        = round(data["wind"]["speed"] * 3.6)
    weather_id  = data["weather"][0]["id"]
    sunrise     = data["sys"]["sunrise"]
    sunset      = data["sys"]["sunset"]

    now_ts   = datetime.now(timezone.utc).timestamp()
    is_night = now_ts < sunrise or now_ts > sunset

    weather_hu   = get_weather_hu(weather_id)
    rain_chance  = get_rain_chance(weather_id)
    image_name   = get_image_name(weather_id, is_night)

    print(f"{weather_hu} | {temp}C | Csapadek: {rain_chance}%")

    src = f"images/{image_name}.jpg"
    dst = "images/current.jpg"

    img = Image.open(src).convert("RGB")
    W, H = img.size

    box_width  = 520
    box_height = 360
    box_x = W - box_width - 60
    box_y = H // 2 - box_height // 2
    radius = 25

    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ov_draw = ImageDraw.Draw(overlay)
    draw_rounded_rectangle(ov_draw,
        (box_x, box_y, box_x + box_width, box_y + box_height),
        radius, (0, 0, 0, 170), outline=(255, 255, 255, 60), width=2)

    img = img.convert("RGBA")
    img = Image.alpha_composite(img, overlay)
    img = img.convert("RGB")
    draw = ImageDraw.Draw(img)

    try:
        font_temp    = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 100)
        font_feels   = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 36)
        font_weather = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 44)
        font_detail  = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 32)
        font_small   = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 28)
    except:
        font_temp = font_feels = font_weather = font_detail = font_small = ImageFont.load_default()

    ml = 35
    x  = box_x + ml
    y  = box_y + 30

    # Homerseklet
    draw.text((x, y), f"{temp}C", font=font_temp, fill=(255, 255, 255))

    # Erzet
    y += 110
    draw.text((x, y), f"Erzet: {feels_like}C", font=font_feels, fill=(210, 210, 210))

    # Elvalaszto vonal
    y += 52
    draw.line([(x, y), (box_x + box_width - ml, y)], fill=(255, 255, 255, 80), width=1)
    y += 14

    # Idojaras
    draw.text((x, y), weather_hu, font=font_weather, fill=(255, 255, 255))

    # Csapadek
    y += 58
    if rain_chance > 0:
        draw.text((x, y), f"Csapadek esely: {rain_chance}%", font=font_detail, fill=(180, 210, 255))
    else:
        draw.text((x, y), "Csapadek nem varhato", font=font_detail, fill=(180, 255, 180))

    # Paratartalom + szel
    y += 48
    draw.text((x, y),           f"Par: {humidity}%", font=font_small, fill=(180, 180, 180))
    draw.text((x + 180, y),     f"Szel: {wind} km/h", font=font_small, fill=(180, 180, 180))

    # Datum - box alatt kozepen
    now_hu    = datetime.now(timezone(timedelta(hours=2))).strftime("%Y.%m.%d.  %H:%M")
    date_text = f"Budapest  *  {now_hu}"
    bbox      = draw.textbbox((0, 0), date_text, font=font_small)
    date_w    = bbox[2] - bbox[0]
    date_x    = box_x + (box_width - date_w) // 2
    draw.text((date_x, box_y + box_height + 18), date_text, font=font_small, fill=(150, 150, 150))

    img.save(dst, "JPEG", quality=95)
    print("current.jpg kesz")

    image_url   = f"{BASE_URL}/current.jpg"
    weather_json = [{
        "location": "Budapest",
        "title":    f"{weather_hu} * {temp}C",
        "author":   "OpenWeatherMap",
        "url_img":  image_url
    }]

    with open("weather.json", "w", encoding="utf-8") as f:
        json.dump(weather_json, f, ensure_ascii=False, indent=2)

    print("weather.json kesz")

if __name__ == "__main__":
    main()
