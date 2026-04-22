import requests
import json
import os
import time
from datetime import datetime, timezone, timedelta
from PIL import Image
from io import BytesIO

# ============================================================
# KONFIGURÁCIÓ
# ============================================================
API_KEY = os.environ.get("OWM_API_KEY")
CITY = "Budapest"
GITHUB_USER = "harsanyiz"
GITHUB_REPO = "weather-wallpaper"
BRANCH = "main"
BASE_URL = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/{BRANCH}"
ICONS_URL = f"{BASE_URL}/images/ICONS_PNG80"
NAMEDAYS_URL = f"{BASE_URL}/Data/Magyarnevnapok.ics"
IMAGE_BASE_URL = f"{BASE_URL}/images"
# ============================================================

def get_weather_data():
    """Aktuális időjárás és 3 napos előrejelzés lekérése OWM API-ból."""
    # Aktuális adatok
    resp = requests.get(
        f"https://api.openweathermap.org/data/2.5/weather"
        f"?q={CITY}&appid={API_KEY}&units=metric"
    )
    data = resp.json()

    # Előrejelzés (3 órás bontás) - Innen nyerjük ki a POP-ot és a köv. napokat
    f_resp = requests.get(
        f"https://api.openweathermap.org/data/2.5/forecast"
        f"?q={CITY}&appid={API_KEY}&units=metric"
    )
    f_data = f_resp.json()

    tz_offset = data.get("timezone", 3600)
    now_dt = datetime.now(timezone(timedelta(seconds=tz_offset)))
    
    # Napnyugta/napkelte ellenőrzés az ikonstílushoz
    is_night = (
        now_dt.timestamp() < data["sys"]["sunrise"]
        or now_dt.timestamp() > data["sys"]["sunset"]
    )

    weather_id = data["weather"][0]["id"]

    # --- ESŐ VALÓSZÍNŰSÉG (POP) ---
    # Az aktuális API nem ad 'pop'-ot, így a forecast legelső (aktuálishoz legközelebbi) elemét nézzük
    current_pop = 0
    if "list" in f_data and len(f_data["list"]) > 0:
        # A pop értéke 0 és 1 közötti, 100-zal szorozva kapunk százalékot
        current_pop = round(f_data["list"][0].get("pop", 0) * 100)

    # Előrejelzés szűrése (következő 3 nap dél körüli adatai)
    forecast_list = []
    seen_days = set()
    today = now_dt.date()
    for entry in f_data["list"]:
        dt_obj = datetime.fromtimestamp(
            entry["dt"], tz=timezone(timedelta(seconds=tz_offset))
        )
        if dt_obj.date() > today and dt_obj.date() not in seen_days and dt_obj.hour >= 12:
            forecast_list.append(entry)
            seen_days.add(dt_obj.date())
        if len(forecast_list) == 3:
            break

    sunrise_dt = datetime.fromtimestamp(data["sys"]["sunrise"], tz=timezone(timedelta(seconds=tz_offset)))
    sunset_dt  = datetime.fromtimestamp(data["sys"]["sunset"],  tz=timezone(timedelta(seconds=tz_offset)))

    return {
        "temp": round(data["main"]["temp"]),
        "feels_like": round(data["main"]["feels_like"]),
        "humidity": data["main"]["humidity"],
        "pop": current_pop,
        "wind_kmh": round(data["wind"]["speed"] * 3.6),
        "weather_id": weather_id,
        "weather_hu": get_weather_hu(weather_id),
        "is_night": is_night,
        "now_dt": now_dt,
        "update_time": now_dt.strftime("%H:%M"),
        "sunrise": sunrise_dt.strftime("%H:%M"),
        "sunset":  sunset_dt.strftime("%H:%M"),
        "forecast": forecast_list,
        "tz_offset": tz_offset,
    }

def get_weather_hu(weather_id):
    """OWM Időjárás kód → Magyar leírás mapping."""
    mapping = {
        800: "Derült",
        801: "Pár felhő",
        802: "Részben felhős",
        803: "Felhős",
        804: "Borult",
        500: "Szemerkélő eső",
        501: "Eső",
        502: "Intenzív eső",
        511: "Ónos eső",
        200: "Vihar",
        600: "Hószállingózás",
        601: "Havazás",
        701: "Párás idő",
        741: "Köd",
    }
    return mapping.get(weather_id, "Változékony")

