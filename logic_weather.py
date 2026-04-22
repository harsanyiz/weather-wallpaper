import requests
from datetime import datetime, timezone
import json
import os

# ---------- NÉVNAPOK ADATBÁZIS (magyar, hónap–nap alapú) ----------
# Itt egy tömörített példa, a teljes listát külön fájlból is betöltheted.
# A lényeg: a névnapokat (UTC) nap alapján adjuk vissza.

NAMEDAYS_DB = {
    (1, 1): "Fruzsina",
    (1, 2): "Ábel",
    (1, 3): "Genovéva, Benjámin",
    (1, 4): "Titusz, Angéla",
    (1, 5): "Simon",
    (1, 6): "Boldizsár",
    (1, 7): "Attila, Ramóna",
    (1, 8): "Szeverin",
    (1, 9): "Marcell",
    (1, 10): "Mellinda, Vilmos",
    # ... itt folytatódik a többi nap
    # (a teljes listát csatolhatom külön, de a logika a lényeg)
    (12, 31): "Szilveszter"
}

def get_namedays_for_utc_date(utc_dt):
    """
    Visszaadja a névnapokat az UTC dátum alapján.
    - utc_dt: datetime objektum (aware vagy naive, de UTC-nek vesszük)
    - Nem számít a rendszer időzónája, nem vált éjfélkor helyi idő szerint.
    """
    # Biztosítjuk, hogy UTC-ként kezeljük
    if utc_dt.tzinfo is None:
        utc_dt = utc_dt.replace(tzinfo=timezone.utc)
    month = utc_dt.month
    day = utc_dt.day
    # Keresés a szótárban
    nameday = NAMEDAYS_DB.get((month, day), "")
    # Ha több név van, vesszővel elválasztva adjuk vissza
    if nameday:
        return [name.strip() for name in nameday.split(",")]
    return []

# ---------- IDŐJÁRÁS API ----------
API_KEY = "YOUR_OPENWEATHER_API_KEY"  # Ide tedd a saját kulcsod
CITY = "Budapest"
URL = f"http://api.openweathermap.org/data/2.5/weather?q={CITY}&units=metric&appid={API_KEY}"
FORECAST_URL = f"http://api.openweathermap.org/data/2.5/forecast?q={CITY}&units=metric&appid={API_KEY}"

def get_weather_data():
    """Lekéri az aktuális időjárást és az előrejelzést, visszaad egy dict-et."""
    try:
        resp = requests.get(URL)
        data = resp.json()
        if resp.status_code != 200:
            raise Exception(data.get("message", "Ismeretlen hiba"))
        
        # Aktuális idő (UTC)
        now_utc = datetime.utcnow().replace(tzinfo=timezone.utc)
        
        # Alap adatok
        temp = round(data["main"]["temp"])
        feels_like = round(data["main"]["feels_like"])
        humidity = data["main"]["humidity"]
        wind_speed = data["wind"]["speed"]  # m/s
        wind_kmh = round(wind_speed * 3.6)
        weather_main = data["weather"][0]["main"]  # "Clear", "Clouds" stb.
        weather_hu = magyar_weather(weather_main)
        pop = data.get("pop", 0)  # csapadék valószínűsége (0-1)
        
        # Napkelte/napnyugta (UTC)
        sunrise_ts = data["sys"]["sunrise"]
        sunset_ts = data["sys"]["sunset"]
        sunrise = datetime.fromtimestamp(sunrise_ts, tz=timezone.utc).strftime("%H:%M")
        sunset = datetime.fromtimestamp(sunset_ts, tz=timezone.utc).strftime("%H:%M")
        
        # Előrejelzés a következő napokra (déli órák)
        forecast_resp = requests.get(FORECAST_URL)
        forecast_data = forecast_resp.json()
        forecast_list = []
        seen_dates = set()
        for item in forecast_data["list"]:
            dt_utc = datetime.fromtimestamp(item["dt"], tz=timezone.utc)
            date_str = dt_utc.strftime("%Y-%m-%d")
            if date_str not in seen_dates and dt_utc.hour >= 11 and dt_utc.hour <= 13:
                seen_dates.add(date_str)
                forecast_list.append({
                    "dt": item["dt"],
                    "main": {"temp": item["main"]["temp"]},
                    "pop": item.get("pop", 0)
                })
                if len(forecast_list) >= 3:
                    break
        
        # Névnapok (az aktuális UTC naphoz)
        namedays = get_namedays_for_utc_date(now_utc)
        
        return {
            "temp": temp,
            "feels_like": feels_like,
            "humidity": humidity,
            "wind_kmh": wind_kmh,
            "weather_main": weather_main,
            "weather_hu": weather_hu,
            "pop": int(pop * 100),
            "sunrise": sunrise,
            "sunset": sunset,
            "forecast": forecast_list,
            "now_dt": now_utc,          # UTC datetime, fontos!
            "namedays": namedays
        }
    except Exception as e:
        print(f"Hiba az időjárás lekérésekor: {e}")
        return None

def magyar_weather(english_main):
    """Angol időjárás szöveg magyarítása"""
    mapping = {
        "Clear": "Derült",
        "Clouds": "Felhős",
        "Rain": "Esős",
        "Snow": "Havas",
        "Fog": "Ködös",
        "Thunderstorm": "Viharos",
        "Drizzle": "Szakadó",
        "Mist": "Ködös",
        "Haze": "Ködös"
    }
    return mapping.get(english_main, english_main)

def get_day_hu(dt):
    """A datetime objektum napját adja vissza magyar névvel, nagybetűsen."""
    days = ["Hétfő", "Kedd", "Szerda", "Csütörtök", "Péntek", "Szombat", "Vasárnap"]
    # Ha dt UTC, akkor a hét napja az UTC szerint lesz helyes
    return days[dt.weekday()]

# ---------- HASZNÁLAT PÉLDA ----------
if __name__ == "__main__":
    weather = get_weather_data()
    if weather:
        print("Hőmérséklet:", weather["temp"], "°C")
        print("Névnap:", ", ".join(weather["namedays"]))
        print("Dátum (UTC):", weather["now_dt"].strftime("%Y-%m-%d %H:%M UTC"))
