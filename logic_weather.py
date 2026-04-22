# logic_weather.py - Adatlekérés és feldolgozás
import requests
import os
from datetime import datetime, timezone, timedelta

API_KEY = os.environ.get("OWM_API_KEY")
CITY = "Budapest"

def get_image_name(weather_id, is_night):
    suffix = "night" if is_night else "day"
    if weather_id in [611, 612, 613, 615, 616]: return f"sleet_{suffix}"
    elif weather_id in [620, 621, 622, 600, 601, 602]: return f"snow_{suffix}"
    elif weather_id == 800: return f"sunny_{suffix}"
    else: return f"cloudy_{suffix}"

def get_weather_hu(weather_id):
    mapping = {800: "Derült", 801: "Pár felhő", 802: "Részben felhős", 803: "Felhős", 804: "Borult", 511: "Ónos eső"}
    return mapping.get(weather_id, "Változékony")

def get_day_hu(date_obj):
    napok = ["Hétfő", "Kedd", "Szerda", "Csütörtök", "Péntek", "Szombat", "Vasárnap"]
    return napok[date_obj.weekday()]

def fetch_weather_data():
    """Lekéri az aktuális időjárást és a 3 napos előrejelzést"""
    resp = requests.get(f"https://api.openweathermap.org/data/2.5/weather?q={CITY}&appid={API_KEY}&units=metric")
    data = resp.json()
    f_resp = requests.get(f"https://api.openweathermap.org/data/2.5/forecast?q={CITY}&appid={API_KEY}&units=metric")
    f_data = f_resp.json()

    temp = round(data["main"]["temp"])
    weather_id = data["weather"][0]["id"]
    tz_offset = data.get("timezone", 3600)
    now_dt = datetime.now(timezone(timedelta(seconds=tz_offset)))
    update_time = now_dt.strftime("%H:%M")
    is_night = now_dt.timestamp() < data["sys"]["sunrise"] or now_dt.timestamp() > data["sys"]["sunset"]
    image_name = get_image_name(weather_id, is_night)
    weather_hu = get_weather_hu(weather_id)

    # Következő 3 nap délutáni adatai
    forecast_list = []
    seen_days = set()
    today = now_dt.date()
    for entry in f_data['list']:
        dt_obj = datetime.fromtimestamp(entry['dt'], tz=timezone(timedelta(seconds=tz_offset)))
        if dt_obj.date() > today and dt_obj.date() not in seen_days and dt_obj.hour >= 12:
            forecast_list.append({
                "dt": entry['dt'],
                "temp": round(entry['main']['temp']),
                "day_name": get_day_hu(dt_obj)
            })
            seen_days.add(dt_obj.date())
        if len(forecast_list) == 3: break

    weather_data = {
        "temp": temp,
        "weather_id": weather_id,
        "weather_hu": weather_hu,
        "feels_like": round(data['main']['feels_like']),
        "wind_speed": round(data['wind']['speed'] * 3.6),
        "humidity": data['main']['humidity'],
        "day_name": get_day_hu(now_dt),
        "is_night": is_night,
        "image_name": image_name,
        "tz_offset": tz_offset
    }
    
    return weather_data, forecast_list, update_time, data