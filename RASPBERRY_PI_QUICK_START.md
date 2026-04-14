# 🥧 SETUP RAPIDO RASPBERRY PI - Portale SLA

## ✅ PREREQUISITI VERIFICATI

Prima di iniziare, verifica:

```bash
# 1. Architettura (importante per MongoDB!)
uname -m
# Se vedi "aarch64" = 64-bit ✅ (OK mongo:6.0)
# Se vedi "armv7l" = 32-bit ⚠️ (usa mongo:4.4)

# 2. Spazio disco (minimo 8GB liberi)
df -h

# 3. RAM (minimo 2GB, consigliato 4GB+)
free -h
```

---

## 📝 STEP 1: Installa DietPi con Balena Etcher

**Hai già fatto:**
1. ✅ Scarica DietPi da https://dietpi.com/#download
2. ✅ Flasha su microSD con Balena Etcher
3. ✅ Inserisci microSD in Raspberry Pi
4. ✅ Accendi Raspberry Pi

**Primo avvio:**
- Login: `root` / Password: `dietpi`
- Segui wizard configurazione DietPi
- Connetti Wi-Fi o Ethernet
- Aspetta aggiornamenti sistema

---

## 🐳 STEP 2: Installa Docker (5 minuti)

```bash
# Opzione A: Installer automatico DietPi (CONSIGLIATO)
sudo dietpi-software

# Nel menu:
# - Vai su "Browse Software"
# - Cerca "Docker" (ID 162)
# - Seleziona con SPAZIO
# - Cerca "Docker Compose" (ID 134)
# - Seleziona con SPAZIO
# - TAB per andare su "Install"
# - Conferma

# Opzione B: Script ufficiale Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo apt-get install -y docker-compose

# Aggiungi utente corrente a gruppo docker
sudo usermod -aG docker $USER

# RIAVVIA per applicare permessi
sudo reboot
```

Dopo riavvio, verifica:
```bash
docker --version
docker-compose --version
```

---

## 📥 STEP 3: Scarica Codice Portale SLA

### **Opzione A: Da Emergent (CONSIGLIATO)**
1. Vai su Emergent
2. Click **"Download Code"** (scarica .zip)
3. Trasferisci su Raspberry Pi:

```bash
# Dal tuo PC (sostituisci IP_RASPBERRY)
scp portale-sla.zip root@IP_RASPBERRY:/opt/

# Sul Raspberry Pi
cd /opt
unzip portale-sla.zip
cd portale-sla
```

### **Opzione B: Da GitHub**
```bash
# Solo se hai reso pubblico il repository
cd /opt
git clone https://github.com/slaautobrennero/x_vercel2.git portale-sla
cd portale-sla
```

---

## ⚙️ STEP 4: Configura Variabili d'Ambiente

```bash
cd /opt/portale-sla/docker

# Crea file .env da template
cp .env.example .env

# Modifica con nano o vi
nano .env
```

**Modifica questi valori:**

```env
# JWT Secret - OBBLIGATORIO CAMBIARE!
# Genera con: openssl rand -base64 32
JWT_SECRET=INCOLLA_QUI_LA_CHIAVE_GENERATA

# Google Maps (opzionale, lascia vuoto se non hai)
GOOGLE_MAPS_API_KEY=

# URLs (per accesso locale)
FRONTEND_URL=http://localhost:3000
REACT_APP_BACKEND_URL=http://localhost:8001
```

**Genera JWT Secret:**
```bash
openssl rand -base64 32
# Copia il risultato nel file .env
```

Salva: `Ctrl+O`, `Invio`, `Ctrl+X`

---

## 🔍 STEP 5: Verifica Architettura e MongoDB

```bash
# Controlla architettura
uname -m

# Se "armv7l" (32-bit), modifica docker-compose.yml:
nano docker-compose.yml

# Cerca la riga:
#   image: mongo:6.0
# Cambia in:
#   image: mongo:4.4

# Salva e esci
```

---

## 🚀 STEP 6: Avvia Applicazione

```bash
cd /opt/portale-sla/docker

# Prima volta: build + avvio (10-15 minuti)
docker-compose up -d --build

# Questo comando:
# 1. Scarica immagini base (Node, Python, Nginx, MongoDB)
# 2. Fa build del backend (installa dipendenze Python)
# 3. Fa build del frontend (installa dipendenze Node + build React)
# 4. Avvia tutti i container

# ⏰ Aspetta pazientemente (può servire 10-15 min su Raspberry Pi)
```

---

## ✅ STEP 7: Verifica Funzionamento

