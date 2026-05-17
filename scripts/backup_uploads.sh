#!/bin/bash
#############################################
# Script Backup Uploads (file utenti) → Google Drive
# Portale SLA - Sindacato Lavoratori Autostradali
#############################################

# Configurazione
BACKUP_DIR="/opt/portale-sla/backups/uploads"
UPLOADS_PATH="/mnt/dietpi_userdata/docker-data/volumes/sla-uploads-data/_data"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="uploads_${TIMESTAMP}"
RETENTION_DAYS=14
GDRIVE_DEST="gdrive:Portale-SLA-Backups/uploads/"

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Backup UPLOADS - Portale SLA${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

mkdir -p "$BACKUP_DIR"

# Verifica path uploads
if [ ! -d "$UPLOADS_PATH" ]; then
    echo -e "${RED}✗ Path uploads non trovato: $UPLOADS_PATH${NC}"
    exit 1
fi

FILE_COUNT=$(find "$UPLOADS_PATH" -type f | wc -l)
echo -e "${YELLOW}[1/3]${NC} File trovati: $FILE_COUNT"

if [ "$FILE_COUNT" -eq 0 ]; then
    echo -e "${YELLOW}⚠ Nessun file da backuppare. Esco.${NC}"
    exit 0
fi

# Compressione tar.gz
echo -e "${YELLOW}[2/3]${NC} Compressione..."
tar -czf "$BACKUP_DIR/$BACKUP_NAME.tar.gz" -C "$(dirname "$UPLOADS_PATH")" "$(basename "$UPLOADS_PATH")"

if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Compressione fallita${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Compresso: $BACKUP_NAME.tar.gz ($(du -h "$BACKUP_DIR/$BACKUP_NAME.tar.gz" | cut -f1))${NC}"

# Retention
find "$BACKUP_DIR" -name "uploads_*.tar.gz" -type f -mtime +${RETENTION_DAYS} -delete

# Upload Google Drive
echo -e "${YELLOW}[3/3]${NC} Upload Google Drive..."
if command -v rclone &> /dev/null && rclone listremotes | grep -q "gdrive:"; then
    rclone copy "$BACKUP_DIR/$BACKUP_NAME.tar.gz" "$GDRIVE_DEST" --quiet
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Caricato su Google Drive${NC}"
    else
        echo -e "${RED}✗ Errore upload Google Drive${NC}"
    fi
else
    echo -e "${YELLOW}⚠ rclone/gdrive non configurato${NC}"
fi

echo ""
echo -e "${GREEN}BACKUP UPLOADS COMPLETATO${NC}"
echo -e "File: ${BACKUP_NAME}.tar.gz"
echo -e "Locali: $(find "$BACKUP_DIR" -name "uploads_*.tar.gz" -type f | wc -l) backup conservati"
echo ""
