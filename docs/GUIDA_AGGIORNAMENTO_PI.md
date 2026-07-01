# 🔄 Guida Aggiornamento Portale SLA sul Raspberry Pi

Procedura passo-passo per aggiornare il portale SLA installato sul Raspberry Pi 4 partendo dalle modifiche fatte nell'ambiente Emergent (o su GitHub).

> **Path del progetto sul Pi:** `/opt/portale-sla/`
> **Path Docker Compose:** `/opt/portale-sla/docker/`
> **Repo GitHub:** `https://github.com/slaautobrennero/x_vercel2`

---

## 📋 Riepilogo veloce (per chi ha fretta)

```bash
# 1. In Emergent: click "Save to GitHub" (in alto a destra)

# 2. Sul Pi:
cd /opt/portale-sla && git stash && git pull origin main

# 3. Rebuild Docker:
cd /opt/portale-sla/docker && \
docker compose down && \
docker rm -f sla-frontend sla-backend 2>/dev/null; \
docker image rm -f docker-frontend docker-backend 2>/dev/null; \
docker compose build --no-cache --pull frontend backend && \
docker compose up -d && \
sleep 30 && \
docker compose ps && \
curl -s http://localhost:8001/api/version
```

---

## 🎯 Procedura dettagliata

### FASE 1 — Su Emergent (dal browser)

1. Verifica che tutte le modifiche siano salvate nell'editor.
2. Clicca il pulsante **"Save to GitHub"** (in alto a destra della chat).
3. Attendi il messaggio di conferma push riuscito.
4. In alternativa, chiedi all'agente di verificare che l'ultimo commit contenga le modifiche desiderate.

> 💡 Se non fai questo passaggio, il `git pull` sul Pi non troverà le novità.

---

### FASE 2 — Sul Raspberry Pi (via SSH/terminale)

#### 2.1 Vai nella cartella del progetto (SEMPRE)

```bash
cd /opt/portale-sla
```

> ⚠️ **Errore più comune**: dimenticarsi il `cd` e lanciare `docker compose ...` dalla home. Restituisce `no configuration file provided: not found`.

#### 2.2 Stash delle modifiche locali (se ce ne sono)

Se hai modificato file direttamente sul Pi (tipicamente script in `scripts/`), salvali prima del pull:

```bash
git status                # Vedi cosa è modificato
git stash                 # Metti da parte
```

#### 2.3 Pull dal repo GitHub

```bash
git pull origin main
git log --oneline -3      # Verifica di vedere il commit atteso
```

Output atteso: dovresti vedere righe `Fast-forward` seguite dai file modificati.

#### 2.4 (Opzionale) Ripristina le modifiche locali stashate

```bash
git stash pop             # Solo se avevi fatto stash e vuoi ri-applicare
```

Se ci sono conflitti, risolvili manualmente o abbandona lo stash con `git stash drop`.

#### 2.5 Verifica che i file siano aggiornati

Controlla la versione nel codice sorgente:

```bash
grep "APP_VERSION" backend/routes/public.py
grep "APP_VERSION" frontend/src/version.js
```

Devono mostrare la stessa versione (es. `0.10.1-beta`).

---

### FASE 3 — Rebuild dei container Docker

Vai nella cartella docker:

```bash
cd /opt/portale-sla/docker
```

Poi scegli il livello di rebuild in base a quanto sei stato aggressivo prima:

#### 🟢 Livello 1 — Standard (per la maggior parte degli update)

```bash
docker compose down
docker compose build --no-cache frontend backend
docker compose up -d
```

#### 🟡 Livello 2 — Se la versione dopo il build risulta ancora vecchia

```bash
docker compose down
docker rm -f sla-frontend sla-backend 2>/dev/null
docker image rm -f docker-frontend docker-backend 2>/dev/null
docker compose build --no-cache --pull frontend backend
docker compose up -d
```

#### 🔴 Livello 3 — "Nuclear option" (se neanche il livello 2 funziona)

```bash
docker compose down
docker rm -f sla-frontend sla-backend 2>/dev/null
docker image rm -f docker-frontend docker-backend 2>/dev/null
docker builder prune -af      # Svuota cache di build (lento la volta dopo!)
docker compose build --no-cache --pull frontend backend
docker compose up -d
```

⚠️ Il `docker builder prune -af` cancella la cache di **tutti** i progetti Docker sul Pi (non solo questo). Sarà più lento la prossima volta.

---

### FASE 4 — Verifica del deploy

