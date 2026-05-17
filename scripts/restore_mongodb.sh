#!/bin/bash
#############################################
# Script Restore MongoDB CIFRATO
# Portale SLA - Sindacato Lavoratori Autostradali
#############################################

DB_NAME="sla_sindacato"
CONTAINER_NAME="sla-mongodb"
PASSWORD_FILE="/opt/portale-sla/.backup_password"

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Restore MongoDB CIFRATO - Portale SLA${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Verifica argomenti
if [ -z "$1" ]; then
    echo -e "${RED}Uso:${NC} $0 <percorso_backup.tar.gz.enc>"
    echo ""
    echo "Esempio: $0 /opt/portale-sla/backups/db/db_20260512_030000.tar.gz.enc"
    echo ""
    echo "Backup locali disponibili:"
    ls -lh /opt/portale-sla/backups/db/*.tar.gz.enc 2>/dev/null || echo "  (nessuno)"
    exit 1
fi

BACKUP_FILE="$1"

if [ ! -f "$BACKUP_FILE" ]; then
    echo -e "${RED}✗ File non trovato: $BACKUP_FILE${NC}"
    exit 1
fi

if [ ! -f "$PASSWORD_FILE" ]; then
    echo -e "${RED}✗ File password non trovato: $PASSWORD_FILE${NC}"
    exit 1
fi

# Conferma destruttiva
echo -e "${YELLOW}⚠️  ATTENZIONE: Questo sovrascriverà il database '$DB_NAME' attuale!${NC}"
read -p "Continuare? (scrivi 'SI' per confermare): " confirm
if [ "$confirm" != "SI" ]; then
    echo "Annullato."
    exit 0
fi

TMP_DIR=$(mktemp -d)
DECRYPTED="$TMP_DIR/backup.tar.gz"

# Decifratura
echo -e "${YELLOW}[1/4]${NC} Decifratura backup..."
openssl enc -d -aes-256-cbc -pbkdf2 -salt -iter 100000 \
    -in "$BACKUP_FILE" \
    -out "$DECRYPTED" \
    -pass file:"$PASSWORD_FILE"

if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Decifratura fallita! Password errata?${NC}"
    rm -rf "$TMP_DIR"
    exit 1
fi
echo -e "${GREEN}✓ Decifrato${NC}"

# Estrazione
echo -e "${YELLOW}[2/4]${NC} Estrazione archivio..."
tar -xzf "$DECRYPTED" -C "$TMP_DIR"
DUMP_DIR=$(find "$TMP_DIR" -maxdepth 2 -type d -name "db_*" | head -1)
if [ -z "$DUMP_DIR" ]; then
    DUMP_DIR=$(find "$TMP_DIR" -maxdepth 2 -type d ! -name "$(basename "$TMP_DIR")" | head -1)
fi
echo -e "${GREEN}✓ Estratto in: $DUMP_DIR${NC}"

# Copia nel container
echo -e "${YELLOW}[3/4]${NC} Copia nel container MongoDB..."
docker cp "$DUMP_DIR" "$CONTAINER_NAME:/restore_$DB_NAME"

# Restore
echo -e "${YELLOW}[4/4]${NC} Restore database..."
docker exec "$CONTAINER_NAME" mongorestore --drop --db="$DB_NAME" "/restore_$DB_NAME" --quiet
RESTORE_STATUS=$?

# Pulizia
docker exec "$CONTAINER_NAME" rm -rf "/restore_$DB_NAME"
rm -rf "$TMP_DIR"

if [ $RESTORE_STATUS -eq 0 ]; then
    echo -e "${GREEN}✓ Restore completato!${NC}"
else
    echo -e "${RED}✗ Restore fallito${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}DATABASE RIPRISTINATO CON SUCCESSO${NC}"
echo -e "Riavvia il backend per riconnetterti: ${YELLOW}docker compose restart backend${NC}"
echo ""
