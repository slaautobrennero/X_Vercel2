# 🚀 Portale SLA - Guide Complete Passo-Passo

Benvenuto! Qui trovi tutte le guide per completare la configurazione del Portale SLA.

---

## 📚 Indice Guide

### 1️⃣ **Backup Automatico MongoDB → Google Drive**
📄 **File:** [`GUIDA_BACKUP_GOOGLE_DRIVE.md`](./GUIDA_BACKUP_GOOGLE_DRIVE.md)

**Cosa otterrai:**
- ✅ Backup automatico database ogni giorno
- ✅ Upload su Google Drive
- ✅ Retention 7 giorni
- ✅ Script di restore rapido

**Tempo setup:** ~20 minuti  
**Difficoltà:** ⭐⭐☆☆☆ Facile

**Quando farlo:** **SUBITO** (prima di tutto!)

---

### 2️⃣ **Cloudflare Tunnel - Accesso Internet**
📄 **File:** [`GUIDA_CLOUDFLARE_TUNNEL.md`](./GUIDA_CLOUDFLARE_TUNNEL.md)

**Cosa otterrai:**
- ✅ Portale accessibile da qualsiasi luogo via internet
- ✅ URL permanente tipo `https://portale-sla.tuodominio.com`
- ✅ HTTPS automatico (certificato SSL gratuito)
- ✅ Zero port forwarding sul router
- ✅ Protezione DDoS Cloudflare inclusa

**Tempo setup:** ~15 minuti  
**Difficoltà:** ⭐⭐⭐☆☆ Media

**Quando farlo:** Dopo il backup, prima di condividere con utenti

---

### 3️⃣ **PWA - App Mobile Android/iOS**
📄 **File:** [`GUIDA_PWA_MOBILE.md`](./GUIDA_PWA_MOBILE.md)

**Cosa otterrai:**
- ✅ App installabile su Android e iOS
- ✅ Icona sulla home del telefono
- ✅ Funziona offline
- ✅ Schermo intero (no barra browser)
- ✅ Zero pubblicazione su store

**Tempo setup:** ~30 minuti  
**Difficoltà:** ⭐⭐☆☆☆ Facile

**Quando farlo:** Dopo Cloudflare Tunnel (richiede HTTPS)

---

## 🎯 Ordine Consigliato

```
1. Backup Google Drive  (PRIORITÀ MASSIMA)
   ↓
2. Cloudflare Tunnel    (per accesso pubblico)
   ↓
3. PWA Mobile App       (trasforma in app)
```

---

## 📁 File Disponibili

### Script

| File | Descrizione | Path |
|------|-------------|------|
| `backup_mongodb.sh` | Script backup automatico DB | `/app/scripts/` |
| `restore_mongodb.sh` | Script restore backup | `/app/scripts/` |

### Configurazioni PWA

| File | Descrizione | Path |
|------|-------------|------|
| `manifest.json` | Manifest PWA | `/app/frontend/public/` |
| `service-worker.js` | Service Worker per offline | `/app/frontend/public/` |

### Documentazione

| File | Descrizione | Path |
|------|-------------|------|
| `GUIDA_BACKUP_GOOGLE_DRIVE.md` | Guida backup completa | `/app/docs/` |
| `GUIDA_CLOUDFLARE_TUNNEL.md` | Guida Cloudflare completa | `/app/docs/` |
| `GUIDA_PWA_MOBILE.md` | Guida PWA completa | `/app/docs/` |
| `DOCUMENTAZIONE_COMPLETA.md` | Documentazione progetto completo | `/app/` |

---

## 🔗 Accesso Rapido

### Copia File sul Raspberry Pi

**Opzione A: SCP (dal PC)**
```bash
# Dalla directory del progetto sul PC
scp -r /app/scripts/ root@192.168.0.99:/opt/portale-sla/
scp -r /app/docs/ root@192.168.0.99:/opt/portale-sla/
scp /app/frontend/public/manifest.json root@192.168.0.99:/opt/portale-sla/frontend/public/
scp /app/frontend/public/service-worker.js root@192.168.0.99:/opt/portale-sla/frontend/public/
```

