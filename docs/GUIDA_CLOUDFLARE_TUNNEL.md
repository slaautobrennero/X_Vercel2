# 🌐 Guida Completa: Cloudflare Tunnel - Esporre Portale SLA su Internet

## 📋 Cosa Otterrai

Alla fine di questa guida avrai:
- ✅ Portale accessibile da **qualsiasi luogo** via internet
- ✅ URL permanente tipo: `https://portale-sla.tuodominio.com`
- ✅ **HTTPS automatico** (certificato SSL gratuito)
- ✅ **Zero port forwarding** sul router (più sicuro!)
- ✅ **Zero IP pubblico statico** necessario
- ✅ **Protezione DDoS** Cloudflare inclusa
- ✅ **100% GRATUITO**

---

## 🎯 Prerequisiti

- ☑ Raspberry Pi con Portale SLA funzionante
- ☑ Account Cloudflare gratuito (crea su https://cloudflare.com)
- ☑ Un dominio (opzionale ma consigliato)*

**Nota dominio:** Se NON hai un dominio, Cloudflare ti darà un sottodominio gratuito tipo `tuonome.trycloudflare.com`

---

## 🚀 SETUP PASSO-PASSO

### **STEP 1: Crea Account Cloudflare (se non lo hai)**

1. Vai su https://dash.cloudflare.com/sign-up
2. Registrati con email (gratuito)
3. Verifica email
4. Login

✅ Account creato!

---

### **STEP 2: Aggiungi Dominio a Cloudflare (Opzionale)**

**Se hai un dominio:**

1. In Cloudflare Dashboard → **Add a Site**
2. Inserisci il tuo dominio (es: `tuodominio.com`)
3. Scegli piano **Free** → Continue
4. Cloudflare ti darà 2 nameserver tipo:
   ```
   alice.ns.cloudflare.com
   bob.ns.cloudflare.com
   ```
5. Vai dal tuo **registrar** (dove hai comprato il dominio: Aruba, GoDaddy, ecc.)
6. Cambia i nameserver con quelli di Cloudflare
7. Aspetta 5-60 minuti (verifica DNS propagation)

**Se NON hai un dominio:**
- Salta questo step! Cloudflare ti darà un URL temporaneo gratuito

---

### **STEP 3: Installa cloudflared sul Raspberry Pi**

Sul tuo **Raspberry Pi**, esegui:

```bash
# Download cloudflared per ARM64
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64 -o cloudflared

# Sposta in /usr/local/bin
sudo mv cloudflared /usr/local/bin/

# Rendi eseguibile
sudo chmod +x /usr/local/bin/cloudflared

# Verifica installazione
cloudflared --version
```

**Output atteso:**
```
cloudflared version 2024.x.x
```

✅ cloudflared installato!

---

### **STEP 4: Autentica cloudflared con Cloudflare**

```bash
cloudflared tunnel login
```

**Output:**
```
Please open the following URL and log in with your Cloudflare account:

https://dash.cloudflare.com/argotunnel?callback=https%3A%2F%2F...

Leave cloudflared running to download the cert automatically.
```

**Cosa fare:**

1. **Copia l'URL** che appare nel terminale
2. **Aprilo nel browser del tuo PC**
3. Fai login con Cloudflare
4. **Autorizza il dominio** (scegli il dominio dalla lista)*
5. Clicca **Authorize**

*Se non hai dominio, verrà creato automaticamente uno gratuito

**Il terminale mostrerà:**
```
You have successfully logged in.
```

Questo ha creato il file: `~/.cloudflared/cert.pem`

✅ Autenticazione completata!

---

### **STEP 5: Crea il Tunnel**

```bash
# Crea tunnel con nome "portale-sla"
cloudflared tunnel create portale-sla
```

**Output:**
```
Tunnel credentials written to /root/.cloudflared/XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX.json
Created tunnel portale-sla with id XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX
```

**⚠️ IMPORTANTE:** Annota il **Tunnel ID** (le X nell'output sopra)!

Verifica tunnel creato:
```bash
cloudflared tunnel list
```

Dovresti vedere:
```
ID                                   NAME          CREATED
xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx portale-sla   2026-04-19T...
```

✅ Tunnel creato!

---

### **STEP 6: Configura il Tunnel**

Crea file di configurazione:

```bash
mkdir -p ~/.cloudflared
nano ~/.cloudflared/config.yml
```

**Incolla questo contenuto** (sostituisci `TUNNEL_ID` con il tuo ID del Step 5):

```yaml
tunnel: TUNNEL_ID_QUI
credentials-file: /root/.cloudflared/TUNNEL_ID_QUI.json

ingress:
  # Regola 1: Frontend (tutto tranne /api)
  - hostname: portale-sla.tuodominio.com
    service: http://localhost:3000
  
  # Regola 2: Se hai un dominio separato per le API (opzionale)
  # - hostname: api.tuodominio.com
  #   service: http://localhost:8001
  
  # Regola di default (catch-all)
  - service: http_status:404
```

**⚠️ Personalizza:**
- Sostituisci `TUNNEL_ID_QUI` con il tuo Tunnel ID (2 posti!)
- Sostituisci `portale-sla.tuodominio.com` con:
  - Il tuo dominio vero (es: `sla.miositoweb.it`)
  - Oppure un sottodominio Cloudflare gratuito

**Salva:** CTRL+X → Y → INVIO

---

### **STEP 7: Crea DNS Record in Cloudflare**

**Metodo Automatico (Consigliato):**

```bash
# Sostituisci con il tuo dominio e tunnel ID
cloudflared tunnel route dns portale-sla portale-sla.tuodominio.com
```

**Output:**
```
Created CNAME record for portale-sla.tuodominio.com pointing to TUNNEL_ID.cfargotunnel.com
```

**Metodo Manuale** (se automatico fallisce):

1. Vai su Cloudflare Dashboard → Il tuo dominio → **DNS** → **Records**
2. Clicca **Add record**
3. Compila:
   - **Type:** CNAME
   - **Name:** portale-sla (o @ per root domain)
   - **Target:** `TUNNEL_ID.cfargotunnel.com`
   - **Proxy status:** ✅ Proxied (arancione)
4. **Save**

✅ DNS configurato!

---

### **STEP 8: Avvia il Tunnel (Test Manuale)**

```bash
cloudflared tunnel run portale-sla
```

**Output:**
```
2024-04-19T19:00:00Z INF Starting tunnel tunnelID=xxxxxxxx
2024-04-19T19:00:01Z INF Connection registered connIndex=0 ip=xxx.xxx.xxx.xxx
2024-04-19T19:00:01Z INF Connection registered connIndex=1 ip=xxx.xxx.xxx.xxx
...
```

**✅ Se vedi "Connection registered" → FUNZIONA!**

**Test dal browser:**
Vai su `https://portale-sla.tuodominio.com` 

Dovresti vedere la pagina di login del Portale SLA! 🎉

**Ferma il tunnel:** CTRL+C

---

### **STEP 9: Rendi il Tunnel Permanente (Avvio Automatico)**

Crea un **systemd service** per far partire il tunnel automaticamente al boot:

```bash
sudo nano /etc/systemd/system/cloudflared.service
```

**Incolla:**

```ini
[Unit]
Description=Cloudflare Tunnel - Portale SLA
After=network.target

[Service]
Type=simple
User=root
ExecStart=/usr/local/bin/cloudflared tunnel --config /root/.cloudflared/config.yml run portale-sla
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=multi-user.target
```

**Salva:** CTRL+X → Y → INVIO

**Abilita e avvia il service:**

```bash
# Ricarica systemd
sudo systemctl daemon-reload

# Abilita avvio automatico
sudo systemctl enable cloudflared

# Avvia il tunnel
sudo systemctl start cloudflared

# Verifica stato
sudo systemctl status cloudflared
```

**Output atteso:**
```
● cloudflared.service - Cloudflare Tunnel - Portale SLA
   Loaded: loaded (/etc/systemd/system/cloudflared.service; enabled)
   Active: active (running) since ...
```

✅ Se vedi **active (running)** → Tutto ok!

**Comandi utili:**
```bash
# Ferma tunnel
sudo systemctl stop cloudflared

# Riavvia tunnel
sudo systemctl restart cloudflared

# Visualizza log in tempo reale
sudo journalctl -u cloudflared -f
```

---

## ✅ TUNNEL ATTIVO!

Il tuo Portale SLA è ora accessibile da **qualsiasi luogo** via internet!

---

## 🔒 Configurazione Sicurezza (Opzionale ma Consigliata)

### **1. Abilita Cloudflare WAF (Web Application Firewall)**

1. Cloudflare Dashboard → Il tuo dominio → **Security** → **WAF**
2. Attiva **Managed Rules**
3. Imposta sensibilità: **Medium**

### **2. Rate Limiting (Limita Tentativi Login)**

1. Dashboard → **Security** → **WAF** → **Rate limiting rules**
2. **Create rule**:
   - **Nome:** Limit Login Attempts
   - **URL:** `portale-sla.tuodominio.com/api/auth/login`
   - **Requests:** 5 every 1 minute
   - **Action:** Block
3. **Save**

### **3. Accesso Geo-Restrizioni (Solo Italia)**

Se vuoi permettere accesso solo dall'Italia:

1. Dashboard → **Security** → **WAF** → **Firewall rules**
2. **Create rule**:
   - **Nome:** Allow Italy Only
   - **Field:** Country
   - **Operator:** does not equal
   - **Value:** Italy (IT)
   - **Action:** Block
3. **Save**

### **4. Cloudflare Access (Login Extra - Opzionale)**

Aggiungi un ulteriore layer di autenticazione:

1. Dashboard → **Zero Trust** → **Access** → **Applications**
2. **Add an application** → Self-hosted
3. **Application domain:** `portale-sla.tuodominio.com`
4. **Policies:** Scegli chi può accedere (email whitelisting, Google login, ecc.)

---

## 📊 Monitoraggio e Analytics

### **Visualizza Statistiche Tunnel**

```bash
# Log in tempo reale
sudo journalctl -u cloudflared -f

# Log completi
sudo journalctl -u cloudflared --no-pager
```

### **Cloudflare Analytics**

1. Dashboard → Il tuo dominio → **Analytics & Logs**
2. Visualizza:
   - Requests (richieste totali)
   - Bandwidth (traffico)
   - Threats blocked (minacce bloccate)
   - Geographic distribution (da dove accedono)

---

## 🌍 Test Accesso da Internet

### **Dal tuo smartphone (dati mobili, NON WiFi):**

1. Disattiva WiFi
2. Apri browser
3. Vai su `https://portale-sla.tuodominio.com`
4. Dovresti vedere la pagina di login!

### **Condividi con amici per test:**

Dai l'URL ad amici/colleghi e chiedi di provare ad accedere. Se vedono la pagina di login → FUNZIONA! 🎉

---

## 🆘 Troubleshooting

### "Error 502 Bad Gateway"

**Causa:** Il tunnel non riesce a raggiungere il frontend

**Fix:**
```bash
# Verifica che il frontend sia UP
docker compose -f /opt/portale-sla/docker/docker-compose.yml ps

# Verifica tunnel attivo
sudo systemctl status cloudflared

# Controlla log
sudo journalctl -u cloudflared -n 50
```

### "Error 1033: Argo Tunnel error"

**Causa:** Tunnel ID o credentials errati

**Fix:**
```bash
# Verifica config.yml
cat ~/.cloudflared/config.yml

# Ricontrolla Tunnel ID
cloudflared tunnel list
```

### "DNS_PROBE_FINISHED_NXDOMAIN"

**Causa:** DNS non propagato ancora

**Fix:**
- Aspetta 5-60 minuti
- Verifica DNS: https://dnschecker.org (inserisci il tuo dominio)

### Tunnel si disconnette spesso

**Causa:** Connessione internet instabile

**Fix:**
```bash
# Modifica service per restart più aggressivo
sudo nano /etc/systemd/system/cloudflared.service

# Cambia:
RestartSec=5s
# In:
RestartSec=10s

# E aggiungi:
StartLimitInterval=0

# Reload
sudo systemctl daemon-reload
sudo systemctl restart cloudflared
```

---

## 📚 Comandi Utili Riassunti

```bash
# Stato tunnel
sudo systemctl status cloudflared

# Log real-time
sudo journalctl -u cloudflared -f

# Riavvia tunnel
sudo systemctl restart cloudflared

# Lista tunnel
cloudflared tunnel list

# Info tunnel
cloudflared tunnel info portale-sla

# Test config
cloudflared tunnel --config ~/.cloudflared/config.yml ingress validate

# Elimina tunnel (ATTENZIONE!)
cloudflared tunnel delete portale-sla
```

---

## 🎉 Configurazione Completata!

Ora il tuo Portale SLA è:
- ✅ Accessibile da internet
- ✅ Protetto HTTPS
- ✅ Protetto da Cloudflare (DDoS protection)
- ✅ Avvio automatico al boot
- ✅ Sempre online

**URL Pubblico:** `https://portale-sla.tuodominio.com`

---

## 📖 Documentazione Cloudflare Ufficiale

- Cloudflare Tunnel: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/
- Zero Trust: https://developers.cloudflare.com/cloudflare-one/
- Community: https://community.cloudflare.com/

---

**Prossimo step:** [Configurazione PWA (App Mobile)](./GUIDA_PWA_MOBILE.md)
