#!/bin/bash
#############################################
# Script Backup Automatico MongoDB → Google Drive
# Portale SLA - Sindacato Lavoratori Autostradali
#############################################

# Configurazione
BACKUP_DIR="/opt/portale-sla/backups"
DB_NAME="sla_sindacato"
CONTAINER_NAME="sla-mongodb"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="backup_${TIMESTAMP}"
RETENTION_DAYS=7  # Mantieni backup per 7 giorni

# Colori per output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Backup MongoDB - Portale SLA${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Crea directory backup se non esiste
mkdir -p "$BACKUP_DIR"

# Step 1: Verifica container MongoDB attivo
echo -e "${YELLOW}[1/5]${NC} Verifica container MongoDB..."
if ! docker ps | grep -q "$CONTAINER_NAME"; then
    echo -e "${RED}✗ ERRORE: Container MongoDB non attivo!${NC}"
    exit 1
fi
echo -e "${GREEN}✓ MongoDB attivo${NC}"

# Step 2: Dump database
echo -e "${YELLOW}[2/5]${NC} Creazione dump database..."
docker exec "$CONTAINER_NAME" mongodump \
    --db="$DB_NAME" \
    --out="/dump" \
    --quiet

if [ $? -ne 0 ]; then
    echo -e "${RED}✗ ERRORE: Dump database fallito!${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Dump completato${NC}"

# Step 3: Copia dump dal container
echo -e "${YELLOW}[3/5]${NC} Copia backup dal container..."
docker cp "$CONTAINER_NAME:/dump/$DB_NAME" "$BACKUP_DIR/$BACKUP_NAME"

if [ $? -ne 0 ]; then
    echo -e "${RED}✗ ERRORE: Copia backup fallita!${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Backup copiato in: $BACKUP_DIR/$BACKUP_NAME${NC}"

# Step 4: Comprimi backup
echo -e "${YELLOW}[4/5]${NC} Compressione backup..."
tar -czf "$BACKUP_DIR/$BACKUP_NAME.tar.gz" -C "$BACKUP_DIR" "$BACKUP_NAME"

if [ $? -eq 0 ]; then
    rm -rf "$BACKUP_DIR/$BACKUP_NAME"  # Rimuovi versione non compressa
    echo -e "${GREEN}✓ Backup compresso: $BACKUP_NAME.tar.gz${NC}"
else
    echo -e "${RED}✗ Compressione fallita (backup non compresso mantenuto)${NC}"
fi

# Step 5: Pulizia dump nel container
echo -e "${YELLOW}[5/5]${NC} Pulizia container..."
docker exec "$CONTAINER_NAME" rm -rf /dump
echo -e "${GREEN}✓ Pulizia completata${NC}"

# Step 6: Rimuovi backup vecchi (più di RETENTION_DAYS giorni)
echo -e "${YELLOW}[Extra]${NC} Rimozione backup vecchi (>${RETENTION_DAYS} giorni)..."
find "$BACKUP_DIR" -name "backup_*.tar.gz" -type f -mtime +${RETENTION_DAYS} -delete
OLD_COUNT=$(find "$BACKUP_DIR" -name "backup_*.tar.gz" -type f | wc -l)
echo -e "${GREEN}✓ Backup totali conservati: $OLD_COUNT${NC}"

# Step 7: Sincronizzazione Google Drive (se rclone configurato)
if command -v rclone &> /dev/null; then
    if rclone listremotes | grep -q "gdrive:"; then
        echo -e "${YELLOW}[Sync]${NC} Sincronizzazione con Google Drive..."
        rclone copy "$BACKUP_DIR/$BACKUP_NAME.tar.gz" "gdrive:Portale-SLA-Backups/" --progress
        
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✓ Backup caricato su Google Drive!${NC}"
        else
            echo -e "${RED}✗ Errore upload Google Drive${NC}"
        fi
    else
        echo -e "${YELLOW}⚠ Google Drive non configurato (esegui setup rclone)${NC}"
    fi
else
    echo -e "${YELLOW}⚠ rclone non installato (backup solo locale)${NC}"
fi

# Riepilogo finale
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  BACKUP COMPLETATO!${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "Backup: ${GREEN}$BACKUP_NAME.tar.gz${NC}"
echo -e "Dimensione: $(du -h "$BACKUP_DIR/$BACKUP_NAME.tar.gz" | cut -f1)"
echo -e "Percorso: $BACKUP_DIR"
echo ""
