import requests
import json
import os
import time
from datetime import datetime, timezone, timedelta

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
    resp = requests.get(
        f"https://api.openweathermap.org/data/2.5/weather"
        f"?q={CITY}&appid={API_KEY}&units=metric"
    )
    data = resp.json()

    f_resp = requests.get(
        f"https://api.openweathermap.org/data/2.5/forecast"
        f"?q={CITY}&appid={API_KEY}&units=metric"
    )
    f_data = f_resp.json()

    tz_offset = data.get("timezone", 3600)
    now_dt = datetime.now(timezone(timedelta(seconds=tz_offset)))
    is_night = (
        now_dt.timestamp() < data["sys"]["sunrise"]
        or now_dt.timestamp() > data["sys"]["sunset"]
    )

    weather_id = data["weather"][0]["id"]

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
    """Időjárás kód → magyar szöveg."""
    mapping = {
        800: "Derült",
        801: "Pár felhő",
        802: "Részben felhős",
        803: "Felhős",
        804: "Borult",
        511: "Ónos eső",
    }
    return mapping.get(weather_id, "Változékony")


def get_icon_name(weather_id, is_night):
    """
    OWM weather_id → ikon fájlnév (ICONS_PNG80 mappa alapján).
    Visszaadja a fájlnevet kiterjesztés nélkül.
    """
    suffix = "night" if is_night else "day"

    # Zivatar (2xx)
    if 200 <= weather_id <= 232:
        return f"{suffix}_rain_thunder"

    # Szitálás (3xx)
    if 300 <= weather_id <= 321:
        return "rain"

    # Eső (5xx)
    if weather_id in [500, 501]:
        return f"{suffix}_rain"
    if weather_id in [502, 503, 504]:
        return "rain"
    if weather_id == 511:
        return f"{suffix}_sleet"
    if 520 <= weather_id <= 531:
        return f"{suffix}_rain"

    # Hó (6xx)
    if weather_id in [600, 601, 602]:
        return f"{suffix}_snow"
    if weather_id in [611, 612, 613, 615, 616]:
        return f"{suffix}_sleet"
    if weather_id in [620, 621, 622]:
        return f"{suffix}_snow"

    # Légköri jelenségek (7xx)
    if weather_id in [701, 741]:
        return "mist"
    if weather_id == 711:
        return "fog"
    if weather_id == 761:
        return "fog"
    if weather_id == 771:
        return "wind"
    if weather_id == 781:
        return "tornado"

    # Tiszta (800)
    if weather_id == 800:
        return "night_clear" if is_night else "day_clear"

    # Felhős (80x)
    if weather_id == 801:
        return f"{suffix}_partial_cloud"
    if weather_id == 802:
        return f"{suffix}_partial_cloud"
    if weather_id == 803:
        return "cloudy"
    if weather_id == 804:
        return "overcast"

    return "cloudy"


def get_background_image_name(weather_id, is_night):
    """Háttérkép neve (eredeti logika megtartva)."""
    suffix = "night" if is_night else "day"
    if weather_id in [611, 612, 613, 615, 616]:
        return f"sleet_{suffix}"
    elif weather_id in [620, 621, 622, 600, 601, 602]:
        return f"snow_{suffix}"
    elif weather_id == 800:
        return f"sunny_{suffix}"
    else:
        return f"cloudy_{suffix}"


def download_icon(icon_name):
    """Letölti az ikont a GitHubról, visszaad PIL Image objektumot."""
    from PIL import Image
    from io import BytesIO

    url = f"{ICONS_URL}/{icon_name}.png"
    resp = requests.get(url)
    if resp.status_code == 200:
        return Image.open(BytesIO(resp.content)).convert("RGBA")
    else:
        print(f"⚠️  Ikon nem található: {url}")
        return None


def get_todays_namedays():
    """
    Letölti a Magyarnevnapok.ics fájlt GitHubról,
    és visszaadja a mai naphoz tartozó neveket listában.
    """
    try:
        resp = requests.get(NAMEDAYS_URL)
        resp.raise_for_status()
        ics_text = resp.text

        today = datetime.now()
        today_str = today.strftime("%m%d")  # pl. "0422"

        names = []
        lines = ics_text.splitlines()
        i = 0
        while i < len(lines):
            if lines[i].strip() == "BEGIN:VEVENT":
                event = {}
                i += 1
                while i < len(lines) and lines[i].strip() != "END:VEVENT":
                    line = lines[i].strip()
                    if line.startswith("DTSTART"):
                        # DTSTART;VALUE=DATE:20000422  vagy DTSTART:20000422
                        val = line.split(":")[-1].strip()
                        event["date"] = val[4:]  # hónap+nap: "0422"
        elif line.startswith("SUMMARY"):
                        val = line.split(":", 1)[-1].strip()
                        event["summary"] = val
                    i += 1
                if event.get("date") == today_str and "summary" in event:
                    raw = event["summary"]
                    # Kicseréljük a \, sorokat, a pontosvesszőket, és töröljük a maradék \ jelet
                    clean_raw = raw.replace("\\,", ",").replace(";", ",").replace("\\", "")
                    # Most már biztonságosan darabolhatunk a vessző mentén
                    parts = [n.strip() for n in clean_raw.split(",")]
                    names.extend(parts)
            else:
                i += 1

        return names if names else ["–"]

    except Exception as e:
        print(f"⚠️  Névnap hiba: {e}")
        return ["–"]


def get_day_hu(date_obj):
    napok = ["Hétfő", "Kedd", "Szerda", "Csütörtök", "Péntek", "Szombat", "Vasárnap"]
    return napok[date_obj.weekday()]


def build_weather_json(weather_hu, temp, v_param):
    """Frissíti a weather.json fájlt."""
    image_url = f"{IMAGE_BASE_URL}/current.jpg?v={v_param}"
    weather_json = [
        {
            "location": CITY,
            "title": f"{weather_hu} {temp}C",
            "author": "Gemini Design",
            "image_url": image_url,
            "url_img": image_url,
        }
    ]
    with open("weather.json", "w", encoding="utf-8") as f:
        json.dump(weather_json, f, ensure_ascii=False, indent=2)
