# 🌤 Weather Wallpaper – Projectivy Launcher

Automatikus időjárás-alapú háttérkép Budapest számára, Projectivy Launcher + Overflight pluginhoz.

## Hogyan működik?

- GitHub Actions **2 óránként** lekéri a budapesti időjárást (OpenWeatherMap)
- Kiválasztja a megfelelő háttérképet (14 db, nappal/éjszaka párok)
- Ráírja a hőmérsékletet és időjárásadatokat
- Frissíti a `weather.json`-t amit az Overflight olvas

## Beállítás

### 1. GitHub Secret hozzáadása
- Repo → Settings → Secrets and variables → Actions → New repository secret
- Név: `OWM_API_KEY`
- Érték: az OpenWeatherMap API kulcsod

### 2. Overflight beállítás a TV-n
- Overflight plugin → Media source URL:
```
https://raw.githubusercontent.com/harsanyiz/weather-wallpaper/main/weather.json
```

### 3. Képek cseréje
A `images/` mappában lévő fájlokat bármikor lecserélheted:

| Fájlnév | Időjárás |
|---------|----------|
| `sunny_day.jpg` | Napos – nappal |
| `sunny_night.jpg` | Napos – éjszaka |
| `cloudy_day.jpg` | Felhős – nappal |
| `cloudy_night.jpg` | Felhős – éjszaka |
| `rainy_day.jpg` | Esős – nappal |
| `rainy_night.jpg` | Esős – éjszaka |
| `snow_day.jpg` | Havas – nappal |
| `snow_night.jpg` | Havas – éjszaka |
| `sleet_day.jpg` | Ónos eső – nappal |
| `sleet_night.jpg` | Ónos eső – éjszaka |
| `hail_day.jpg` | Jégeső – nappal |
| `hail_night.jpg` | Jégeső – éjszaka |
| `foggy_day.jpg` | Ködös – nappal |
| `foggy_night.jpg` | Ködös – éjszaka |

> ⚠️ A `current.jpg`-t NE cseréld – azt a bot írja felül!
