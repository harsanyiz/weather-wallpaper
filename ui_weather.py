def draw_weather_widget(
    img, weather,
    icon_img, feel_icon_img, rainq_icon_img,
    wind1_icon_img, para_icon_img,
    forecast_icons,
    sunrise_icon_img, sunset_icon_img,
    namedays, tz_offset
):
    from logic_weather import get_day_hu

    bx, by, bw, bh = OFFSET_LEFT, WIDGET_Y, WIDGET_WIDTH, WIDGET_HEIGHT

    # --- HÁTTÉRKÉP BETÖLTÉSE (időjárás és napszak alapján) ---
    weather_condition = weather.get("weather_main", "Clear")
    now = weather["now_dt"]
    hour = now.hour
    is_day = 6 <= hour <= 18  # nappal 6-18 óra között
    
    bg_image = get_background_image(weather_condition, is_day)
    
    if bg_image:
        # Átméretezés a widget méretére
        bg_image = bg_image.resize((bw, bh), Image.Resampling.LANCZOS)
        # Beillesztés a widget helyére (maszk NÉLKÜL, hogy teljesen fedjen)
        img.paste(bg_image, (bx, by))
        
        # Világos/sötét szövegszínek meghatározása a háttér alapján
        bg_brightness = ImageStat.Stat(bg_image.convert("L")).mean[0]
        
        if bg_brightness > 145:
            colors = {
                "main":     (20,  20,  35,  255),
                "dim":      (120, 110, 140, 200),
                "line":     (0,   0,   0,   12),
                "accent":   (255, 100, 50,  255),
                "accent2":  (0,   150, 255, 255),
            }
        else:
            colors = {
                "main":     (255, 255, 255, 255),
                "dim":      (150, 155, 180, 200),
                "line":     (100, 150, 255, 30),
                "accent":   (0,   230, 200, 255),
                "accent2":  (0,   160, 255, 255),
            }
    else:
        # Ha nincs háttérkép, használd a gradiens megoldást
        brightness = ImageStat.Stat(img.crop((bx, by, bx + bw, by + bh)).convert("L")).mean[0]

        if brightness > 145:
            colors = {
                "main":     (20,  20,  35,  255),
                "dim":      (120, 110, 140, 200),
                "line":     (0,   0,   0,   12),
                "accent":   (255, 100, 50,  255),
                "accent2":  (0,   150, 255, 255),
                "bg_start": (255, 255, 245, 255),  # alpha 255 - teljesen átlátszatlan
                "bg_end":   (245, 240, 255, 255),  # alpha 255 - teljesen átlátszatlan
            }
        else:
            colors = {
                "main":     (255, 255, 255, 255),
                "dim":      (150, 155, 180, 200),
                "line":     (100, 150, 255, 30),
                "accent":   (0,   230, 200, 255),
                "accent2":  (0,   160, 255, 255),
                "bg_start": (18,  18,  28,  255),  # alpha 255 - teljesen átlátszatlan
                "bg_end":   (28,  18,  38,  255),  # alpha 255 - teljesen átlátszatlan
            }

        draw = ImageDraw.Draw(img)

        # GRADIENT HÁTTÉR (teljesen átlátszatlan)
        gx = bx + GRADIENT_OFFSET
        bs, be = colors["bg_start"], colors["bg_end"]
        for y in range(by, by + bh):
            t = (y - by) / bh
            r = int(bs[0] + (be[0] - bs[0]) * t)
            g = int(bs[1] + (be[1] - bs[1]) * t)
            b = int(bs[2] + (be[2] - bs[2]) * t)
            draw.line([(gx, y), (gx + bw - GRADIENT_OFFSET, y)], fill=(r, g, b, 255), width=1)
        
        draw = ImageDraw.Draw(img)

    draw = ImageDraw.Draw(img)

    # ... a többi kód változatlan marad ...
