import requests
import json
import os
from datetime import datetime, timezone, timedelta
from PIL import Image, ImageDraw, ImageFont

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
    elif weather_id in [200, 201, 202, 210, 211, 212, 221, 230, 231, 232]: return f"hail_{suffix}"
    elif weather_id in range(500, 532): return f"rainy_{suffix}"
    elif weather_id in range(300, 322): return f"rainy_{suffix}"
    elif weather_id in [800]: return f"sunny_{suffix}"
    elif weather_id in [801, 802, 803, 804]: return f"cloudy_{suffix}"
    else: return f"cloudy_{suffix}"

def get_weather_hu(weather_id):
    if weather_id in [611, 612, 613, 615, 616]: return "Onos eso"
    elif weather_id in [620, 621, 622, 600, 601, 602]: return "Havazas"
    elif weather_id == 511: return "Jeg eso"
    elif weather_id in [781, 771, 762, 761, 751, 731, 721, 711, 701]: return "Kod"
    elif weather_id in range(200, 233): return "Zivatar"
    elif weather_id in range(500, 532): return "Eso"
    elif weather_id in range(300, 322): return "Szitalas"
    elif weather_id == 800: return "Derult"
    elif weather_id in [801, 802]: return "Enyhén felhos"
    elif weather_id in [803, 804]: return "Felhos"
    else: return "Valtozekony"

def get_rain_chance(weather_id):
    if weather_id in range(200, 233): return 80
    elif weather_id in range(500, 532): return 70
    elif weather_id in range(300, 322): return 50
    elif weather_id in [611, 612, 613, 615, 616]: return 60
    elif weather_id in [801, 802]: return 20
    elif weather_id in [803, 804]: return 30
    elif weather_id == 800: return 0
    else: return 10

def draw_rounded_rectangle(draw, xy, radius, fill):
    x1, y1, x2, y2 = xy
    draw.rectangle([(x1 + radius, y1), (x2 - radius, y2)], fill=fill)
    draw.rectangle([(x1, y1 + radius), (x2, y2 - radius)], fill=fill)
    draw.pieslice([(x1, y1), (x1 + radius*2, y1 + radius*2)], 180, 270, fill=fill)
    draw.pieslice([(x2 - radius*2, y1), (x2, y1 + radius*2)], 270, 360, fill=fill)
    draw.pieslice([(x1, y2 - radius*2), (x1 + radius*2, y2)], 90, 180, fill=fill)
    draw.pieslice([(x2 - radius*2, y2 - radius*2), (x2, y2)], 0, 90, fill=fill)

def main():
    url = f"https://api.openweathermap.org/data/2.5/weather?q={CITY}&appid={API_KEY}&units=metric"
    resp = requests.get(url)
    data = resp.json()

    temp       = round(data["main"]["temp"])
    feels_like = round(data["main"]["feels_like"])
    humidity   = data["main"]["humidity"]
    wind       = round(data["wind"]["speed"] * 3.6)
    weather_id = data["weather"][0]["id"]
    sunrise    = data["sys"]["sunrise"]
    sunset     = data["sys"]["sunset"]

    now_ts   = datetime.now(timezone.utc).timestamp()
    is_night = now_ts < sunrise or now_ts > sunset

    weather_hu  = get_weather_hu(weather_id)
    rain_chance = get_rain_chance(weather_id)
    image_name  = get_image_name(weather_id, is_night)

    src = f"images/{image_name}.jpg"
    dst = "images/current.jpg"

    img = Image.open(src).convert("RGB")
    W, H = img.size

    # Box méretek - nagyobb hogy minden beleférjen
    box_w  = 540
    box_h  = 430
    box_x  = W - box_w - 60
    box_y  = H // 2 - box_h // 2

    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ov_draw = ImageDraw.Draw(overlay)
    draw_rounded_rectangle(ov_draw, (box_x, box_y, box_x + box_w, box_y + box_h), 25, (0, 0, 0, 175))
    img = img.convert("RGBA")
    img = Image.alpha_composite(img, overlay)
    img = img.convert("RGB")
    draw = ImageDraw.Draw(img)

    try:
        bold = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        reg  = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
        font_temp    = ImageFont.truetype(bold, 100)
        font_feels   = ImageFont.truetype(reg,  36)
        font_weather = ImageFont.truetype(bold,  44)
        font_detail  = ImageFont.truetype(reg,  32)
        font_small   = ImageFont.truetype(reg,  28)
    except:
        font_temp = font_feels = font_weather = font_detail = font_small = ImageFont.load_default()

    ml = 35
    x  = box_x + ml
    y  = box_y + 28

    # Homerseklet
    draw.text((x, y), f"{temp}C", font=font_temp, fill=(255, 255, 255))
    y += 108

    # Erzet
    draw.text((x, y), f"Erzet: {feels_like}C", font=font_feels, fill=(210, 210, 210))
    y += 50

    # Elvalaszto
    draw.line([(x, y), (box_x + box_w - ml, y)], fill=(200, 200, 200), width=1)
    y += 16

    # Idojaras
    draw.text((x, y), weather_hu, font=font_weather, fill=(255, 255, 255))
    y += 58

    # Csapadek
    if rain_chance > 0:
        draw.text((x, y), f"Csapadek esely: {rain_chance}%", font=font_detail, fill=(180, 210, 255))
    else:
        draw.text((x, y), "Csapadek nem varhato", font=font_detail, fill=(180, 255, 180))
    y += 50

    # Par + Szel
    draw.text((x, y),        f"Par: {humidity}%", font=font_small, fill=(180, 180, 180))
    draw.text((x + 190, y),  f"Szel: {wind} km/h", font=font_small, fill=(180, 180, 180))
    y += 46

    # Elvalaszto
    draw.line([(x, y), (box_x + box_w - ml, y)], fill=(120, 120, 120), width=1)
    y += 14

    # Budapest + datum - BENN a dobozban
    now_hu    = datetime.now(timezone(timedelta(hours=2))).strftime("%Y.%m.%d.  %H:%M")
    date_text = f"Budapest  |  {now_hu}"
    bbox      = draw.textbbox((0, 0), date_text, font=font_small)
    date_w    = bbox[2] - bbox[0]
    date_x    = box_x + (box_w - date_w) // 2
    draw.text((date_x, y), date_text, font=font_small, fill=(150, 150, 150))

    img.save(dst, "JPEG", quality=95)
    print("current.jpg kesz")

    image_url    = f"{BASE_URL}/current.jpg"
    weather_json = [{"location": "Budapest", "title": f"{weather_hu} {temp}C",
                     "author": "OpenWeatherMap", "url_img": image_url}]
    with open("weather.json", "w", encoding="utf-8") as f:
        json.dump(weather_json, f, ensure_ascii=False, indent=2)
    print("weather.json kesz")

if __name__ == "__main__":
    main()
