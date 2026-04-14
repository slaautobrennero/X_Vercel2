# 🐳 GUIDA DEPLOYMENT DOCKER - Portale SLA

## 📋 Indice
1. [Opzione A: Docker Locale (Raspberry Pi / PC)](#opzione-a-docker-locale)
2. [Opzione B: Docker Online (DigitalOcean / VPS)](#opzione-b-docker-online)
3. [Configurazione Variabili d'Ambiente](#configurazione-variabili)
4. [Comandi Utili](#comandi-utili)
5. [Troubleshooting](#troubleshooting)

---

## 🏠 OPZIONE A: Docker Locale (Raspberry Pi / PC)

### **Requisiti:**
- Raspberry Pi 4 (4GB+ RAM) o PC Linux/Windows/Mac
- Docker e Docker Compose installati
- Connessione internet

### **STEP 1: Installa Docker**

#### **Su Raspberry Pi (DietPi/Raspbian):**
```bash
# Installa Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Aggiungi utente al gruppo docker
sudo usermod -aG docker $USER

# Installa Docker Compose
sudo apt-get update
sudo apt-get install -y docker-compose

# Verifica installazione
docker --version
docker-compose --version
```

#### **Su Windows:**
1. Scarica **Docker Desktop** da https://www.docker.com/products/docker-desktop/
2. Installa e riavvia
3. Verifica: `docker --version`

#### **Su Mac:**
1. Scarica **Docker Desktop** da https://www.docker.com/products/docker-desktop/
2. Installa
3. Verifica: `docker --version`

---

### **STEP 2: Prepara il Codice**

```bash
# Scarica il codice (usa "Download Code" su Emergent o git clone)
cd /percorso/dove/hai/scaricato/portale-sla

# Entra nella directory docker
cd docker

# Crea file .env da template
cp .env.example .env

# Modifica .env con le tue credenziali
nano .env  # oppure usa un editor di testo
```

---

### **STEP 3: Configura Variabili d'Ambiente**

Modifica `/docker/.env`:

```env
# JWT Secret - OBBLIGATORIO CAMBIARE!
JWT_SECRET=la_tua_password_sicura_lunga_almeno_32_caratteri

# Google Maps (opzionale, lascia vuoto se non hai)
GOOGLE_MAPS_API_KEY=

# URLs (per locale, lascia così)
FRONTEND_URL=http://localhost:3000
REACT_APP_BACKEND_URL=http://localhost:8001
```

**Genera JWT Secret sicuro:**
```bash
openssl rand -base64 32
# Copia il risultato in JWT_SECRET
```

---

### **STEP 4: Avvia l'Applicazione**

```bash
cd /percorso/portale-sla/docker

# Prima volta: build e avvio
docker-compose up -d --build

# Questo comando:
# 1. Scarica le immagini necessarie
# 2. Fa il build del frontend e backend
# 3. Avvia MongoDB, Backend, Frontend
# Tempo: 5-10 minuti prima volta
```

---

### **STEP 5: Verifica Funzionamento**

```bash
# Controlla che tutti i container siano running
docker-compose ps

# Dovresti vedere:
# sla-mongodb   Running   0.0.0.0:27017->27017/tcp
# sla-backend   Running   0.0.0.0:8001->8001/tcp
# sla-frontend  Running   0.0.0.0:3000->80/tcp

# Vedi i log
docker-compose logs -f

# Testa l'app
# Apri browser: http://localhost:3000
```

---

### **STEP 6: Accesso da Esterno (IP Pubblico)**

Per rendere accessibile l'app da internet:

#### **Opzione 1: Port Forwarding sul Router**
1. Accedi al tuo router (es: 192.168.1.1)
2. Configura port forwarding:
   - Porta esterna: 80 → Porta interna: 3000 (IP del Raspberry)
   - Porta esterna: 8001 → Porta interna: 8001
3. Trova il tuo IP pubblico: https://www.whatismyip.com/
4. Accedi con: `http://TUO_IP_PUBBLICO`

⚠️ **Problema IP dinamico:** L'IP pubblico cambia.

#### **Opzione 2: DynDNS (IP dinamico → dominio fisso)**
Servizi gratuiti:
- **No-IP**: https://www.noip.com/
- **DuckDNS**: https://www.duckdns.org/

1. Registrati e crea un hostname (es: `miosindacato.ddns.net`)
2. Installa client DynDNS sul Raspberry
3. Accedi con: `http://miosindacato.ddns.net`

---

## ☁️ OPZIONE B: Docker Online (DigitalOcean / VPS)

### **Vantaggi:**
- ✅ IP fisso
- ✅ Sempre online 24/7
- ✅ Backup automatici
- ✅ Nessuna configurazione router

### **Costo:** ~€6-12/mese

---

### **STEP 1: Crea VPS su DigitalOcean**

1. Vai su https://www.digitalocean.com/
2. **Crea account** (€200 crediti gratis primi 60 giorni con codice promo)
3. Click su **"Create" → "Droplets"**
4. Scegli:
   - **Distribution**: Ubuntu 22.04 LTS
   - **Plan**: Basic ($6/mese - 1GB RAM)
   - **Datacenter**: Frankfurt (più vicino all'Italia)
5. **Authentication**: Password (crea password sicura)
6. Click **"Create Droplet"**

---

### **STEP 2: Connetti al Server**

```bash
# Da terminale locale (sostituisci IP_DEL_SERVER)
ssh root@IP_DEL_SERVER

# Inserisci password quando richiesto
```

---

### **STEP 3: Installa Docker sul Server**

```bash
# Aggiorna sistema
apt update && apt upgrade -y

# Installa Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Installa Docker Compose
apt install -y docker-compose

# Verifica
docker --version
docker-compose --version
```

---

### **STEP 4: Carica il Codice**

#### **Opzione 1: Git Clone**
```bash
# Installa Git
apt install -y git

# Clona repository (sostituisci con il tuo repo pubblico)
git clone https://github.com/TUO_USERNAME/x_vercel2.git /opt/portale-sla
cd /opt/portale-sla/docker
```

#### **Opzione 2: SCP (copia manuale)**
```bash
# Dal tuo PC locale
scp -r /percorso/portale-sla root@IP_SERVER:/opt/portale-sla
```

---

### **STEP 5: Configura e Avvia**

```bash
cd /opt/portale-sla/docker

# Crea .env
cp .env.example .env
nano .env

# Modifica variabili (vedi sopra)
# Salva: Ctrl+O, Invio, Ctrl+X

# Avvia
docker-compose up -d --build

# Verifica
docker-compose ps
docker-compose logs -f
```

---

### **STEP 6: Accedi all'App**

Apri browser: `http://IP_DEL_SERVER:3000`

---

## 🔧 Configurazione Variabili d'Ambiente

File: `/docker/.env`

```env
# JWT Secret - Cambia in produzione!
JWT_SECRET=genera_con_openssl_rand_base64_32

# Google Maps (opzionale)
GOOGLE_MAPS_API_KEY=la_tua_chiave_google

# Frontend URL (per CORS backend)
# Locale: http://localhost:3000
# Online: http://IP_SERVER:3000 o http://tuodominio.it
FRONTEND_URL=http://localhost:3000

# Backend URL (per frontend)
# Locale: http://localhost:8001
# Online: http://IP_SERVER:8001 o http://api.tuodominio.it
REACT_APP_BACKEND_URL=http://localhost:8001
```

---

## 📝 Comandi Utili

### **Gestione Container**

```bash
# Avvia tutti i servizi
docker-compose up -d

# Ferma tutti i servizi
docker-compose down

# Riavvia servizio specifico
docker-compose restart backend
docker-compose restart frontend

# Ricostrui dopo modifiche codice
docker-compose up -d --build

# Vedi log in tempo reale
docker-compose logs -f

# Vedi log singolo servizio
docker-compose logs -f backend
docker-compose logs -f frontend

# Stato container
docker-compose ps

# Accedi dentro container
docker exec -it sla-backend bash
docker exec -it sla-frontend sh
```

### **Database MongoDB**

```bash
# Accedi a MongoDB
docker exec -it sla-mongodb mongosh

# Backup database
docker exec sla-mongodb mongodump --out /backup
docker cp sla-mongodb:/backup ./backup-$(date +%Y%m%d)

# Restore database
docker cp ./backup sla-mongodb:/backup
docker exec sla-mongodb mongorestore /backup
```

### **Pulizia**

```bash
# Rimuovi container fermi
docker-compose down

# Rimuovi anche i volumi (ATTENZIONE: cancella dati!)
docker-compose down -v

# Pulizia immagini inutilizzate
docker system prune -a
```

---

## 🔥 Troubleshooting

### **Container non si avvia**

```bash
# Vedi errori specifici
docker-compose logs backend
docker-compose logs frontend

# Controlla porta già in uso
sudo lsof -i :3000
sudo lsof -i :8001
sudo lsof -i :27017

# Ferma e riavvia tutto
docker-compose down
docker-compose up -d --build
```

### **Frontend non carica**

```bash
# Ricostrui frontend
docker-compose up -d --build frontend

# Vedi log Nginx
docker-compose logs frontend
```

### **Backend errore database**

```bash
# Controlla MongoDB running
docker-compose ps

# Vedi log MongoDB
docker-compose logs mongodb

# Riavvia MongoDB
docker-compose restart mongodb
```

### **Modifiche codice non applicate**

```bash
# SEMPRE ricostruire dopo modifiche
docker-compose down
docker-compose up -d --build

# Forza rebuild senza cache
docker-compose build --no-cache
docker-compose up -d
```

---

## 🎯 Checklist Deployment

### **Prima di avviare:**
- [ ] Docker e Docker Compose installati
- [ ] File `.env` configurato con JWT_SECRET
- [ ] Porte 3000, 8001, 27017 libere

### **Dopo avvio:**
- [ ] Tutti container running (`docker-compose ps`)
- [ ] Nessun errore nei log (`docker-compose logs`)
- [ ] App accessibile su `http://localhost:3000`
- [ ] Login funziona con credenziali test

### **Per produzione:**
- [ ] JWT_SECRET cambiato (non default)
- [ ] Firewall configurato
- [ ] Backup automatici database configurati
- [ ] Dominio configurato (opzionale)
- [ ] HTTPS configurato (opzionale, con Caddy o Nginx Proxy)

---

## 📞 Supporto

**Log utili per debug:**
- Frontend build: `docker-compose logs frontend`
- Backend startup: `docker-compose logs backend`
- MongoDB: `docker-compose logs mongodb`

**File di configurazione:**
- `/docker/docker-compose.yml` - Orchestrazione servizi
- `/docker/backend.Dockerfile` - Build backend
- `/docker/frontend.Dockerfile` - Build frontend
- `/docker/nginx.conf` - Configurazione web server

---

**Buon deployment! 🚀**
