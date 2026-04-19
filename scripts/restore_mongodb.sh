#!/bin/bash
#############################################
# Script Restore MongoDB da Backup
# Portale SLA
#############################################

# Colori
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

BACKUP_DIR="/opt/portale-sla/backups"
CONTAINER_NAME="sla-mongodb"
DB_NAME="sla_sindacato"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Restore MongoDB - Portale SLA${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Lista backup disponibili
echo -e "${YELLOW}Backup disponibili:${NC}"
echo ""
ls -lh "$BACKUP_DIR"/*.tar.gz 2>/dev/null | awk '{print $9}' | nl
echo ""

# Chiedi quale backup ripristinare
read -p "Inserisci il numero del backup da ripristinare (o 'q' per uscire): " CHOICE

if [ "$CHOICE" = "q" ]; then
    echo "Operazione annullata."
    exit 0
fi

# Ottieni il file selezionato
BACKUP_FILE=$(ls -1 "$BACKUP_DIR"/*.tar.gz 2>/dev/null | sed -n "${CHOICE}p")

if [ -z "$BACKUP_FILE" ]; then
    echo -e "${RED}✗ Backup non valido!${NC}"
    exit 1
fi

echo ""
echo -e "${YELLOW}Backup selezionato:${NC} $(basename "$BACKUP_FILE")"
echo ""
echo -e "${RED}⚠ ATTENZIONE: Questo sovrascriverà il database corrente!${NC}"
read -p "Sei sicuro di voler continuare? (sì/no): " CONFIRM

if [ "$CONFIRM" != "sì" ] && [ "$CONFIRM" != "si" ]; then
    echo "Operazione annullata."
    exit 0
fi

# Decomprimi backup
echo -e "${YELLOW}[1/4]${NC} Decompressione backup..."
TEMP_DIR=$(mktemp -d)
tar -xzf "$BACKUP_FILE" -C "$TEMP_DIR"
echo -e "${GREEN}✓ Decompressione completata${NC}"

# Ferma backend per evitare scritture durante restore
echo -e "${YELLOW}[2/4]${NC} Arresto backend..."
docker compose -f /opt/portale-sla/docker/docker-compose.yml stop backend
echo -e "${GREEN}✓ Backend arrestato${NC}"

# Copia backup nel container
echo -e "${YELLOW}[3/4]${NC} Copia backup nel container..."
BACKUP_NAME=$(basename "$BACKUP_FILE" .tar.gz)
docker cp "$TEMP_DIR/$BACKUP_NAME" "$CONTAINER_NAME:/restore"

# Restore database
echo -e "${YELLOW}[4/4]${NC} Restore database..."
docker exec "$CONTAINER_NAME" mongorestore \
    --db="$DB_NAME" \
    --drop \
    "/restore" \
    --quiet

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Restore completato!${NC}"
else
    echo -e "${RED}✗ Errore durante il restore${NC}"
    exit 1
fi

# Pulizia
docker exec "$CONTAINER_NAME" rm -rf /restore
rm -rf "$TEMP_DIR"

# Riavvia backend
echo -e "${YELLOW}Riavvio backend...${NC}"
docker compose -f /opt/portale-sla/docker/docker-compose.yml start backend
sleep 3
echo -e "${GREEN}✓ Backend riavviato${NC}"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  RESTORE COMPLETATO!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