```bash
# Controlla status container
docker-compose ps

# Dovresti vedere 3 container in stato "Up":
# sla-mongodb    Up    0.0.0.0:27017->27017/tcp
# sla-backend    Up    0.0.0.0:8001->8001/tcp
# sla-frontend   Up    0.0.0.0:3000->80/tcp

# Se non sono tutti "Up", vedi i log:
docker-compose logs -f

# Testa backend
curl http://localhost:8001/docs
# Dovresti vedere documentazione API

# Testa frontend - Apri browser su Raspberry Pi o altro PC:
# http://IP_RASPBERRY:3000
```

---

## 🌐 STEP 8: Accesso da Altri Dispositivi (Opzionale)

### **Trova IP Raspberry Pi:**
```bash
hostname -I
# Es: 192.168.1.100
```

### **Accedi da PC/smartphone sulla stessa rete:**
```
http://192.168.1.100:3000
```

### **Accesso da INTERNET (port forwarding router):**
1. Accedi al router (es: 192.168.1.1)
2. Port Forwarding:
   - Porta esterna: 80 → IP Raspberry: 192.168.1.100, Porta 3000
3. Trova IP pubblico: https://www.whatismyip.com/
4. Accedi: `http://TUO_IP_PUBBLICO`

⚠️ **Problema IP dinamico:** Usa DynDNS (No-IP, DuckDNS) per avere dominio fisso.

---

## 🔄 COMANDI UTILI

```bash
# Vedi log in tempo reale
docker-compose logs -f

# Log singolo servizio
docker-compose logs -f backend
docker-compose logs -f frontend

# Riavvia tutto
docker-compose restart

# Ferma tutto
docker-compose down

# Riavvia dopo modifiche codice
docker-compose down
docker-compose up -d --build

# Backup database
docker exec sla-mongodb mongodump --out /backup
docker cp sla-mongodb:/backup ./backup-$(date +%Y%m%d)

# Spazio disco usato da Docker
docker system df
```

---

## 🔥 TROUBLESHOOTING

### **Container non si avvia**
```bash
# Vedi errori specifici
docker-compose logs backend
docker-compose logs frontend
docker-compose logs mongodb

# Ricostrui da zero
docker-compose down
docker-compose up -d --build --force-recreate
```

### **"Out of memory" durante build**
```bash
# Aumenta swap (solo prima volta)
sudo dphys-swapfile swapoff
sudo nano /etc/dphys-swapfile
# Cambia CONF_SWAPSIZE=2048
sudo dphys-swapfile setup
sudo dphys-swapfile swapon

# Poi riprova build
docker-compose up -d --build
```

### **MongoDB non supporta architettura**
```bash
# Errore tipo "exec format error"
# Cambia mongo:6.0 → mongo:4.4 in docker-compose.yml
nano docker-compose.yml
# Cerca: image: mongo:6.0
# Cambia: image: mongo:4.4
docker-compose down
docker-compose up -d
```

### **Frontend build fallisce (date-fns error)**
```bash
# Già fixato con --legacy-peer-deps
# Ma se vedi ancora errori:
docker-compose logs frontend

# Ricostrui solo frontend
docker-compose up -d --build frontend
```

---

## 📊 PERFORMANCE ATTESE

**Raspberry Pi 4 (4GB RAM):**
- Build iniziale: 10-15 minuti
- Avvio successivi: 30-60 secondi
- Utilizzo RAM: ~1.5-2GB
- Utilizzo CPU idle: 5-10%
- Utilizzo CPU attivo: 30-50%

**Raspberry Pi 3:**
- Build iniziale: 20-30 minuti
- Può andare out of memory (aumenta swap)
- Funziona ma lento

---

## ✅ CHECKLIST POST-INSTALLAZIONE

- [ ] Tutti container in stato "Up"
- [ ] Frontend accessibile http://IP:3000
- [ ] Backend docs http://IP:8001/docs
- [ ] Login funziona con credenziali test
- [ ] Backup database configurato (opzionale)
- [ ] Firewall configurato (opzionale)
- [ ] DynDNS configurato per accesso esterno (opzionale)

---

## 🎯 CREDENZIALI TEST

Dopo primo avvio, crea utente SuperAdmin da MongoDB:
```bash
docker exec -it sla-mongodb mongosh

use sla_sindacato
db.users.insertOne({
  email: "admin@sla.it",
  password_hash: "$2b$12$...", // genera con bcrypt
  nome: "Admin",
  cognome: "Sistema",
  ruolo: "superadmin",
  created_at: new Date()
})
```

Oppure registrati dal frontend come primo utente e modifica ruolo da MongoDB.

---

**Setup completato! App online su Raspberry Pi! 🥧🚀**

Per dubbi, vedi `/app/DOCKER_DEPLOYMENT_GUIDE.md` (guida completa).