def get_icon_name(weather_id, is_night):
    """Weather_id alapján meghatározza a PNG ikon nevét."""
    suffix = "night" if is_night else "day"
    if 200 <= weather_id <= 232: return f"{suffix}_rain_thunder"
    if 300 <= weather_id <= 321: return "rain"
    if weather_id in [500, 501]: return f"{suffix}_rain"
    if weather_id in [502, 503, 504]: return "rain"
    if weather_id == 511: return f"{suffix}_sleet"
    if 520 <= weather_id <= 531: return f"{suffix}_rain"
    if weather_id in [600, 601, 602]: return f"{suffix}_snow"
    if weather_id in [611, 612, 613, 615, 616]: return f"{suffix}_sleet"
    if weather_id in [620, 621, 622]: return f"{suffix}_snow"
    if weather_id in [701, 741]: return "mist"
    if weather_id == 711: return "fog"
    if weather_id == 761: return "fog"
    if weather_id == 771: return "wind"
    if weather_id == 781: return "tornado"
    if weather_id == 800: return "night_clear" if is_night else "day_clear"
    if weather_id == 801: return f"{suffix}_partial_cloud"
    if weather_id == 802: return f"{suffix}_partial_cloud"
    if weather_id == 803: return "cloudy"
    if weather_id == 804: return "overcast"
    return "cloudy"

def get_background_image_name(weather_id, is_night):
    """Háttérkép választó logika."""
    suffix = "night" if is_night else "day"
    if weather_id in [611, 612, 613, 615, 616]: return f"sleet_{suffix}"
    elif weather_id in [620, 621, 622, 600, 601, 602]: return f"snow_{suffix}"
    elif weather_id == 800: return f"sunny_{suffix}"
    else: return f"cloudy_{suffix}"

def download_icon(icon_name):
    """Letölti az ikont a GitHub-ról és PIL Image-ként adja vissza."""
    url = f"{ICONS_URL}/{icon_name}.png"
    try:
        resp = requests.get(url)
        if resp.status_code == 200:
            return Image.open(BytesIO(resp.content)).convert("RGBA")
    except:
        pass
    return None

def get_todays_namedays():
    """ICS letöltése és a mai névnapok kinyerése."""
    try:
        resp = requests.get(NAMEDAYS_URL)
        resp.raise_for_status()
        ics_text = resp.text

        today_str = datetime.now().strftime("%m%d")
        names = []
        lines = ics_text.splitlines()
        
        i = 0
        while i < len(lines):
            if lines[i].strip() == "BEGIN:VEVENT":
                event = {}
                i += 1
                while i < len(lines) and lines[i].strip() != "END:VEVENT":
                    l = lines[i].strip()
                    if l.startswith("DTSTART"):
                        val = l.split(":")[-1].strip()
                        event["date"] = val[4:] # Csak a hónap/nap (MMDD)
                    elif l.startswith("SUMMARY"):
                        val = l.split(":", 1)[-1].strip()
                        event["summary"] = val
                    i += 1
                
                if event.get("date") == today_str and "summary" in event:
                    raw = event["summary"]
                    clean_raw = raw.replace("\\,", ",").replace(";", ",").replace("\\", "")
                    parts = [n.strip() for n in clean_raw.split(",")]
                    names.extend(parts)
            else:
                i += 1
        return names if names else ["–"]
    except Exception as e:
        print(f"⚠️ Névnap hiba: {e}")
        return ["–"]

def get_day_hu(date_obj):
    """Dátum objektumból magyar napnév."""
    napok = ["Hétfő", "Kedd", "Szerda", "Csütörtök", "Péntek", "Szombat", "Vasárnap"]
    return napok[date_obj.weekday()]

def build_weather_json(weather_hu, temp, v_param):
    """Frissíti a külső weather.json fájlt."""
    image_url = f"{IMAGE_BASE_URL}/current.jpg?v={v_param}"
    weather_json = [{
        "location": CITY,
        "title": f"{weather_hu} {temp}C",
        "author": "Gemini Design",
        "image_url": image_url,
        "url_img": image_url,
    }]
    with open("weather.json", "w", encoding="utf-8") as f:
        json.dump(weather_json, f, ensure_ascii=False, indent=2)