**Opzione B: Manuale (copia-incolla)**

Le guide contengono istruzioni dettagliate per creare i file manualmente.

---

## ✅ Checklist Completa

Prima di condividere il portale con gli utenti, verifica:

### Sicurezza & Backup
- [ ] Backup automatico configurato e testato
- [ ] Backup caricato su Google Drive
- [ ] Script restore testato
- [ ] Password SuperAdmin cambiata (non usare `SuperAdmin2024` in produzione!)

### Accesso Pubblico
- [ ] Cloudflare Tunnel configurato
- [ ] HTTPS funzionante
- [ ] URL permanente assegnato
- [ ] DNS propagato (test da smartphone con dati mobili)

### Mobile App
- [ ] PWA configurata
- [ ] Icone generate
- [ ] Service Worker registrato
- [ ] Test installazione Android
- [ ] Test installazione iOS

### Funzionalità
- [ ] Login funzionante
- [ ] Registrazione nuovi utenti testata
- [ ] Creazione rimborso testata
- [ ] Approvazione rimborso testata (Admin)
- [ ] Upload documenti funzionante
- [ ] Bacheca annunci funzionante

### Performance
- [ ] Container Docker stabili (uptime > 24h)
- [ ] RAM uso < 50% (verifica con `docker stats`)
- [ ] Disco spazio > 2GB liberi
- [ ] Backup automatico eseguito con successo

---

## 🆘 Supporto

### Documentazione Principale
- **Guida completa progetto:** `/app/DOCUMENTAZIONE_COMPLETA.md`
- **README quick start:** `/app/README.md`
- **Credenziali test:** `/app/memory/test_credentials.md`

### Log e Debug

```bash
# Log backend
docker compose -f /opt/portale-sla/docker/docker-compose.yml logs backend -f

# Log frontend
docker compose -f /opt/portale-sla/docker/docker-compose.yml logs frontend -f

# Log MongoDB
docker compose -f /opt/portale-sla/docker/docker-compose.yml logs mongodb -f

# Log backup
tail -f /var/log/sla_backup.log

# Log Cloudflare Tunnel
sudo journalctl -u cloudflared -f
```

### Risorse Sistema

```bash
# Uso container
docker stats

# RAM totale
free -h

# Spazio disco
df -h

# Processi CPU
htop
```

---

## 📊 Roadmap Post-Setup

Dopo aver completato le 3 guide, considera:

1. **Popolamento Database**
   - Crea sedi (Autostrade per l'Italia, SATAP, SALT, ecc.)
   - Crea motivi rimborso (Assemblea, Riunione, Formazione)
   - Registra utenti test per ogni ruolo

2. **Google Maps API** (Opzionale)
   - Setup API Key per calcolo automatico KM
   - Guida: `/app/DOCUMENTAZIONE_COMPLETA.md` sezione 14.1

3. **Ottimizzazioni**
   - Paginazione API (roadmap sezione 16.1)
   - Refactoring server.py in routes modulari
   - Frontend error handling migliorato

4. **Sicurezza Avanzata**
   - Rate limiting Cloudflare
   - Geo-restriction (solo Italia)
   - Cloudflare Access (whitelist utenti)

---

## 🎉 Conclusione

Seguendo queste 3 guide avrai un sistema **production-ready**:

✅ **Backup sicuro** → Non perderai mai i dati  
✅ **Accessibile ovunque** → Utenti da tutta Italia  
✅ **App mobile** → Esperienza nativa su smartphone  

**Tempo totale stimato:** ~1-2 ore

**Difficoltà:** Media (le guide sono molto dettagliate!)

---

**Preparato da:** Emergent AI Agent  
**Data:** 19 Aprile 2026  
**Versione:** 1.0  

**Buon lavoro! 🚀**
