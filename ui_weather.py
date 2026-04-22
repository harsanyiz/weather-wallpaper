from PIL import Image, ImageDraw, ImageFont, ImageStat, ImageFilter
from datetime import datetime, timezone, timedelta
import math

# ============================================================
# XIAOMI PREMIUM TV WIDGET DESIGN - 4K HORIZONTAL
# ============================================================
WIDGET_WIDTH  = 2400
WIDGET_HEIGHT = 220  # Slightly taller for premium look
WIDGET_Y      = 80   # Moved up a bit
OFFSET_LEFT   = 135
INNER_MARGIN  = 60

# Premium font sizes
FONT_TEMP     = 88   # Main temperature
FONT_HEADER   = 26   # Day + weather description
FONT_LABEL    = 24   # Labels (WIND, HUMIDITY, etc.)
FONT_VALUE    = 34   # Values
FONT_SMALL    = 28   # Feels like temp
FONT_DATETIME = 26   # Date+time
FONT_NAME     = 32   # Nameday
FONT_FORECAST_DAY = 24   # Forecast day name
FONT_FORECAST_TEMP = 32  # Forecast temperature
FONT_SUN_TIME = 32   # Sunrise/sunset times

# Icon sizes - Premium proportions
ICON_DISPLAY_SIZE  = 150   # Main weather icon
FEEL_ICON_SIZE     = 38    # Feels like icon
WIND_ICON_SIZE     = 38    # Wind icon
HUMIDITY_ICON_SIZE = 38    # Humidity icon
SUN_ICON_SIZE      = 38    # Sunrise/sunset icons
FORECAST_ICON_SIZE = 48    # Forecast icons
ICON_GAP           = 12    # Gap between icon and text

# Premium spacing
SECTION_GAP        = 55     # Between sections
VERTICAL_SPACING   = 28     # Vertical spacing between rows
HEADER_BOTTOM_GAP  = 12     # Gap after header row

# Glass morphism effect
GLASS_BLUR = 15
GLASS_OPACITY = 180
CORNER_RADIUS = 30
# ============================================================


