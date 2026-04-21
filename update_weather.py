# ── SZEKCIÓ 1: MA ──────────────────────────────────────────
# Érzet IKONNAL
feels_icon = load_icon("feel", size=32)
if feels_icon:
    img.paste(feels_icon, (curr_x, mid_y + 2), feels_icon)
feels_txt = f"érzet: {feels}°C"
draw.text((curr_x + 40, mid_y + 5), feels_txt, font=f_d, fill=c_dim)

# ── SZEKCIÓ 3: SZÉL + PÁRA (IKONOKKAL, középre) ────────────
wind_icon = load_icon("tornado", size=32)
hum_icon = load_icon("para", size=32)

# Ikonok + szövegek
wind_txt = f"{wind} km/h"
hum_txt = f"{humidity}%"

wind_w = draw.textbbox((0, 0), wind_txt, font=f_d)[2]
hum_w = draw.textbbox((0, 0), hum_txt, font=f_d)[2]

# Teljes szélesség: ikon1 + szóköz + szöveg1 + gap + ikon2 + szóköz + szöveg2
total_w2 = 32 + 8 + wind_w + 40 + 32 + 8 + hum_w
info_x = curr_x + (available_width - total_w2) // 2

if wind_icon:
    img.paste(wind_icon, (info_x, mid_y + 12), wind_icon)
draw.text((info_x + 32 + 8, mid_y + 15), wind_txt, font=f_d, fill=c_dim)

if hum_icon:
    img.paste(hum_icon, (info_x + 32 + 8 + wind_w + 40, mid_y + 12), hum_icon)
draw.text((info_x + 32 + 8 + wind_w + 40 + 32 + 8, mid_y + 15), hum_txt, font=f_d, fill=c_dim)

# ── SZEKCIÓ 5: NÉVNAPOK + FRISSÍTVE (középre, nagyobb) ─────
FONT_NAMEDAY = 32  # nagyobb

if nameday_one_line:
    # Névnapok középre
    nameday_w = draw.textbbox((0, 0), nameday_one_line, font=f_n)[2]
    nameday_x = (OFFSET_LEFT + WIDGET_WIDTH - INNER_MARGIN + curr_x) // 2
    # vagy: widget közepe
    center_x = OFFSET_LEFT + WIDGET_WIDTH // 2
    draw.text((center_x - nameday_w // 2, y_bot - 55), nameday_one_line, font=f_n, fill=c_dim)
    
    # Frissítve alá, kisebbel
    upd_text = f"Frissítve: {local_now.strftime('%H:%M')}"
    upd_w = draw.textbbox((0, 0), upd_text, font=f_u)[2]
    draw.text((center_x - upd_w // 2, y_bot - 25), upd_text, font=f_u, fill=c_main)
