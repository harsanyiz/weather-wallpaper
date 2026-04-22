def draw_weather_widget(img, weather, icon_img, feel_icon_img, rainq_icon_img, wind1_icon_img, para_icon_img, forecast_icons, sunrise_icon_img, sunset_icon_img, namedays, tz_offset):
    from logic_weather import get_day_hu
    bx, by, bw, bh = OFFSET_LEFT, WIDGET_Y, WIDGET_WIDTH, WIDGET_HEIGHT
    
    # Automatikus sötét/világos mód - LUXUS KÍNAI EV színek
    brightness = ImageStat.Stat(img.crop((bx, by, bx + bw, by + bh)).convert("L")).mean[0]
    
    if brightness > 145:
        colors = {
            "main": (20, 20, 35, 255),
            "dim": (120, 110, 140, 200),
            "line": (0, 0, 0, 12),
            "accent": (255, 100, 50, 255),
            "accent2": (0, 200, 180, 255),
            "bg_start": (255, 255, 245, 220),
            "bg_end": (245, 240, 255, 220)
        }
    else:
        colors = {
            "main": (255, 255, 255, 255),
            "dim": (150, 155, 180, 200),
            "line": (100, 150, 255, 30),
            "accent": (0, 230, 200, 255),
            "accent2": (180, 100, 255, 255),
            "bg_start": (18, 18, 28, 210),
            "bg_end": (28, 18, 38, 210)
        }
    
    draw = ImageDraw.Draw(img)
    
    # GRADIENT HÁTTÉR - javítva: 10 pixel balra tolás
    gradient_start_x = bx - 10  # 10 pixel balra
    for y in range(by, by + bh):
        ratio = (y - by) / bh
        r = int(colors["bg_start"][0] * (1 - ratio) + colors["bg_end"][0] * ratio)
        g = int(colors["bg_start"][1] * (1 - ratio) + colors["bg_end"][1] * ratio)
        b = int(colors["bg_start"][2] * (1 - ratio) + colors["bg_end"][2] * ratio)
        a = colors["bg_start"][3]
        draw.line([(gradient_start_x, y), (gradient_start_x + bw, y)], fill=(r, g, b, a), width=1)
    
    mid_y = by + (bh // 2)
    curr_x = bx + INNER_MARGIN
    
    # Betűtípusok - a fontosabbakhoz Heavy, a többiekhez Bold vagy Regular
    f_t = get_f(FONT_TEMP, heavy=True)
    f_h = get_f(FONT_HEADER, bold=True)
    f_v = get_f(FONT_VALUE, heavy=True)
    f_s = get_f(FONT_SMALL)
    f_dt = get_f(FONT_DATETIME)
    f_n = get_f(FONT_NAME, bold=True)
    f_fd = get_f(FONT_FORECAST_DAY, bold=True)
    f_fv = get_f(FONT_FORECAST_TEMP, heavy=True)

    # 1. AKTUÁLIS BLOKK (HŐFOK + ESŐ/ÉRZET EGYMÁS FELETT)
    SEC1_W = 820
    temp_txt, feel_txt, rain_txt = f"{weather['temp']}°C", f"{weather['feels_like']}°C", f"{weather.get('pop', 0)}%"
    
    t_bbox = draw.textbbox((0, 0), temp_txt, font=f_t)
    t_w = t_bbox[2]
    
    main_content_w = ICON_DISPLAY_SIZE + 40 + t_w + 60 + 110
    start_x = (curr_x + SEC1_W // 2) - (main_content_w // 2)
    
    paste_icon(img, icon_img, start_x, mid_y - ICON_DISPLAY_SIZE // 2)
    tx, ty = start_x + ICON_DISPLAY_SIZE + 40, mid_y - (t_bbox[3] // 2) + 5
    
    # Fejléc (NAP + ÁLLAPOT)
    draw.text((tx + 20, mid_y - 65), get_day_hu(weather["now_dt"]).upper(), font=f_h, fill=colors["accent2"])
    day_w = draw.textbbox((0, 0), get_day_hu(weather["now_dt"]).upper(), font=f_h)[2]
    draw.text((tx + 20 + day_w + 30, mid_y - 65), weather["weather_hu"].upper(), font=f_h, fill=colors["accent"])
    
    # Fő Hőfok
    draw.text((tx, ty), temp_txt, font=f_t, fill=colors["main"])
    
    # INFÓ OSZLOP (Eső esélye fent, Érzet lent)
    info_x = tx + t_w + 60
    
    if rainq_icon_img: 
        paste_icon(img, rainq_icon_img, info_x, mid_y - 42, size=42)
    draw.text((info_x + 52, mid_y - 42), rain_txt, font=f_s, fill=colors["dim"])
    
    if feel_icon_img: 
        paste_icon(img, feel_icon_img, info_x + 4, mid_y + 8, size=36)
    draw.text((info_x + 52, mid_y + 8), feel_txt, font=f_s, fill=colors["dim"])
    
    curr_x += SEC1_W
    draw.line([(curr_x, by + 50), (curr_x, by + bh - 50)], fill=colors["line"], width=2)

    # 2. SZÉL & PÁRA
    SEC2_W, ix = 300, curr_x + 70
    for i, (val, unit, icon, sz) in enumerate([(weather['wind_kmh'], " km/h", wind1_icon_img, WIND_ICON_SIZE), (weather['humidity'], "%", para_icon_img, PARA_ICON_SIZE)]):
        y_pos = mid_y - 68 if i == 0 else mid_y + 12
        if icon: 
            paste_icon(img, icon, ix, y_pos + 4, size=sz)
        draw.text((ix + 58, y_pos), f"{val}{unit}", font=f_v, fill=colors["main"])
    curr_x += SEC2_W
    draw.line([(curr_x, by + 50), (curr_x, by + bh - 50)], fill=colors["line"], width=2)

    # 3. NAPKELTE / NAPNYUGTA
    SEC3_W, sx = 260, curr_x + 70
    for i, (val, icon) in enumerate([(weather['sunrise'], sunrise_icon_img), (weather['sunset'], sunset_icon_img)]):
        y_pos = mid_y - 65 if i == 0 else mid_y + 10
        if icon: 
            paste_icon(img, icon, sx, y_pos + 6, size=SUN_ICON_SIZE)
        draw.text((sx + 58, y_pos), val, font=f_v, fill=colors["main"])
    curr_x += SEC3_W
    draw.line([(curr_x, by + 50), (curr_x, by + bh - 50)], fill=colors["line"], width=2)

    # 4. ELŐREJELZÉS (3 NAP)
    SEC4_W, slot_w = 540, 180
    for i, day_entry in enumerate(weather["forecast"]):
        sm = curr_x + (i * slot_w) + (slot_w // 2)
        dn = get_day_hu(datetime.fromtimestamp(day_entry["dt"])).upper()[:3]
        fv = f"{round(day_entry['main']['temp'])}°C"
        if i < len(forecast_icons): 
            paste_icon(img, forecast_icons[i], sm - 25, mid_y - 75, size=50)
        draw.text((sm - draw.textbbox((0, 0), dn, font=f_fd)[2] // 2, mid_y - 15), dn, font=f_fd, fill=colors["accent2"])
        draw.text((sm - draw.textbbox((0, 0), fv, font=f_fv)[2] // 2, mid_y + 15), fv, font=f_fv, fill=colors["main"])
        
        pop_val = day_entry.get('pop', 0)
        if pop_val > 0:
            pop_txt = f"{round(pop_val * 100)}%"
            draw.text((sm - draw.textbbox((0, 0), pop_txt, font=f_s)[2] // 2, mid_y + 45), pop_txt, font=f_s, fill=colors["accent"])
    
    curr_x += SEC4_W
    draw.line([(curr_x, by + 50), (curr_x, by + bh - 50)], fill=colors["line"], width=2)

    # 5. NÉVNAP & IDŐ
    draw.text((curr_x + 50, mid_y - 50), "NÉVNAP", font=f_h, fill=colors["accent2"])
    draw.text((curr_x + 50, mid_y - 2), ", ".join(namedays), font=f_n, fill=colors["main"])
    
    dt_txt = weather["now_dt"].strftime("%Y.%m.%d  %H:%M")
    draw.text((bx + bw - draw.textbbox((0, 0), dt_txt, font=f_dt)[2] - 20, by + 15), dt_txt, font=f_dt, fill=colors["dim"])