def find_font(bold=False, light=False):
    paths = [
        "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf" if bold else
        "/usr/share/fonts/truetype/noto/NotoSans-Light.ttf" if light else
        "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for p in paths:
        import os
        if os.path.exists(p):
            return p
    return None


def get_f(size, bold=False, light=False):
    path = find_font(bold, light)
    if path:
        return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def get_premium_colors(brightness):
    """Xiaomi-style gradient-aware colors"""
    if brightness > 145:
        # Light theme
        return {
            "main": (28, 28, 30, 255),      # Dark gray
            "dim": (110, 110, 115, 230),    # Medium gray
            "accent": (0, 122, 255, 255),   # Xiaomi blue accent
            "line": (200, 200, 200, 60),    # Subtle separator
            "glass": (255, 255, 255, GLASS_OPACITY),
        }
    else:
        # Dark theme - Premium dark mode
        return {
            "main": (255, 255, 255, 255),   # Pure white
            "dim": (180, 180, 185, 230),    # Soft white
            "accent": (0, 150, 255, 255),   # Brighter accent for dark
            "line": (80, 80, 90, 80),       # Subtle dark separator
            "glass": (30, 30, 35, GLASS_OPACITY),
        }


def rounded_rectangle(draw, xy, radius, fill=None, outline=None, width=1):
    """Draw rounded rectangle"""
    x1, y1, x2, y2 = xy
    draw.rectangle([x1+radius, y1, x2-radius, y2], fill=fill, outline=outline)
    draw.rectangle([x1, y1+radius, x2, y2-radius], fill=fill, outline=outline)
    draw.pieslice([x1, y1, x1+radius*2, y1+radius*2], 180, 270, fill=fill, outline=outline)
    draw.pieslice([x2-radius*2, y1, x2, y1+radius*2], 270, 360, fill=fill, outline=outline)
    draw.pieslice([x1, y2-radius*2, x1+radius*2, y2], 90, 180, fill=fill, outline=outline)
    draw.pieslice([x2-radius*2, y2-radius*2, x2, y2], 0, 90, fill=fill, outline=outline)


def paste_icon(img, icon_img, x, y, size=ICON_DISPLAY_SIZE, opacity=255):
    """Premium icon pasting with optional opacity"""
    if icon_img is None:
        return
    resized = icon_img.resize((size, size), Image.Resampling.LANCZOS)
    
    # Apply opacity if needed
    if opacity < 255 and resized.mode == 'RGBA':
        alpha = resized.split()[3]
        alpha = alpha.point(lambda p: p * opacity // 255)
        resized.putalpha(alpha)
    
    img.paste(resized, (int(x), int(y)), resized)


def draw_weather_widget(img, weather, icon_img, feel_icon_img,
                        wind_icon_img, para_icon_img,
                        forecast_icons, sunrise_icon_img, sunset_icon_img,
                        namedays, tz_offset):
    """
    Xiaomi Premium TV Widget Design
    """
    from logic_weather import get_day_hu

    bx = OFFSET_LEFT
    by = WIDGET_Y
    bw = WIDGET_WIDTH
    bh = WIDGET_HEIGHT

    # Create glass morphism background
    overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    
    # Get region brightness for color adaptation
    region = img.crop((bx, by, bx + bw, by + bh)).convert("L")
    colors = get_premium_colors(ImageStat.Stat(region).mean[0])
    
    # Draw premium glass background
    rounded_rectangle(overlay_draw, (bx, by, bx + bw, by + bh), 
                     CORNER_RADIUS, fill=colors["glass"])
    
    # Add subtle gradient overlay
    for i in range(bh):
        alpha = int(50 * (1 - i / bh))
        overlay_draw.line([(bx, by + i), (bx + bw, by + i)], 
                         fill=(255, 255, 255, alpha))
    
    img.paste(overlay, (0, 0), overlay)
    
    draw = ImageDraw.Draw(img)
    
    # Premium fonts
    f_t    = get_f(FONT_TEMP, bold=True)
    f_h    = get_f(FONT_HEADER, light=True)
    f_l    = get_f(FONT_LABEL, light=True)
    f_v    = get_f(FONT_VALUE, bold=True)
    f_s    = get_f(FONT_SMALL)
    f_dt   = get_f(FONT_DATETIME, light=True)
    f_n    = get_f(FONT_NAME, bold=True)
    f_fd   = get_f(FONT_FORECAST_DAY, light=True)
    f_fv   = get_f(FONT_FORECAST_TEMP, bold=True)
    f_sun  = get_f(FONT_SUN_TIME, bold=True)

    curr_x = int(bx + INNER_MARGIN)
    mid_y  = int(by + (bh // 2))
    now_dt = weather["now_dt"]

    # ── SECTION 1: MAIN WEATHER ────────────────────────────────────────────────
    day_txt  = get_day_hu(now_dt).upper()
    desc_txt = weather["weather_hu"].upper()
    temp_txt = f"{weather['temp']}°"
    feel_txt = f"{weather['feels_like']}°"

    # Measure text
    day_w    = draw.textbbox((0, 0), day_txt,  font=f_h)[2]
    desc_w   = draw.textbbox((0, 0), desc_txt, font=f_h)[2]
    temp_w   = draw.textbbox((0, 0), temp_txt, font=f_t)[2]
    feel_w   = draw.textbbox((0, 0), feel_txt, font=f_s)[2]

    header_gap   = 12
    feel_row_w   = FEEL_ICON_SIZE + ICON_GAP + feel_w
    temp_row_w   = temp_w + 16 + feel_row_w
    
    # Layout
    icon_gap_px  = ICON_DISPLAY_SIZE + 35 if icon_img else 0

    if icon_img:
        paste_icon(img, icon_img, curr_x, mid_y - ICON_DISPLAY_SIZE // 2)

    tx = curr_x + icon_gap_px

    # Draw header (day + description) with accent dot
    header_y = mid_y - 58
    draw.text((tx, header_y), day_txt, font=f_h, fill=colors["dim"])
    draw.text((tx + day_w + header_gap, header_y), desc_txt, font=f_h, fill=colors["accent"])
    
    # Draw main temperature
    temp_y = header_y + 50
    draw.text((tx, temp_y), temp_txt, font=f_t, fill=colors["main"])
    
    # Draw feels like with icon
    feel_icon_y = temp_y + 8
    feel_text_y = temp_y + 12
    feel_x = tx + temp_w + 18
    
    if feel_icon_img:
        paste_icon(img, feel_icon_img, feel_x, feel_icon_y, size=FEEL_ICON_SIZE)
    draw.text((feel_x + FEEL_ICON_SIZE + ICON_GAP, feel_text_y),
              feel_txt, font=f_s, fill=colors["dim"])

    curr_x += icon_gap_px + temp_w + 18 + feel_row_w + SECTION_GAP
    
    # Premium separator
    draw.line([(curr_x, by + 30), (curr_x, by + bh - 30)], 
              fill=colors["line"], width=2)
    curr_x += 45

    # ── SECTION 2: WIND + HUMIDITY (Stacked vertically) ───────────────────────
    wind_val = f"{weather['wind_kmh']} km/h"
    hum_val  = f"{weather['humidity']}%"
    
    # Labels
    wind_label = "SZÉL"
    hum_label = "PÁRA"
    
    wind_lw = draw.textbbox((0, 0), wind_label, font=f_l)[2]
    wind_vw = draw.textbbox((0, 0), wind_val, font=f_v)[2]
    hum_lw = draw.textbbox((0, 0), hum_label, font=f_l)[2]
    hum_vw = draw.textbbox((0, 0), hum_val, font=f_v)[2]
    
    col2_w = max(WIND_ICON_SIZE + ICON_GAP + max(wind_lw, wind_vw),
                 HUMIDITY_ICON_SIZE + ICON_GAP + max(hum_lw, hum_vw))

    top_y = mid_y - 45
    bot_y = mid_y + 10

    # Wind row
    if wind_icon_img:
        paste_icon(img, wind_icon_img, curr_x, top_y, size=WIND_ICON_SIZE)
    draw.text((curr_x + WIND_ICON_SIZE + ICON_GAP, top_y - 5), 
              wind_label, font=f_l, fill=colors["dim"])
    draw.text((curr_x + WIND_ICON_SIZE + ICON_GAP, top_y + 22), 
              wind_val, font=f_v, fill=colors["main"])

    # Humidity row
    if para_icon_img:
        paste_icon(img, para_icon_img, curr_x, bot_y, size=HUMIDITY_ICON_SIZE)
    draw.text((curr_x + HUMIDITY_ICON_SIZE + ICON_GAP, bot_y - 5), 
              hum_label, font=f_l, fill=colors["dim"])
    draw.text((curr_x + HUMIDITY_ICON_SIZE + ICON_GAP, bot_y + 22), 
              hum_val, font=f_v, fill=colors["main"])

    curr_x += col2_w + SECTION_GAP
    draw.line([(curr_x, by + 30), (curr_x, by + bh - 30)], 
              fill=colors["line"], width=2)
    curr_x += 45

    # ── SECTION 3: SUNRISE + SUNSET ───────────────────────────────────────────
    sunrise_txt = weather["sunrise"]
    sunset_txt  = weather["sunset"]
    
    sunrise_label = "KELÉS"
    sunset_label = "NYUGTA"
    
    sr_lw = draw.textbbox((0, 0), sunrise_label, font=f_l)[2]
    sr_vw = draw.textbbox((0, 0), sunrise_txt, font=f_sun)[2]
    ss_lw = draw.textbbox((0, 0), sunset_label, font=f_l)[2]
    ss_vw = draw.textbbox((0, 0), sunset_txt, font=f_sun)[2]
    
    sun_col_w = max(SUN_ICON_SIZE + ICON_GAP + max(sr_lw, sr_vw),
                    SUN_ICON_SIZE + ICON_GAP + max(ss_lw, ss_vw))

    # Sunrise
    if sunrise_icon_img:
        paste_icon(img, sunrise_icon_img, curr_x, top_y, size=SUN_ICON_SIZE)
    draw.text((curr_x + SUN_ICON_SIZE + ICON_GAP, top_y - 5), 
              sunrise_label, font=f_l, fill=colors["dim"])
    draw.text((curr_x + SUN_ICON_SIZE + ICON_GAP, top_y + 22), 
              sunrise_txt, font=f_sun, fill=colors["main"])

    # Sunset
    if sunset_icon_img:
        paste_icon(img, sunset_icon_img, curr_x, bot_y, size=SUN_ICON_SIZE)
    draw.text((curr_x + SUN_ICON_SIZE + ICON_GAP, bot_y - 5), 
              sunset_label, font=f_l, fill=colors["dim"])
    draw.text((curr_x + SUN_ICON_SIZE + ICON_GAP, bot_y + 22), 
              sunset_txt, font=f_sun, fill=colors["main"])

    curr_x += sun_col_w + SECTION_GAP
    draw.line([(curr_x, by + 30), (curr_x, by + bh - 30)], 
              fill=colors["line"], width=2)
    curr_x += 45

    # ── SECTION 4: FORECAST (3 days) ──────────────────────────────────────────
    for i, day_entry in enumerate(weather["forecast"]):
        d_name   = get_day_hu(datetime.fromtimestamp(day_entry["dt"])).upper()[:3]
        f_val    = f"{round(day_entry['main']['temp'])}°"
        
        d_name_w = draw.textbbox((0, 0), d_name, font=f_fd)[2]
        f_val_w  = draw.textbbox((0, 0), f_val, font=f_fv)[2]
        col_w    = max(d_name_w, f_val_w, FORECAST_ICON_SIZE + 10)

        fc_icon = forecast_icons[i] if i < len(forecast_icons) else None
        if fc_icon:
            paste_icon(img, fc_icon,
                       curr_x + (col_w - FORECAST_ICON_SIZE) // 2,
                       mid_y - 48,
                       size=FORECAST_ICON_SIZE)

        draw.text((curr_x + (col_w - d_name_w) // 2, mid_y + 10),
                  d_name, font=f_fd, fill=colors["dim"])
        draw.text((curr_x + (col_w - f_val_w) // 2, mid_y + 38),
                  f_val, font=f_fv, fill=colors["main"])
        curr_x += col_w + 25

    # ── SECTION 5: NAMEDAY ────────────────────────────────────────────────────
    draw.line([(curr_x, by + 30), (curr_x, by + bh - 30)], 
              fill=colors["line"], width=2)
    curr_x += 45

    nameday_value = ", ".join(n.strip().rstrip("\\") for n in namedays)
    
    # Premium nameday card
    nameday_x = curr_x
    nameday_width = 280
    nameday_height = 90
    
    # Draw subtle background for nameday
    rounded_rectangle(draw, (nameday_x, mid_y - 45, nameday_x + nameday_width, mid_y + 45), 
                     20, fill=colors["glass"])
    
    draw.text((nameday_x + 20, mid_y - 30), "NÉVNAP", font=f_l, fill=colors["accent"])
    draw.text((nameday_x + 20, mid_y), nameday_value, font=f_n, fill=colors["main"])

    curr_x += nameday_width + SECTION_GAP

    # ── SECTION 6: AIR QUALITY INDICATOR (Premium touch) ───────────────────────
    # Optional: Add a small air quality indicator if available
    if "aqi" in weather:
        aqi_value = weather.get("aqi", 42)  # Example default
        aqi_label = "LEVEGŐ"
        aqi_status = "JÓ" if aqi_value <= 50 else "KÖZEPES" if aqi_value <= 100 else "ROSSZ"
        
        aqi_color = (76, 175, 80, 255) if aqi_value <= 50 else (255, 193, 7, 255) if aqi_value <= 100 else (244, 67, 54, 255)
        
        draw.text((curr_x, mid_y - 30), aqi_label, font=f_l, fill=colors["dim"])
        draw.text((curr_x, mid_y), aqi_status, font=f_n, fill=aqi_color)

    # ── DATE & TIME (Top right corner) ────────────────────────────────────────
    datetime_txt = now_dt.strftime("%Y.%m.%d  •  %H:%M")
    dt_w = draw.textbbox((0, 0), datetime_txt, font=f_dt)[2]
    dt_x = bx + bw - dt_w - INNER_MARGIN
    
    # Premium time background pill
    time_pill_padding = 20
    time_pill_height = 45
    rounded_rectangle(draw, 
                     (dt_x - time_pill_padding, by + 15, 
                      dt_x + dt_w + time_pill_padding, by + 15 + time_pill_height),
                     22, fill=colors["glass"])
    
    draw.text((dt_x, by + 28), datetime_txt, font=f_dt, fill=colors["main"])
