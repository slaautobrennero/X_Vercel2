# 🔄 Guida Completa: Backup Automatico MongoDB → Google Drive

## Panoramica

Sistema di backup automatico che:
- ✅ Fa dump del database MongoDB ogni giorno (personalizzabile)
- ✅ Comprime i backup (.tar.gz)
- ✅ Carica automaticamente su Google Drive
- ✅ Mantiene solo gli ultimi 7 backup (configurable)
- ✅ Log delle operazioni
- ✅ Script di restore rapido

---

## 📋 Prerequisiti

- Raspberry Pi con Portale SLA funzionante
- Account Google Drive (gratis)
- 10 minuti di tempo

---

## 🚀 SETUP PASSO-PASSO

### **STEP 1: Copia gli Script sul Raspberry Pi**

Sul tuo **Raspberry Pi**, esegui:

```bash
# Crea directory scripts se non esiste
mkdir -p /opt/portale-sla/scripts

# Crea directory backup
mkdir -p /opt/portale-sla/backups
```

Ora copia i file da `/app/scripts/` del progetto Emergent al Raspberry Pi:

**Opzione A: Copia manuale** (se hai accesso SSH dal PC):
```bash
# Dal tuo PC (sostituisci con il tuo IP Raspberry)
scp /percorso/progetto/scripts/backup_mongodb.sh root@192.168.0.99:/opt/portale-sla/scripts/
scp /percorso/progetto/scripts/restore_mongodb.sh root@192.168.0.99:/opt/portale-sla/scripts/
```

**Opzione B: Crea manualmente sul Raspberry Pi**:
```bash
# Sul Raspberry Pi
nano /opt/portale-sla/scripts/backup_mongodb.sh
# Incolla il contenuto dello script backup_mongodb.sh
# Salva: CTRL+X → Y → INVIO

nano /opt/portale-sla/scripts/restore_mongodb.sh
# Incolla il contenuto dello script restore_mongodb.sh
# Salva: CTRL+X → Y → INVIO
```

**Rendi gli script eseguibili:**
```bash
chmod +x /opt/portale-sla/scripts/backup_mongodb.sh
chmod +x /opt/portale-sla/scripts/restore_mongodb.sh
```

---

### **STEP 2: Test Backup Locale (senza Google Drive)**

Prima testiamo che il backup funzioni localmente:

```bash
# Esegui backup manuale
/opt/portale-sla/scripts/backup_mongodb.sh
```

**Output atteso:**
```
========================================
  Backup MongoDB - Portale SLA
========================================

[1/5] Verifica container MongoDB...
✓ MongoDB attivo
[2/5] Creazione dump database...
✓ Dump completato
[3/5] Copia backup dal container...
✓ Backup copiato in: /opt/portale-sla/backups/backup_20260419_190000
[4/5] Compressione backup...
✓ Backup compresso: backup_20260419_190000.tar.gz
[5/5] Pulizia container...
✓ Pulizia completata
[Extra] Rimozione backup vecchi (>7 giorni)...
✓ Backup totali conservati: 1
⚠ rclone non installato (backup solo locale)

========================================
  BACKUP COMPLETATO!
========================================
Backup: backup_20260419_190000.tar.gz
Dimensione: 12M
Percorso: /opt/portale-sla/backups
```

✅ Se vedi questo, il backup locale funziona!

Verifica che il file esista:
```bash
ls -lh /opt/portale-sla/backups/
```

---

### **STEP 3: Installa e Configura rclone per Google Drive**

**3.1 Installa rclone:**
```bash
sudo apt update
sudo apt install rclone -y
```

**3.2 Configura Google Drive:**
```bash
rclone config
```

Segui questa sequenza:

```
n/s/q> n                          # New remote
name> gdrive                      # Nome: gdrive
Storage> drive                    # Tipo: Google Drive (digita "drive")
client_id>                        # Premi INVIO (usa default)
client_secret>                    # Premi INVIO (usa default)
scope> 1                          # Full access
root_folder_id>                   # Premi INVIO
service_account_file>             # Premi INVIO
Edit advanced config? (y/n) n    # No
Use auto config? (y/n) n          # No (non abbiamo browser sul Raspberry)
```

**IMPORTANTE:** Apparirà un link tipo:
```
https://accounts.google.com/o/oauth2/auth?access_type=...
```

**3.3 Autorizza Google Drive:**

1. **Copia quel link**
2. **Aprilo nel browser del tuo PC**
3. Fai login con il tuo account Google
4. Autorizza rclone
5. Google ti darà un **codice di autorizzazione**
6. **Copia il codice** e incollalo nel terminale SSH del Raspberry

```
Enter verification code> [INCOLLA IL CODICE QUI]
```

Continua:
```
Configure this as a team drive? (y/n) n
Yes this is OK (y/n) y            # Conferma
Current remotes:                   # Vedrai "gdrive"
e/n/d/r/c/s/q> q                  # Quit
```

**3.4 Test Google Drive:**
```bash
# Crea cartella su Google Drive
rclone mkdir gdrive:Portale-SLA-Backups

# Lista cartelle
rclone lsd gdrive:

# Dovresti vedere: Portale-SLA-Backups
```

