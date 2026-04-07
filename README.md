# SLA - Portale Sindacato Lavoratori Autostradali

Sistema gestionale per rimborsi e comunicazioni del Sindacato Lavoratori Autostradali.

## Indice

- [Funzionalità](#funzionalità)
- [Architettura](#architettura)
- [Installazione](#installazione)
  - [Con Docker (Consigliato)](#con-docker-consigliato)
  - [Manuale](#installazione-manuale)
- [Configurazione](#configurazione)
- [Deploy su Raspberry Pi](#deploy-su-raspberry-pi)
- [Migrazione a servizio cloud](#migrazione-a-servizio-cloud)
- [Struttura Codice](#struttura-codice)
- [API Reference](#api-reference)

---

## Funzionalità

### Per tutti gli utenti
- **Bacheca**: Visualizza annunci e comunicati
- **Documenti**: Scarica modulistica e documenti

### Per Delegati/Segreteria/Segretario
- **Rimborsi**: Richiedi rimborsi per trasferte
  - Calcolo automatico KM con Google Maps
  - Upload ricevute spese (pasti, pedaggi)
  - Tracciamento stato (in attesa → approvato → pagato)

### Per Admin
- **Gestione Rimborsi**: Approva/rifiuta richieste
- **Gestione Utenti**: Modifica ruoli
- **Report**: Export CSV rendiconti annuali

### Per SuperAdmin
- **Gestione Sedi**: Crea/modifica concessionarie
- **Motivi Rimborso**: Configura causali
- **Vista globale**: Accesso a tutte le sedi

---

## Architettura

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Frontend  │────▶│   Backend   │────▶│   MongoDB   │
│    React    │     │   FastAPI   │     │             │
│   :3000     │     │   :8001     │     │   :27017    │
└─────────────┘     └─────────────┘     └─────────────┘
```

- **Frontend**: React 18, Tailwind CSS, Lucide Icons
- **Backend**: FastAPI, Motor (async MongoDB), JWT Auth
- **Database**: MongoDB 6.0

---

## Installazione

### Con Docker (Consigliato)

**Requisiti:**
- Docker 20.10+
- Docker Compose 2.0+
- 2GB RAM minimo

**Passi:**

```bash
# 1. Clona o copia i file
cd /percorso/progetto

# 2. Crea file .env da template
cp docker/.env.example docker/.env

# 3. IMPORTANTE: Modifica .env con valori sicuri
nano docker/.env
# - Cambia JWT_SECRET con una chiave casuale
# - Cambia ADMIN_PASSWORD

# 4. Avvia i container
cd docker
docker-compose up -d

# 5. Verifica che tutto funzioni
docker-compose ps
docker-compose logs -f
```

**Accesso:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8001
- Swagger Docs: http://localhost:8001/docs

### Installazione Manuale

**Requisiti:**
- Python 3.10+
- Node.js 18+
- MongoDB 6.0+

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
cp .env.example .env
# Modifica .env
uvicorn server:app --host 0.0.0.0 --port 8001
```

**Frontend:**
```bash
cd frontend
yarn install
cp .env.example .env
# Modifica REACT_APP_BACKEND_URL
yarn start
```

---

## Configurazione

### Variabili Ambiente

| Variabile | Descrizione | Default |
|-----------|-------------|---------|
| `MONGO_URL` | URL connessione MongoDB | `mongodb://localhost:27017` |
| `DB_NAME` | Nome database | `sla_sindacato` |
| `JWT_SECRET` | Chiave segreta per token JWT | **OBBLIGATORIO** |
| `ADMIN_EMAIL` | Email superadmin iniziale | `superadmin@sla.it` |
| `ADMIN_PASSWORD` | Password superadmin | **OBBLIGATORIO** |
| `GOOGLE_MAPS_API_KEY` | API Key Google Maps | (opzionale) |
| `FRONTEND_URL` | URL frontend per CORS | `http://localhost:3000` |

### Google Maps API (Opzionale)

Per abilitare il calcolo automatico KM:

1. Vai su https://console.cloud.google.com/
2. Crea un nuovo progetto
3. Abilita **Directions API**
4. Crea credenziali → API Key
5. Aggiungi la key in `GOOGLE_MAPS_API_KEY`

---

## Deploy su Raspberry Pi

### Con DietPi + Docker

**1. Installa DietPi su Raspberry Pi 4:**
- Scarica DietPi da https://dietpi.com/
- Flasha su SD card con Balena Etcher
- Avvia e completa setup iniziale

**2. Installa Docker:**
```bash
# Aggiorna sistema
apt update && apt upgrade -y

# Installa Docker
curl -fsSL https://get.docker.com | sh

# Aggiungi utente al gruppo docker
usermod -aG docker $USER

# Installa Docker Compose
apt install docker-compose-plugin -y

# Riavvia
reboot
```

**3. Copia il progetto:**
```bash
# Opzione A: Con git
git clone https://tuo-repo/sla-portale.git

# Opzione B: Con scp dal tuo PC
scp -r /percorso/progetto pi@raspberrypi:/home/pi/sla-portale
```

**4. Avvia:**
```bash
cd sla-portale/docker
cp .env.example .env
nano .env  # Configura
docker compose up -d
```

**5. Accesso da rete locale:**
- Trova IP del Raspberry: `hostname -I`
- Apri browser: `http://IP_RASPBERRY:3000`

### Ottimizzazioni per Raspberry Pi

In `docker-compose.yml`, aggiungi limiti memoria:

```yaml
services:
  mongodb:
    mem_limit: 512m
  backend:
    mem_limit: 256m
  frontend:
    mem_limit: 128m
```

---

## Migrazione a servizio cloud

Quando vorrai passare a un hosting a pagamento:

### Opzione 1: VPS con Docker (Consigliato)

Providers: Hetzner, DigitalOcean, Contabo

```bash
# 1. Crea VPS (Ubuntu 22.04, 2GB RAM)
# 2. Installa Docker (come sopra)
# 3. Copia progetto
# 4. Configura dominio (A record → IP server)
# 5. Aggiungi HTTPS con Caddy o Nginx + Let's Encrypt
```

### Opzione 2: Platform as a Service

- **Backend**: Railway, Render, Fly.io
- **Frontend**: Vercel, Netlify
- **Database**: MongoDB Atlas (free tier 512MB)

### Backup dati MongoDB

```bash
# Export
docker exec sla-mongodb mongodump --out /dump
docker cp sla-mongodb:/dump ./backup

# Import su nuovo server
docker cp ./backup nuovo-server:/dump
docker exec nuovo-mongodb mongorestore /dump
```

---

## Struttura Codice

```
/app
├── backend/
│   ├── server.py           # Entry point FastAPI
│   ├── requirements.txt    # Dipendenze Python
│   ├── .env               # Configurazione (non committare!)
│   │
│   ├── models/            # 📦 Modelli Pydantic
│   │   ├── __init__.py
│   │   ├── user.py        # Modelli utente/auth
│   │   ├── sede.py        # Modelli concessionarie
│   │   ├── rimborso.py    # Modelli rimborsi
│   │   └── documento.py   # Modelli documenti/annunci
│   │
│   ├── utils/             # 🔧 Utilità
│   │   ├── __init__.py
│   │   ├── config.py      # Configurazione da .env
│   │   ├── database.py    # Connessione MongoDB
│   │   └── auth.py        # JWT, password hashing
│   │
│   ├── services/          # ⚙️ Logica di business
│   │   ├── __init__.py
│   │   ├── google_maps.py # Calcolo KM
│   │   ├── file_handler.py# Upload/download file
│   │   └── notifications.py# Notifiche in-app
│   │
│   └── uploads/           # 📁 File caricati
│
├── frontend/
│   ├── src/
│   │   ├── App.js         # Entry point + routing
│   │   ├── context/       # Context React (auth)
│   │   ├── layouts/       # Layout principale
│   │   ├── pages/         # Pagine
│   │   └── lib/           # Utilità (formatting, etc)
│   └── ...
│
└── docker/
    ├── docker-compose.yml # Orchestrazione container
    ├── backend.Dockerfile
    ├── frontend.Dockerfile
    ├── nginx.conf         # Config Nginx per React
    └── .env.example       # Template variabili
```

---

## API Reference

### Autenticazione

| Endpoint | Metodo | Descrizione |
|----------|--------|-------------|
| `/api/auth/register` | POST | Registra nuovo utente |
| `/api/auth/login` | POST | Login (ritorna cookie JWT) |
| `/api/auth/logout` | POST | Logout (cancella cookie) |
| `/api/auth/me` | GET | Dati utente corrente |
| `/api/auth/refresh` | POST | Rinnova access token |

### Sedi

| Endpoint | Metodo | Ruolo | Descrizione |
|----------|--------|-------|-------------|
| `/api/sedi` | GET | * | Lista sedi |
| `/api/sedi` | POST | SuperAdmin | Crea sede |
| `/api/sedi/{id}` | PUT | Admin+ | Modifica sede |
| `/api/sedi/{id}` | DELETE | SuperAdmin | Elimina sede |

### Rimborsi

| Endpoint | Metodo | Ruolo | Descrizione |
|----------|--------|-------|-------------|
| `/api/rimborsi` | GET | Delegato+ | Lista rimborsi |
| `/api/rimborsi` | POST | Delegato+ | Nuova richiesta |
| `/api/rimborsi/{id}` | PUT | Admin | Approva/rifiuta |
| `/api/rimborsi/{id}/ricevute-spese` | POST | * | Upload ricevuta |
| `/api/rimborsi/{id}/contabile` | POST | Admin | Chiudi con bonifico |
| `/api/calcola-km` | POST | * | Calcola KM Google Maps |

### Documenti & Annunci

| Endpoint | Metodo | Ruolo | Descrizione |
|----------|--------|-------|-------------|
| `/api/annunci` | GET | * | Lista annunci |
| `/api/annunci` | POST | Segreteria+ | Pubblica annuncio |
| `/api/documenti` | GET | * | Lista documenti |
| `/api/documenti` | POST | Segreteria+ | Carica documento |
| `/api/documenti/{id}/download` | GET | * | Scarica file |

### Report

| Endpoint | Metodo | Ruolo | Descrizione |
|----------|--------|-------|-------------|
| `/api/reports/rimborsi-annuali?anno=2024` | GET | Admin+ | Report aggregato |
| `/api/reports/rimborsi-export?anno=2024` | GET | Admin+ | Export CSV |

---

## Ruoli e Permessi

| Ruolo | Bacheca | Documenti | Rimborsi | Gestione Rimborsi | Gestione Utenti | Gestione Sedi |
|-------|:-------:|:---------:|:--------:|:-----------------:|:---------------:|:-------------:|
| Iscritto | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Delegato | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| Segreteria | ✅+ | ✅+ | ✅ | ❌ | ❌ | ❌ |
| Segretario | ✅+ | ✅+ | ✅ | ⚠️ | ⚠️ | ❌ |
| Admin | ✅+ | ✅+ | ✅ | ✅ | ✅ | ❌ |
| SuperUser | 👁️ | 👁️ | 👁️ | ❌ | 👁️ | ❌ |
| SuperAdmin | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

- ✅ = Accesso completo
- ✅+ = Può anche creare/modificare
- ⚠️ = Solo propria sede
- 👁️ = Solo visualizzazione

---

## Supporto

Per problemi o domande:
- Apri una issue su GitHub
- Contatta il team di sviluppo

---

**Sviluppato con ❤️ per SLA - Sindacato Lavoratori Autostradali**
