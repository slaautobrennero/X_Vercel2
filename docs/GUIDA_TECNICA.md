# Guida tecnica unica - Portale SLA (Raspberry Pi)

Unico riferimento per installare, aggiornare, proteggere e ripristinare il portale.
Le guide d'uso per gli utenti (Iscritto, Delegato, Segreteria, ecc.) sono dentro il portale, alla voce **Guida**.

| Cosa | Dove |
|---|---|
| Progetto sul Pi | `/opt/portale-sla/` |
| Docker Compose | `/opt/portale-sla/docker/` |
| Configurazione (segreti) | `/opt/portale-sla/docker/.env` (mai su GitHub) |
| Backup | `/opt/portale-sla/backups/` + Google Drive |
| Script | `/opt/portale-sla/scripts/` |

Architettura: 3 container (`sla-mongodb`, `sla-backend`, `sla-frontend`) su rete Docker interna.
Internet → Cloudflare Tunnel (HTTPS) → frontend Nginx (porta 3000) → backend (`127.0.0.1:8001`, non raggiungibile dalla rete di casa).
Il database (porta 27017) non è esposto e richiede password. I file caricati (ricevute, documenti) sono salvati dentro MongoDB (GridFS), quindi il backup del database li include.

---

## 1. Aggiornamento (uso quotidiano)

1. Su Emergent: **Save to GitHub**.
2. Sul Pi:
   ```bash
   sla-update
   ```
