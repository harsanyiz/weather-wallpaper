# ui_weather.py - KINÉZET (design, elrendezés, rajzolás)
import os
from PIL import Image, ImageDraw, ImageFont, ImageStat
from datetime import datetime, timezone

# ============================================================
# 4K-S HORIZONTÁLIS DESIGN KONFIGURÁCIÓ
# ============================================================
WIDGET_WIDTH = 2200   
WIDGET_HEIGHT = 200   
WIDGET_Y = 100        
OFFSET_LEFT = 135     
INNER_MARGIN = 80     

# 4K-s betűméretek
FONT_TEMP = 90        
FONT_DESC = 32        
FONT_LABEL = 28       
FONT_VALUE = 36       
FONT_UPDATE = 24      
FONT_NAME_DAY = 28    # Névnap betűméret

# Ikon méret
ICON_SIZE = 64
# ============================================================

def find_font(bold=False):
    paths = [
        "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    ]
    for p in paths:
        if os.path.exists(p): return p
    return None

def get_font(size, bold=False):
    path = find_font(bold)
    if path: return ImageFont.truetype(path, size)
    return ImageFont.load_default()

def get_text_colors(brightness):
    if brightness > 145:
        return {"main": (0,0,0,230), "dim": (0,0,0,140), "line": (0,0,0,40)}
    return {"main": (255,255,255,255), "dim": (255,255,255,160), "line": (255,255,255,40)}

def load_icon(icon_name, size):
    """Betölti és átméretezi az ikont"""
    icon_path = f"images/ICONS_PNG80/{icon_name}"
    if os.path.exists(icon_path):
        icon = Image.open(icon_path).convert("RGBA")
        return icon.resize((size, size), Image.Resampling.LANCZOS)
    return None

def draw_weather_widget(img, weather_data, forecast_list, update_time):
    """A teljes widget kirajzolása a képre"""
    W, H = img.size
    bx, by, bw, bh = OFFSET_LEFT, WIDGET_Y, WIDGET_WIDTH, WIDGET_HEIGHT
    
    # Színmeghatározás a háttér alapján
    region = img.crop((bx, by, bx + bw, by + bh)).convert("L")
    avg_brightness = ImageStat.Stat(region).mean[0]
    colors = get_text_colors(avg_brightness)

    img = img.convert("RGBA")
    draw = ImageDraw.Draw(img)

    # Betűtípusok betöltése
    f_temp = get_font(FONT_TEMP, True)
    f_desc = get_font(FONT_DESC)
    f_label = get_font(FONT_LABEL)
    f_value = get_font(FONT_VALUE, True)
    f_update = get_font(FONT_UPDATE)
    f_name_day = get_font(FONT_NAME_DAY)

    curr_x = int(bx + INNER_MARGIN)
    mid_y = int(by + (bh // 2))

    # --- 1. SZEKCIÓ: NAP + HŐFOK + LEÍRÁS + IKON ---
    curr_x = _draw_current_weather(draw, img, curr_x, mid_y, by, bh, weather_data, f_temp, f_desc, f_label, colors)
    
    # --- 2. SZEKCIÓ: ADATOK (ÉRZET, SZÉL, PÁRA) ---
    curr_x = _draw_weather_details(draw, curr_x, mid_y, weather_data, f_label, f_value, colors)
    
    # --- 3. SZEKCIÓ: 3 NAPOS ELŐREJELZÉS ---
    curr_x = _draw_forecast(draw, curr_x, mid_y, by, bh, forecast_list, f_label, f_value, colors)
    
    # --- 4. SZEKCIÓ: FRISSÍTÉS ---
    curr_x = _draw_update_time(draw, curr_x, mid_y, update_time, f_update, colors)
    
    # --- 5. SZEKCIÓ: NÉVNAP (ha van) ---
    if weather_data.get("name_day") and weather_data["name_day"]:
        _draw_name_day(draw, curr_x + 20, mid_y, weather_data["name_day"], f_name_day, colors)
    
    return img

def _draw_current_weather(draw, img, curr_x, mid_y, by, bh, data, f_temp, f_desc, f_label, colors):
    day_txt = data["day_name"].upper()
    temp_txt = f"{data['temp']}°C"
    desc_txt = data["weather_hu"].upper()

    day_w = draw.textbbox((0, 0), day_txt, font=f_label)[2]
    temp_w = draw.textbbox((0, 0), temp_txt, font=f_temp)[2]
    desc_w = draw.textbbox((0, 0), desc_txt, font=f_desc)[2]
    max_w = max(day_w, temp_w, desc_w)
    
    # Ikon beszúrása a szöveg mellé
    icon = load_icon(data["icon_name"], ICON_SIZE)
    if icon:
        icon_x = curr_x + max_w + 20
        icon_y = mid_y - ICON_SIZE // 2
        img.paste(icon, (icon_x, icon_y), icon)
        max_w += ICON_SIZE + 30

    draw.text((int(curr_x + (max_w - day_w) / 2), int(mid_y - 85)), day_txt, font=f_label, fill=colors["dim"])
    draw.text((int(curr_x + (max_w - temp_w) / 2), int(mid_y - 60)), temp_txt, font=f_temp, fill=colors["main"])
    draw.text((int(curr_x + (max_w - desc_w) / 2), int(mid_y + 35)), desc_txt, font=f_desc, fill=colors["dim"])
    
    curr_x += int(max_w + 70)
    draw.line([(curr_x, by+40), (curr_x, by+bh-40)], fill=colors["line"], width=3)
    return curr_x + 60

def _draw_weather_details(draw, curr_x, mid_y, data, f_label, f_value, colors):
    fields = [
        ("Érzet", f"{data['feels_like']}°C"),
        ("Szél", f"{data['wind_speed']} km/h"),
        ("Pára", f"{data['humidity']}%")
    ]
    for label, val in fields:
        draw.text((curr_x, mid_y - 45), label.upper(), font=f_label, fill=colors["dim"])
        draw.text((curr_x, mid_y), val, font=f_value, fill=colors["main"])
        curr_x += max(draw.textbbox((0,0), label.upper(), font=f_label)[2], 
                      draw.textbbox((0,0), val, font=f_value)[2]) + 80
    return curr_x

def _draw_forecast(draw, curr_x, mid_y, by, bh, forecast_list, f_label, f_value, colors):
    if forecast_list:
        draw.line([(curr_x, by+40), (curr_x, by+bh-40)], fill=colors["line"], width=3)
        curr_x += 60
        for day in forecast_list:
            d_name = day["day_name"].upper()[:3]
            f_val = f"{day['temp']}°C"
            draw.text((curr_x, mid_y - 45), d_name, font=f_label, fill=colors["dim"])
            draw.text((curr_x, mid_y), f_val, font=f_value, fill=colors["main"])
            curr_x += 140
    return curr_x

def _draw_update_time(draw, curr_x, mid_y, update_time, f_update, colors):
    update_txt = f"FRISSÍTVE: {update_time}"
    draw.text((curr_x + 20, mid_y - 12), update_txt, font=f_update, fill=colors["dim"])
    return curr_x + draw.textbbox((0,0), update_txt, font=f_update)[2] + 60

def _draw_name_day(draw, x, mid_y, name_day, f_name_day, colors):
    """Kirajzolja a névnapot a widget végére"""
    name_day_txt = f"📅 NÉVNAP: {name_day}"
    draw.text((x, mid_y - 12), name_day_txt, font=f_name_day, fill=colors["dim"])
