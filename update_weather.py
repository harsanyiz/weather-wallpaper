import time
from PIL import Image

from logic_weather import (
    get_weather_data,
    get_icon_name,
    get_background_image_name,
    download_icon,
    get_todays_namedays,
    build_weather_json,
)
from ui_weather import draw_weather_widget


def main():
    try:
        # ── Időjárás adatok lekérése ──────────────────────────────────────────
        weather = get_weather_data()

        weather_id = weather["weather_id"]
        is_night   = weather["is_night"]

        # ── Ikonok letöltése GitHubról ───────────────────────────────────────
        icon_name        = get_icon_name(weather_id, is_night)
        icon_img         = download_icon(icon_name)
        feel_icon_img    = download_icon("feel")
        sunrise_icon_img = download_icon("day_clear")
        sunset_icon_img  = download_icon("night_clear")

        # Forecast ikonok – minden előrejelzett naphoz külön
        forecast_icons = []
        for entry in weather["forecast"]:
            f_id        = entry["weather"][0]["id"]
            f_icon_name = get_icon_name(f_id, is_night=False)
            forecast_icons.append(download_icon(f_icon_name))

        # ── Névnapok lekérése GitHubról ───────────────────────────────────────
        namedays = get_todays_namedays()

        # ── Háttérkép betöltése és 4K-ra méretezése ──────────────────────────
        bg_name = get_background_image_name(weather_id, is_night)
        src = f"images/{bg_name}.jpg"
        dst = "images/current.jpg"

        img = Image.open(src).convert("RGB")
        if img.size != (3840, 2160):
            img = img.resize((3840, 2160), Image.Resampling.LANCZOS)

        img = img.convert("RGBA")

        # ── Widget rárajzolása ────────────────────────────────────────────────
        draw_weather_widget(
            img=img,
            weather=weather,
            icon_img=icon_img,
            feel_icon_img=feel_icon_img,
            forecast_icons=forecast_icons,
            sunrise_icon_img=sunrise_icon_img,
            sunset_icon_img=sunset_icon_img,
            namedays=namedays,
            tz_offset=weather["tz_offset"],
        )

        # ── Mentés ───────────────────────────────────────────────────────────
        img.convert("RGB").save(dst, "JPEG", quality=100, subsampling=0)
        print(f"✅ Kép mentve: {dst}")

        # ── JSON frissítése ───────────────────────────────────────────────────
        v_param = int(time.time())
        build_weather_json(weather["weather_hu"], weather["temp"], v_param)
        print("✅ weather.json frissítve")

    except Exception as e:
        print(f"❌ Hiba: {e}")
        raise


if __name__ == "__main__":
    main()
