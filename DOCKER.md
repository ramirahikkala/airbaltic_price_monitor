# 🐳 Docker & Docker Compose

Air Baltic hintaseuranta toimii myös Dockerissa!

## 🚀 Käynnistys Docker Composella

### 1. Valmistelu

Varmista että `config.json` on olemassa ja konfiguroitu:

```bash
cp config.example.json config.json
# Muokkaa config.json omilla asetuksillasi
```

### 2. Käynnistä

```bash
docker-compose up -d
```

### 3. Tarkista lokit

```bash
docker-compose logs -f airbaltic-price-tracker
```

## 📊 Docker komennot

**Käynnistä:**
```bash
docker-compose up -d
```

**Pysäytä:**
```bash
docker-compose down
```

**Uudelleenkäynnistä:**
```bash
docker-compose restart
```

**Poista kaikki:**
```bash
docker-compose down -v
```

**Lokit:**
```bash
docker-compose logs -f
docker-compose logs --tail=100
```

**Sisään konttiin:**
```bash
docker-compose exec airbaltic-price-tracker sh
```

## 🔧 Konfiguraatio

### docker-compose.yml

**Volume mountit:**
- `./config.json` - Asetukset (read-only)
- `./data` - Pysyvät tiedostot
- `airbaltic-logs` - Lokit

**Restart policy:**
- `unless-stopped` - Käynnistyy automaattisesti uudelleen

### Muuta config.json:ia

```bash
# Pysäytä kontti
docker-compose down

# Muokkaa config.json
nano config.json

# Käynnistä uudelleen
docker-compose up -d
```

## 📁 Tiedostorakenne

```
hintaseuranta_airbaltic/
├── Dockerfile              # Docker image määritys
├── docker-compose.yml      # Docker Compose konfiguraatio
├── .dockerignore           # Ohita tiedostot Docker buildissa
├── price_tracker.py        # Pääohjelma
├── config.json             # Asetukset
├── config.example.json     # Mallit
├── pyproject.toml          # Python dependencies
└── data/                   # Pysyvät tiedostot
    ├── price_history.json
    └── price_tracker.log
```

## 🔄 Jatkuva seuranta

Docker kontti käynnistyy automaattisesti ja seuraa hintoja jatkuvasti.

**Tilanne:**
```bash
docker-compose ps
```

**Näytä status:**
```bash
docker-compose stats
```

## 🆘 Vianmääritys

**Kontti ei käynnisty:**
```bash
docker-compose logs airbaltic-price-tracker
```

**Permission denied:**
```bash
# Tarkista että config.json on luettavissa
chmod 644 config.json
```

**Yhteys HA:han epäonnistuu:**
- Tarkista että HA URL on oikein
- Tarkista token
- Jos HA on samalla verkolla: käytä `host.docker.internal` tai konttiverkkoa

## 📦 Build uudelleen

```bash
# Build uudelleen
docker-compose build --no-cache

# Build ja käynnistä
docker-compose up -d --build
```

## 💾 Varmuuskopiointi

```bash
# Backup data
docker-compose exec airbaltic-price-tracker cat /app/data/price_history.json > backup.json

# Restore data
cat backup.json | docker-compose exec -T airbaltic-price-tracker tee /app/data/price_history.json
```

---

**Happy price tracking in Docker! 🐳✈️**
