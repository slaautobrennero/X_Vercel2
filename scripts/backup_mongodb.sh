#!/bin/bash
#############################################
# Script Backup MongoDB CIFRATO → Google Drive
# Portale SLA - Sindacato Lavoratori Autostradali
#############################################

# Configurazione
BACKUP_DIR="/opt/portale-sla/backups/db"
DB_NAME="sla_sindacato"
CONTAINER_NAME="sla-mongodb"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="db_${TIMESTAMP}"
RETENTION_DAYS=14
PASSWORD_FILE="/opt/portale-sla/.backup_password"
GDRIVE_DEST="gdrive:Portale-SLA-Backups/db/"

# Colori
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Backup MongoDB CIFRATO - Portale SLA${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Verifica password
if [ ! -f "$PASSWORD_FILE" ]; then
    echo -e "${RED}✗ ERRORE: file password non trovato: $PASSWORD_FILE${NC}"
    echo "Crealo con:  echo 'TUA_PASSWORD' > $PASSWORD_FILE && chmod 600 $PASSWORD_FILE"
    exit 1
fi

PERMS=$(stat -c "%a" "$PASSWORD_FILE")
if [ "$PERMS" != "600" ]; then
    echo -e "${YELLOW}⚠ Permessi password file non sicuri ($PERMS), correggo a 600${NC}"
    chmod 600 "$PASSWORD_FILE"
fi

mkdir -p "$BACKUP_DIR"

# Verifica container
echo -e "${YELLOW}[1/6]${NC} Verifica container MongoDB..."
if ! docker ps | grep -q "$CONTAINER_NAME"; then
    echo -e "${RED}✗ ERRORE: Container MongoDB non attivo!${NC}"
    exit 1
fi
echo -e "${GREEN}✓ MongoDB attivo${NC}"

# Dump
echo -e "${YELLOW}[2/6]${NC} Creazione dump database..."
docker exec "$CONTAINER_NAME" mongodump --db="$DB_NAME" --out="/dump" --quiet
if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Dump fallito${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Dump completato${NC}"

# Copia + compressione
echo -e "${YELLOW}[3/6]${NC} Compressione..."
docker cp "$CONTAINER_NAME:/dump/$DB_NAME" "$BACKUP_DIR/$BACKUP_NAME"
tar -czf "$BACKUP_DIR/$BACKUP_NAME.tar.gz" -C "$BACKUP_DIR" "$BACKUP_NAME"
rm -rf "$BACKUP_DIR/$BACKUP_NAME"
echo -e "${GREEN}✓ Compresso: $BACKUP_NAME.tar.gz${NC}"

# Cifratura AES-256-CBC con password
echo -e "${YELLOW}[4/6]${NC} Cifratura AES-256..."
openssl enc -aes-256-cbc -pbkdf2 -salt -iter 100000 \
    -in "$BACKUP_DIR/$BACKUP_NAME.tar.gz" \
    -out "$BACKUP_DIR/$BACKUP_NAME.tar.gz.enc" \
    -pass file:"$PASSWORD_FILE"

if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Cifratura fallita${NC}"
    exit 1
fi

# Rimuovi versione non cifrata
rm -f "$BACKUP_DIR/$BACKUP_NAME.tar.gz"
echo -e "${GREEN}✓ Cifrato: $BACKUP_NAME.tar.gz.enc${NC}"

# Pulizia container
echo -e "${YELLOW}[5/6]${NC} Pulizia container..."
docker exec "$CONTAINER_NAME" rm -rf /dump
echo -e "${GREEN}✓ Pulizia OK${NC}"

# Retention
find "$BACKUP_DIR" -name "db_*.tar.gz.enc" -type f -mtime +${RETENTION_DAYS} -delete
LOCAL_COUNT=$(find "$BACKUP_DIR" -name "db_*.tar.gz.enc" -type f | wc -l)

# Upload Google Drive
echo -e "${YELLOW}[6/6]${NC} Upload Google Drive..."
if command -v rclone &> /dev/null && rclone listremotes | grep -q "gdrive:"; then
    rclone copy "$BACKUP_DIR/$BACKUP_NAME.tar.gz.enc" "$GDRIVE_DEST" --quiet
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Caricato su Google Drive${NC}"
    else
        echo -e "${RED}✗ Errore upload Google Drive${NC}"
    fi
else
    echo -e "${YELLOW}⚠ rclone/gdrive non configurato (solo locale)${NC}"
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  BACKUP DB COMPLETATO!${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "File:       ${GREEN}$BACKUP_NAME.tar.gz.enc${NC}"
echo -e "Dimensione: $(du -h "$BACKUP_DIR/$BACKUP_NAME.tar.gz.enc" | cut -f1)"
echo -e "Locali:     $LOCAL_COUNT backup conservati"
echo -e "Cifratura:  AES-256-CBC con PBKDF2 (100k iter)"
echo ""
