# 🔐 Setup Backup Cifrato + Pulizia Docker

## 1. Crea la password di cifratura backup

⚠️ **CRITICO**: salva la password anche in un password manager esterno (Bitwarden, 1Password, foglio cartaceo). Se la perdi, **i backup cifrati sono irrecuperabili**.

```bash
# Crea il file password (SOLO leggibile da root)
echo "TUA_PASSWORD_SUPER_SEGRETA_QUI" > /opt/portale-sla/.backup_password
chmod 600 /opt/portale-sla/.backup_password

# Verifica
ls -la /opt/portale-sla/.backup_password
# Deve mostrare:  -rw------- 1 root root ... .backup_password
```

💡 Suggerimento password forte: `PortaleSLA-Backup-2026-MioCodice!@#`

---

## 2. Rendi eseguibili gli script

```bash
chmod +x /opt/portale-sla/scripts/backup_mongodb.sh
chmod +x /opt/portale-sla/scripts/backup_uploads.sh
chmod +x /opt/portale-sla/scripts/restore_mongodb.sh
chmod +x /opt/portale-sla/scripts/cleanup_docker.sh
```

---

## 3. Test manuale (consigliato prima di automatizzare)

```bash
# Backup DB (verifica cifratura)
/opt/portale-sla/scripts/backup_mongodb.sh

# Backup uploads (verifica anche se vuoto)
/opt/portale-sla/scripts/backup_uploads.sh

# Pulizia Docker
/opt/portale-sla/scripts/cleanup_docker.sh
```

Verifica che i file `.tar.gz.enc` siano presenti in `/opt/portale-sla/backups/db/` e su Google Drive.

---

## 4. Setup crontab automatico

Esegui:
```bash
crontab -e
```

E inserisci (sostituendo le vecchie righe se presenti):

```cron
# Backup DB ogni giorno alle 03:00
0 3 * * * /opt/portale-sla/scripts/backup_mongodb.sh >> /var/log/sla-backup-db.log 2>&1

# Backup uploads ogni giorno alle 03:15
15 3 * * * /opt/portale-sla/scripts/backup_uploads.sh >> /var/log/sla-backup-uploads.log 2>&1

# Pulizia Docker ogni domenica alle 02:00
0 2 * * 0 /opt/portale-sla/scripts/cleanup_docker.sh >> /var/log/sla-cleanup.log 2>&1
```

Salva ed esci. Verifica:
```bash
crontab -l
```

---

## 5. Test restore (importante!)

Prima del primo "incidente" reale, **prova il restore** su un backup di test:

```bash
# Vedi backup disponibili
ls -lh /opt/portale-sla/backups/db/

# Restore (chiederà conferma "SI")
/opt/portale-sla/scripts/restore_mongodb.sh /opt/portale-sla/backups/db/db_TIMESTAMP.tar.gz.enc
```

---

## 6. Monitoraggio log

```bash
# Vedi ultimi backup eseguiti
tail -50 /var/log/sla-backup-db.log
tail -50 /var/log/sla-backup-uploads.log
tail -50 /var/log/sla-cleanup.log
```

---

## ⚠️ NOTE IMPORTANTI

1. **Password backup**: se la cambi, i backup vecchi diventano illeggibili. Tienine un backup esterno.
2. **Volume uploads Docker**: i file caricati ora sono salvati in `/app/uploads` dentro container, montato su volume Docker `sla-uploads-data` persistente.
3. **Retention**: 14 giorni in locale, illimitato su Google Drive (puoi gestire manualmente da GDrive).
4. **Recovery completo dopo disastro Pi**:
   - Reinstalla DietPi
   - Clona repo, ripristina `.env`, avvia containers
   - Scarica ultimo `db_*.tar.gz.enc` e `uploads_*.tar.gz` da Google Drive
   - Esegui `restore_mongodb.sh` per il DB
   - Estrai uploads con: `tar -xzf uploads_*.tar.gz -C /mnt/dietpi_userdata/docker-data/volumes/sla-uploads-data/`
