# ── SZEKCIÓ 1: AKTUÁLIS (Finomhangolt fejléc és baseline) ──────────────────
SEC1_W = 650 
sec1_mid = curr_x + (SEC1_W // 2)

day_txt, desc_txt = get_day_hu(weather["now_dt"]).upper(), weather["weather_hu"].upper()
temp_txt, feel_txt = f"{weather['temp']}°C", f"{weather['feels_like']}°C"

# Méretek lekérése
t_bbox = draw.textbbox((0, 0), temp_txt, font=f_t)
t_w, t_h = t_bbox[2], t_bbox[3]
f_bbox = draw.textbbox((0, 0), feel_txt, font=f_s)
f_w, f_h_text = f_bbox[2], f_bbox[3]

# Teljes blokk szélessége az ikonnal együtt
main_w = ICON_DISPLAY_SIZE + 45 + t_w + 35 + FEEL_ICON_SIZE + 12 + f_w
start_x = sec1_mid - (main_w // 2)

# Fő ikon pozicionálása
if icon_img:
    paste_icon(img, icon_img, start_x, mid_y - ICON_DISPLAY_SIZE // 2)

# A szövegek kezdőpontja (tx)
tx = start_x + ICON_DISPLAY_SIZE + 45
temp_y = mid_y - (t_h // 2) + 5 # Picit lejjebb toltam a súlypont miatt

# --- FEJLÉC IGAZÍTÁSA ---
# A nap neve és a leírás közé tettem egy kis extra helyet (30px), 
# és pontosan a nagy hőfok (tx) fölé igazítottam
header_y = temp_y - 40 
draw.text((tx, header_y), day_txt, font=f_h, fill=colors["dim"])

# A borult/derült feliratot a nap neve után teszem, fix 30 pixel közzel
day_w_header = draw.textbbox((0, 0), day_txt, font=f_h)[2]
draw.text((tx + day_w_header + 30, header_y), desc_txt, font=f_h, fill=colors["dim"])

# FŐ HŐFOK (marad a helyén)
draw.text((tx, temp_y), temp_txt, font=f_t, fill=colors["main"])

# PIXEL PERFECT BASELINE (a kicsi szám alja a nagyéval egy vonalban)
base_line_y = temp_y + t_h
feel_x = tx + t_w + 35
if feel_icon_img:
    paste_icon(img, feel_icon_img, feel_x, base_line_y - FEEL_ICON_SIZE - 5, size=FEEL_ICON_SIZE)
draw.text((feel_x + FEEL_ICON_SIZE + 12, base_line_y - f_h_text - 3), feel_txt, font=f_s, fill=colors["dim"])
