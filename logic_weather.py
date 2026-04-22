import requests
import json
import os
from datetime import datetime, timezone, timedelta
from io import BytesIO
from PIL import Image

# ============================================================
# KONFIG
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
# IDŐ KEZELÉS (EGY FORRÁS)
# ============================================================
def get_now_dt(tz_offset):
    return datetime.now(timezone(timedelta(seconds=tz_offset)))


# ============================================================
# IDŐJÁRÁS
# ============================================================
def get_weather_data():
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
    now_dt = get_now_dt(tz_offset)

    is_night = (
        now_dt.timestamp() < data["sys"]["sunrise"]
        or now_dt.timestamp() > data["sys"]["sunset"]
    )

    weather_id = data["weather"][0]["id"]

    # POP
    current_pop = 0
    if "list" in f_data and f_data["list"]:
        current_pop = round(f_data["list"][0].get("pop", 0) * 100)

    # forecast (3 nap)
    forecast_list = []
    seen_days = set()
    today = now_dt.date()

    for entry in f_data["list"]:
        dt_obj = datetime.fromtimestamp(
            entry["dt"],
            tz=timezone(timedelta(seconds=tz_offset))
        )

        if dt_obj.date() > today and dt_obj.date() not in seen_days and dt_obj.hour >= 12:
            forecast_list.append(entry)
            seen_days.add(dt_obj.date())

        if len(forecast_list) == 3:
            break

    sunrise = datetime.fromtimestamp(
        data["sys"]["sunrise"],
        tz=timezone(timedelta(seconds=tz_offset))
    ).strftime("%H:%M")

    sunset = datetime.fromtimestamp(
        data["sys"]["sunset"],
        tz=timezone(timedelta(seconds=tz_offset))
    ).strftime("%H:%M")

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
        "sunrise": sunrise,
        "sunset": sunset,
        "forecast": forecast_list,
        "tz_offset": tz_offset,
    }


# ============================================================
# IDŐJÁRÁS SZÖVEG
# ============================================================
def get_weather_hu(weather_id):
    mapping = {
        800: "Derült",
        801: "Pár felhő",
        802: "Részben felhős",
        803: "Felhős",
        804: "Borult",
        500: "Eső",
        501: "Eső",
        502: "Heves eső",
        511: "Ónos eső",
        200: "Vihar",
        600: "Havazás",
        601: "Havazás",
        701: "Párás",
        741: "Köd",
    }
    return mapping.get(weather_id, "Változékony")


# ============================================================
# NÉVNAP (FIX IDŐVEL)
# ============================================================
def get_todays_namedays(now_dt):
    try:
        resp = requests.get(NAMEDAYS_URL)
        resp.raise_for_status()
        ics = resp.text

        today_str = now_dt.strftime("%m%d")

        names = []
        lines = ics.splitlines()

        i = 0
        while i < len(lines):
            if lines[i].strip() == "BEGIN:VEVENT":
                event = {}
                i += 1

                while i < len(lines) and lines[i].strip() != "END:VEVENT":
                    l = lines[i].strip()

                    if l.startswith("DTSTART"):
                        val = l.split(":")[-1].strip()
                        if len(val) >= 8:
                            event["date"] = val[4:8]

                    elif l.startswith("SUMMARY"):
                        event["summary"] = l.split(":", 1)[-1].strip()

                    i += 1

                if event.get("date") == today_str and event.get("summary"):
                    clean = event["summary"].replace("\\,", ",").replace("\\", "")
                    names.extend([n.strip() for n in clean.split(",") if n.strip()])

            else:
                i += 1

        return names if names else ["–"]

    except Exception as e:
        print("Névnap hiba:", e)
        return ["–"]


# ============================================================
# NAP NEVE
# ============================================================
def get_day_hu(date_obj):
    napok = ["Hétfő", "Kedd", "Szerda", "Csütörtök", "Péntek", "Szombat", "Vasárnap"]
    return napok[date_obj.weekday()]


# ============================================================
# ICON LETÖLTÉS
# ============================================================
def download_icon(icon_name):
    try:
        url = f"{ICONS_URL}/{icon_name}.png"
        r = requests.get(url)
        if r.status_code == 200:
            return Image.open(BytesIO(r.content)).convert("RGBA")
    except:
        pass
    return None


# ============================================================
# JSON EXPORT
# ============================================================
def build_weather_json(weather_hu, temp, v_param):
    image_url = f"{IMAGE_BASE_URL}/current.jpg?v={v_param}"

    data = [{
        "location": CITY,
        "title": f"{weather_hu} {temp}C",
        "author": "Gemini Design",
        "image_url": image_url
    }]

    with open("weather.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
