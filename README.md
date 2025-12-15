# ✈️ Air Baltic - Hintaseuranta Home Assistantiin

Automaattinen hintaseurantaohjelma Air Balticin lennoille, integroitu Home Assistantiin REST API:n kautta.

## �� Ominaisuudet

- 🔍 Monitoroi Air Balticin lennon hintoja
- 📊 Tallentaa hintahistorian  
- 🏠 Lähettää hinnan Home Assistantiin real-time
- ⚠️ Seuraa hinnan muutoksia
- 📝 Lokittaa kaikki tapahtumat

## 🚀 Asennus & Käyttö

### 1. Riippuvuuksien asennus

```bash
cd /home/rami/omat/hintaseuranta_airbaltic
uv sync
```

### 2. Konfiguraatio

Muokkaa `config.json`:

```json
{
  "origin": "AMS",                              // Lähtökaupunki
  "destination": "OUL",                         // Kohdekaupunki
  "passengers": 1,                              // Matkustajien määrä
  "month": 4,                                   // Kuukausi
  "check_interval": 3600,                       // Tarkistusväli sekunnissa
  "home_assistant": {
    "url": "http://homeassistant.local:8123",  // HA URL
    "token": "eyJhbGciOiJIUzI1NiIsInR5..."      // HA Long-lived access token
  }
}
```

**Home Assistant:in asetukset:**
1. Mene: **Asetukset → Sovellukset → Sovellukset ja ilmoitukset → Long-Lived Access Tokens**
2. Luo uusi token
3. Kopioi token `config.json`:iin

### 3. Käynnistä

```bash
uv run price_tracker.py
```

## 📊 Home Assistantissa

Ohjelma luo sensori:
```
sensor.airbaltic_ams_oul_price
```

---

**Happy price tracking! ✈️**