3. Controlla che la versione mostrata (in basso a destra nel portale e nell'output) sia quella nuova.

Se `sla-update` non esiste ancora, aggiungi una volta sola questi alias a `~/.bashrc` e poi esegui `source ~/.bashrc`:
```bash
alias sla-pull='cd /opt/portale-sla && git stash && git pull origin main'
alias sla-rebuild='cd /opt/portale-sla/docker && docker compose down && docker rm -f sla-frontend sla-backend 2>/dev/null; docker image rm -f docker-frontend docker-backend 2>/dev/null; docker compose build --no-cache --pull frontend backend && docker compose up -d'
alias sla-status='cd /opt/portale-sla/docker && docker compose ps && echo "---" && curl -s http://localhost:8001/api/version'
alias sla-logs='cd /opt/portale-sla/docker && docker compose logs -f'
alias sla-update='sla-pull && sla-rebuild && sleep 30 && sla-status'
```

Se dopo l'aggiornamento la versione è ancora vecchia (cache Docker):
```bash
cd /opt/portale-sla/docker && docker builder prune -af && sla-rebuild
```

### Dopo aver modificato `docker/.env`
`docker compose restart` **non** rilegge le variabili. Usa:
```bash
cd /opt/portale-sla/docker
sudo docker compose up -d --force-recreate backend
```
Se hai cambiato `REACT_APP_BACKEND_URL` o `REACT_APP_HCAPTCHA_SITE_KEY` serve ricostruire il frontend: `sla-rebuild`.

---

## 2. Prima installazione (nuovo Pi o nuovo server)

Requisiti: Raspberry Pi 4 (64 bit, `uname -m` = `aarch64`), 4 GB RAM consigliati, 8 GB liberi.

```bash
# Docker
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER && sudo reboot

# Codice
cd /opt && git clone https://github.com/slaautobrennero/x_vercel2.git portale-sla
cd /opt/portale-sla/docker && cp .env.example .env && nano .env
```

Valori da compilare in `docker/.env`:

| Variabile | Obbligatoria | Note |
|---|---|---|
| `MONGO_ROOT_PASSWORD` | Sì | `openssl rand -base64 24`. Impostata al primo avvio: non cambiarla dopo |
| `JWT_SECRET` | Sì | `openssl rand -hex 32`. Se la cambi: tutti vengono disconnessi e le password SMTP salvate vanno reinserite |
| `ADMIN_EMAIL` / `ADMIN_PASSWORD` | Sì | SuperAdmin creato solo al primo avvio. Cambia la password al primo accesso |
| `FRONTEND_URL` | Sì | Indirizzo pubblico, es. `https://www.portale-sla.it` (usato nei link delle email) |
| `REACT_APP_BACKEND_URL` | Sì | Stesso indirizzo pubblico |
| `GOOGLE_MAPS_API_KEY` | No | Calcolo automatico dei km |
| `HCAPTCHA_SECRET` / `REACT_APP_HCAPTCHA_SITE_KEY` | Consigliata | Anti-bot sulla registrazione (gratuito su hcaptcha.com) |
| `EMERGENT_EMAIL_KEY` | No | Solo per le sedi che scelgono il servizio email gestito |

Avvio (10-15 minuti la prima volta):
```bash
docker compose up -d --build
docker compose ps        # i 3 container devono risultare "Up"
```
Poi configura Cloudflare Tunnel (sez. 3), i backup (sez. 4) e gli alias (sez. 1).

Se la build va in "out of memory": aumenta lo swap a 2048 MB (`/etc/dphys-swapfile`, `CONF_SWAPSIZE=2048`, poi `sudo dphys-swapfile setup && sudo dphys-swapfile swapon`).

---

## 3. Accesso da Internet: Cloudflare Tunnel

```bash
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64 -o cloudflared
sudo mv cloudflared /usr/local/bin/ && sudo chmod +x /usr/local/bin/cloudflared
cloudflared tunnel login                 # apri il link dal PC e autorizza il dominio
cloudflared tunnel create portale-sla    # annota il TUNNEL_ID
cloudflared tunnel route dns portale-sla www.portale-sla.it
```

`~/.cloudflared/config.yml`:
```yaml
tunnel: TUNNEL_ID
credentials-file: /root/.cloudflared/TUNNEL_ID.json
ingress:
  - hostname: www.portale-sla.it
    service: http://localhost:3000
  - service: http_status:404
```

Avvio automatico al boot (`/etc/systemd/system/cloudflared.service`):
```ini
[Unit]
Description=Cloudflare Tunnel - Portale SLA
After=network.target

[Service]
ExecStart=/usr/local/bin/cloudflared tunnel --config /root/.cloudflared/config.yml run portale-sla
Restart=always
RestartSec=5s

[Install]
WantedBy=multi-user.target
```
```bash
sudo systemctl daemon-reload && sudo systemctl enable --now cloudflared
sudo journalctl -u cloudflared -f      # log
```

Non serve aprire porte sul router. Errore 502 = il frontend non risponde: `sla-status`.

---

## 4. Backup cifrati e ripristino

### Preparazione (una volta)
```bash
# Password di cifratura: conservala anche fuori dal Pi. Se la perdi, i backup sono illeggibili.
echo "PASSWORD_LUNGA_E_SEGRETA" > /opt/portale-sla/.backup_password
chmod 600 /opt/portale-sla/.backup_password
chmod +x /opt/portale-sla/scripts/*.sh

# Google Drive (copia esterna)
sudo apt install rclone -y
rclone config            # nuovo remote chiamato "gdrive", tipo "drive", auto config = n, autorizza dal PC
rclone mkdir gdrive:Portale-SLA-Backups
```

### Automazione (`crontab -e`)
```cron
0 3 * * *  /opt/portale-sla/scripts/backup_mongodb.sh >> /var/log/sla-backup-db.log 2>&1
15 3 * * * /opt/portale-sla/scripts/backup_uploads.sh >> /var/log/sla-backup-uploads.log 2>&1
0 2 * * 0  /opt/portale-sla/scripts/cleanup_docker.sh >> /var/log/sla-cleanup.log 2>&1
```
I backup restano 14 giorni sul Pi e vengono copiati su Google Drive (`Portale-SLA-Backups`).
Il backup del database contiene anche tutti i file allegati. `backup_uploads.sh` copia in più la cache locale dei file.

### Ripristino (provalo almeno una volta prima del go-live)
```bash
ls -lh /opt/portale-sla/backups/db/
/opt/portale-sla/scripts/restore_mongodb.sh /opt/portale-sla/backups/db/db_DATA.tar.gz.enc   # chiede conferma "SI"
```

### Disastro completo (Pi rotto)
1. Nuovo Pi → sezione 2 con lo **stesso** `docker/.env` (tienine una copia sicura fuori dal Pi).
2. Scarica l'ultimo `db_*.tar.gz.enc` da Google Drive e lancia `restore_mongodb.sh`.

---

## 5. Accesso remoto via SSH (Tailscale)

```bash
sudo bash /opt/portale-sla/scripts/setup_tailscale.sh
```
Apri il link mostrato e accedi. Poi da qualunque rete: `ssh root@100.x.y.z` (IP Tailscale del Pi).

---

## 6. Notifiche ed email

- **Notifiche sul telefono (gratuite)**: ogni utente va su Profilo → "Notifiche sul telefono" → Attiva e accetta il permesso. Su iPhone bisogna prima aggiungere il portale alla schermata Home (Safari → Condividi → Aggiungi a Home). Non serve nessuna chiave: il portale le genera da solo.
- **Email**: ogni sede sceglie dal proprio pannello (Admin della sede o SuperAdmin):
  - **Nessuna email** (predefinito, costo zero)
  - **Gmail o casella del dominio** (SMTP). Per Gmail serve una "password per le app" (account Google → Sicurezza → Verifica in due passaggi → Password per le app); host `smtp.gmail.com`, porta 587
  - **Servizio gestito**: solo se `EMERGENT_EMAIL_KEY` è impostata
  Usa "Invia email di prova" dopo aver salvato.

---

## 7. Problemi comuni

| Sintomo | Soluzione |
|---|---|
| `no configuration file provided` | Non sei in `/opt/portale-sla/docker` |
| `git pull` in conflitto | `git stash` e riprova (lo fa già `sla-pull`) |
| Versione ancora vecchia | `docker builder prune -af` e poi `sla-rebuild` |
| Backend si riavvia di continuo | `docker compose logs backend`: di solito manca una variabile obbligatoria in `.env` |
| Nuova variabile `.env` ignorata | `sudo docker compose up -d --force-recreate backend` |
| Errore 502 dal sito | Container fermi (`sla-status`) o tunnel fermo (`systemctl status cloudflared`) |
| Avvisi rossi nel pannello SuperAdmin | Configurazioni di sicurezza mancanti (es. hCaptcha): seguire il testo dell'avviso |

Comandi utili: `sla-status`, `sla-logs`, `docker system df` (spazio usato).

---

## 8. Checklist go-live

- [ ] Password SuperAdmin cambiata
- [ ] PEC/email reali in Impostazioni Sindacato
- [ ] hCaptcha configurato
- [ ] Backup automatici attivi e **ripristino provato**
- [ ] Copia di `docker/.env` e della password backup conservata fuori dal Pi
- [ ] Utenti di prova eliminati
- [ ] Privacy e Termini rivisti da un legale

## 9. Spostamento su VPS/server

Stessa procedura della sezione 2 su un server Ubuntu con Docker, poi ripristino dell'ultimo backup (sezione 4) e spostamento del tunnel Cloudflare (o DNS) sul nuovo server.