Attendi ~30 secondi che i container avviino gli healthcheck, poi:

```bash
docker compose ps
```

Devi vedere `sla-frontend`, `sla-backend`, `sla-mongodb` tutti con status `Up ... (healthy)`.

```bash
curl -s http://localhost:8001/api/version
```

Output atteso (esempio):
```json
{"version":"0.10.1-beta","build_date":"2026-02-15","release_name":"..."}
```

Se la versione corrisponde a quella nel codice → **deploy riuscito** ✅

Poi apri il portale nel browser (via URL Cloudflare Tunnel) e verifica:
- Login funzionante
- In basso a destra il **VersionBadge** mostra la versione nuova
- La feature che hai appena aggiunto è visibile e funzionante

---

## 🛠️ Comandi utili post-deploy

### Log in tempo reale
```bash
cd /opt/portale-sla/docker
docker compose logs -f backend      # Solo backend
docker compose logs -f frontend     # Solo frontend
docker compose logs -f              # Tutti insieme
```

### Restart rapido di un singolo servizio
```bash
docker compose restart backend
docker compose restart frontend
```

### Vedere quanto spazio usa Docker
```bash
docker system df
```

### Cleanup periodico (una volta al mese)
```bash
docker system prune -f              # Rimuove container/network/immagini fermi
```

---

## 🚀 Alias per il futuro (opzionale, ma comodissimo)

Aggiungi questo al tuo `~/.bashrc` una volta sola:

```bash
cat >> ~/.bashrc << 'EOF'

# ==== Alias Portale SLA ====
alias sla-pull='cd /opt/portale-sla && git stash && git pull origin main'
alias sla-rebuild='cd /opt/portale-sla/docker && docker compose down && docker rm -f sla-frontend sla-backend 2>/dev/null; docker image rm -f docker-frontend docker-backend 2>/dev/null; docker compose build --no-cache --pull frontend backend && docker compose up -d'
alias sla-status='cd /opt/portale-sla/docker && docker compose ps && echo "---" && curl -s http://localhost:8001/api/version'
alias sla-logs='cd /opt/portale-sla/docker && docker compose logs -f'
alias sla-update='sla-pull && sla-rebuild && sleep 30 && sla-status'
EOF

source ~/.bashrc
```

Dopo questo, la procedura completa diventa:

```bash
sla-update
```

Un solo comando che fa TUTTO. 🎉

---

## ❗ Errori comuni e come risolverli

| Errore | Causa | Soluzione |
|---|---|---|
| `no configuration file provided: not found` | Non sei in `/opt/portale-sla/docker/` | `cd /opt/portale-sla/docker` |
| `git pull` fallisce con conflitti | Hai modifiche locali su file tracciati | `git stash` prima del pull |
| Dopo build la versione è ancora vecchia | Cache Docker | Passa al Livello 2 o 3 |
| Container `sla-backend` in restart loop | Errore Python o env mancante | `docker compose logs backend` |
| Container `sla-frontend` "unhealthy" | Nginx non risponde in tempo | Aspetta 60 secondi o vedi log |
| MongoDB non parte | Volume corrotto o permessi | `docker compose logs mongodb` |
| `curl /api/version` non risponde | Backend non è ancora healthy | Aspetta ancora 30 secondi |
| GitHub `Permission denied (publickey)` | Chiave SSH del Pi non registrata | Usa HTTPS o registra la chiave |

---

## 🔒 Backup prima di aggiornamenti importanti

Prima di aggiornamenti rischiosi (es. cambio schema DB, refactor grosso):

```bash
# Backup MongoDB
bash /opt/portale-sla/scripts/backup_mongodb.sh

# Backup uploads (rimborsi, modulistica, documenti)
bash /opt/portale-sla/scripts/backup_uploads.sh
```

I backup sono in `/opt/portale-sla/backups/`.

---

## 📚 Vedi anche

- `DOCKER_DEPLOYMENT_GUIDE.md` (root del progetto) — Setup iniziale Docker sul Pi
- `RASPBERRY_PI_QUICK_START.md` (root del progetto) — Prima installazione sul Pi
- `docs/GUIDA_CLOUDFLARE_TUNNEL.md` — Setup accesso HTTPS via Cloudflare
- `docs/GUIDA_BACKUP_CIFRATO.md` — Sistema di backup cifrato
- `memory/PRD.md` — Roadmap e stato del progetto

---

**Ultima revisione:** 2026-02-15
**Autore:** Emergent Agent + slaautobrennero
