#!/bin/bash
#############################################
# Script Pulizia Docker - settimanale
# Portale SLA - Sindacato Lavoratori Autostradali
#############################################

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Pulizia Docker - Portale SLA${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Spazio prima
BEFORE=$(df -h / | awk 'NR==2 {print $4}')
echo -e "${YELLOW}Spazio libero prima: $BEFORE${NC}"
echo ""

# Pulizia immagini non utilizzate
echo -e "${YELLOW}[1/3]${NC} Rimozione immagini non utilizzate..."
docker image prune -af --filter "until=24h" 2>&1 | tail -5

# Pulizia container fermati
echo -e "${YELLOW}[2/3]${NC} Rimozione container fermati..."
docker container prune -f 2>&1 | tail -3

# Pulizia build cache
echo -e "${YELLOW}[3/3]${NC} Rimozione build cache..."
docker builder prune -af --filter "until=24h" 2>&1 | tail -3

# Spazio dopo
AFTER=$(df -h / | awk 'NR==2 {print $4}')
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  PULIZIA COMPLETATA${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "Spazio libero prima: $BEFORE"
echo -e "Spazio libero dopo:  ${GREEN}$AFTER${NC}"
echo ""
