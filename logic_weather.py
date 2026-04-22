import requests
import os
from datetime import datetime, timezone, timedelta
from io import BytesIO
from PIL import Image

# ============================================================
# CONFIG
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
# TIME HELPERS
# ============================================================
def get_now_dt(tz_offset):
    return datetime.now(timezone(timedelta(seconds=tz_offset)))


# ============================================================
# WEATHER
# ============================================================
def get_weather_data():
    w = requests.get(
        f"https://api.openweathermap.org/data/2.5/weather"
        f"?q={CITY}&appid={API_KEY}&units=metric"
    ).json()

    f = requests.get(
        f"https://api.openweathermap.org/data/2.5/forecast"
        f"?q={CITY}&appid={API_KEY}&units=metric"
    ).json()

    tz_offset = w.get("timezone", 3600)
    now_dt = get_now_dt(tz_offset)

    weather_id = w["weather"][0]["id"]

    # night check
    is_night = (
        now_dt.timestamp() < w["sys"]["sunrise"]
        or now_dt.timestamp() > w["sys"]["sunset"]
    )

    # POP
    pop = 0
    if "list" in f and f["list"]:
        pop = round(f["list"][0].get("pop", 0) * 100)

    # forecast (3 nap)
    forecast = []
    seen = set()
    today = now_dt.date()

    for item in f["list"]:
        dt = datetime.fromtimestamp(
            item["dt"],
            tz=timezone(timedelta(seconds=tz_offset))
        )

        if dt.date() > today and dt.date() not in seen and dt.hour >= 12:
            forecast.append(item)
            seen.add(dt.date())

        if len(forecast) == 3:
            break

    sunrise = datetime.fromtimestamp(
        w["sys"]["sunrise"],
        tz=timezone(timedelta(seconds=tz_offset))
    ).strftime("%H:%M")

    sunset = datetime.fromtimestamp(
        w["sys"]["sunset"],
        tz=timezone(timedelta(seconds=tz_offset))
    ).strftime("%H:%M")

    return {
        "temp": round(w["main"]["temp"]),
        "feels_like": round(w["main"]["feels_like"]),
        "humidity": w["main"]["humidity"],
        "wind_kmh": round(w["wind"]["speed"] * 3.6),
        "pop": pop,
        "weather_id": weather_id,
        "weather_hu": get_weather_hu(weather_id),
        "is_night": is_night,
        "now_dt": now_dt,
        "sunrise": sunrise,
        "sunset": sunset,
        "forecast": forecast,
        "tz_offset": tz_offset
    }


# ============================================================
# WEATHER TEXT
# ============================================================
def get_weather_hu(weather_id):
    return {
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
    }.get(weather_id, "Változékony")


# ============================================================
# ICON NAME (FIX IMPORT HIBA MEGOLDÁS)
# ============================================================
def get_icon_name(weather_id, is_night):
    suffix = "night" if is_night else "day"

    if 200 <= weather_id <= 232:
        return f"{suffix}_rain_thunder"
    if 300 <= weather_id <= 321:
        return "rain"
    if weather_id in [500, 501]:
        return f"{suffix}_rain"
    if weather_id in [502, 503, 504]:
        return "rain"
    if weather_id == 511:
        return f"{suffix}_sleet"
    if 520 <= weather_id <= 531:
        return f"{suffix}_rain"
    if weather_id in [600, 601, 602]:
        return f"{suffix}_snow"
    if weather_id in [611, 612, 613, 615, 616]:
        return f"{suffix}_sleet"
    if 620 <= weather_id <= 622:
        return f"{suffix}_snow"
    if weather_id in [701, 741]:
        return "mist"
    if weather_id in [711, 761]:
        return "fog"
    if weather_id == 771:
        return "wind"
    if weather_id == 781:
        return "tornado"
    if weather_id == 800:
        return "night_clear" if is_night else "day_clear"
    if weather_id in [801, 802]:
        return f"{suffix}_partial_cloud"
    if weather_id == 803:
        return "cloudy"
    if weather_id == 804:
        return "overcast"

    return "cloudy"


# ============================================================
# NÉVNAP (FIX IDŐVEL)
# ============================================================
def get_todays_namedays(now_dt):
    try:
        r = requests.get(NAMEDAYS_URL)
        r.raise_for_status()
        ics = r.text

        today = now_dt.strftime("%m%d")

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
                        v = l.split(":")[-1].strip()
                        if len(v) >= 8:
                            event["date"] = v[4:8]

                    elif l.startswith("SUMMARY"):
                        event["summary"] = l.split(":", 1)[-1].strip()

                    i += 1

                if event.get("date") == today and event.get("summary"):
                    clean = event["summary"].replace("\\,", ",").replace("\\", "")
                    names.extend([n.strip() for n in clean.split(",") if n.strip()])
            else:
                i += 1

        return names if names else ["–"]

    except Exception as e:
        print("NÉVNAP ERROR:", e)
        return ["–"]


# ============================================================
# DAY NAME
# ============================================================
def get_day_hu(date_obj):
    days = ["Hétfő", "Kedd", "Szerda", "Csütörtök", "Péntek", "Szombat", "Vasárnap"]
    return days[date_obj.weekday()]


# ============================================================
# ICON DOWNLOAD
# ============================================================
def download_icon(name):
    try:
        url = f"{ICONS_URL}/{name}.png"
        r = requests.get(url)
        if r.status_code == 200:
            return Image.open(BytesIO(r.content)).convert("RGBA")
    except:
        pass
    return None