✅ Se vedi la cartella, Google Drive è configurato!

---

### **STEP 4: Test Backup Completo con Upload Google Drive**

Ora esegui di nuovo il backup - questa volta caricherà su Google Drive:

```bash
/opt/portale-sla/scripts/backup_mongodb.sh
```

**Output finale deve includere:**
```
[Sync] Sincronizzazione con Google Drive...
Transferred:   	   12.345 MiB / 12.345 MiB, 100%
✓ Backup caricato su Google Drive!
```

**Verifica su Google Drive:**

Vai su https://drive.google.com nel browser e cerca la cartella **Portale-SLA-Backups**. Dovresti vedere il file `.tar.gz`!

---

### **STEP 5: Automatizza con Cron (Backup Giornaliero)**

**5.1 Apri crontab:**
```bash
crontab -e
```

**5.2 Aggiungi questa riga alla fine del file:**

```bash
# Backup MongoDB ogni giorno alle 3:00 AM
0 3 * * * /opt/portale-sla/scripts/backup_mongodb.sh >> /var/log/sla_backup.log 2>&1
```

**Salva:** CTRL+X → Y → INVIO

**5.3 Verifica cron installato:**
```bash
crontab -l
```

Dovresti vedere la riga appena aggiunta.

---

## ✅ BACKUP COMPLETATO!

Ora hai:
- ✅ Backup automatico ogni giorno alle 3:00 AM
- ✅ Upload automatico su Google Drive
- ✅ Retention 7 giorni (vecchi backup eliminati automaticamente)
- ✅ Log salvati in `/var/log/sla_backup.log`

---

## 🔄 Come Ripristinare un Backup

### Metodo 1: Script Automatico (Consigliato)

```bash
/opt/portale-sla/scripts/restore_mongodb.sh
```

Lo script ti mostrerà la lista dei backup disponibili. Scegli il numero e conferma!

### Metodo 2: Manuale

```bash
# 1. Scarica backup da Google Drive (se necessario)
rclone copy "gdrive:Portale-SLA-Backups/backup_20260419_190000.tar.gz" /opt/portale-sla/backups/

# 2. Decomprimi
cd /opt/portale-sla/backups
tar -xzf backup_20260419_190000.tar.gz

# 3. Ferma backend
docker compose -f /opt/portale-sla/docker/docker-compose.yml stop backend

# 4. Copia nel container
docker cp backup_20260419_190000 sla-mongodb:/restore

# 5. Restore
docker exec sla-mongodb mongorestore \
  --db=sla_sindacato \
  --drop \
  /restore

# 6. Riavvia backend
docker compose -f /opt/portale-sla/docker/docker-compose.yml start backend
```

---

## 📊 Monitoraggio Backup

**Visualizza log backup:**
```bash
tail -f /var/log/sla_backup.log
```

**Lista backup locali:**
```bash
ls -lh /opt/portale-sla/backups/
```

**Lista backup su Google Drive:**
```bash
rclone ls gdrive:Portale-SLA-Backups/
```

**Spazio occupato:**
```bash
du -sh /opt/portale-sla/backups/
```

---

## ⚙️ Configurazione Avanzata

### Cambia Orario Backup

Modifica crontab:
```bash
crontab -e

# Esempi:
0 2 * * *   # Ogni giorno alle 2:00 AM
0 */6 * * * # Ogni 6 ore
0 0 * * 0   # Ogni domenica a mezzanotte
```

### Cambia Retention (giorni da mantenere)

Modifica lo script:
```bash
nano /opt/portale-sla/scripts/backup_mongodb.sh

# Cerca questa riga e cambia il numero:
RETENTION_DAYS=7  # Cambia a 14, 30, ecc.
```

### Notifiche Email (Opzionale)

Installa mailutils:
```bash
sudo apt install mailutils -y
```

Aggiungi alla fine dello script backup:
```bash
# Dopo l'ultima echo
echo "Backup completato: $BACKUP_NAME" | mail -s "Backup SLA OK" tua-email@example.com
```

---

## 🆘 Troubleshooting

### "Container MongoDB non attivo"
```bash
docker compose -f /opt/portale-sla/docker/docker-compose.yml ps
# Verifica che sla-mongodb sia UP
```

### "rclone: command not found"
```bash
sudo apt install rclone -y
```

### "gdrive: remote not found"
Riconfi rclone:
```bash
rclone config
```

### Backup troppo grandi
Comprimi di più:
```bash
# Nel backup script, cambia tar con:
tar -czf --best "$BACKUP_DIR/$BACKUP_NAME.tar.gz" -C "$BACKUP_DIR" "$BACKUP_NAME"
```

---

## 📚 File di Riferimento

- Script backup: `/opt/portale-sla/scripts/backup_mongodb.sh`
- Script restore: `/opt/portale-sla/scripts/restore_mongodb.sh`
- Directory backup: `/opt/portale-sla/backups/`
- Log: `/var/log/sla_backup.log`
- Cron: `crontab -l`

---

**🎉 Sistema di backup completo e automatico configurato!**
