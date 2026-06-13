#!/bin/bash
# ==============================================================
# Migrazione: attivazione autenticazione MongoDB
# ==============================================================
# Da eseguire UNA VOLTA SOLA, dopo il git pull, PRIMA del rebuild.
# 
# Cosa fa:
# 1. Legge MONGO_ROOT_USERNAME / MONGO_ROOT_PASSWORD da docker/.env
# 2. Crea l'utente admin nel DB già esistente (era senza auth)
# 3. Verifica che l'auth funzioni
# 4. Termina: puoi fare `docker compose up -d --build`
# ==============================================================
set -e

cd "$(dirname "$0")/../docker"

if [ ! -f .env ]; then
  echo "❌ docker/.env non trovato"
  exit 1
fi

# Carica variabili
source .env
USER="${MONGO_ROOT_USERNAME:-admin}"
PASS="$MONGO_ROOT_PASSWORD"

if [ -z "$PASS" ] || [[ "$PASS" == *"CAMBIA"* ]]; then
  echo "❌ Devi prima impostare MONGO_ROOT_PASSWORD in docker/.env"
  echo "   Genera password: openssl rand -base64 24"
  exit 1
fi

echo "==================================="
echo "  Setup Auth MongoDB - Portale SLA"
echo "==================================="
echo ""
echo "Utente admin: $USER"
echo "Password:     ${PASS:0:4}**** (nascosta)"
echo ""

# Check container attivo
if ! docker ps --format '{{.Names}}' | grep -q "^sla-mongodb$"; then
  echo "❌ Container sla-mongodb non in esecuzione. Avvialo: docker compose up -d mongodb"
  exit 1
fi

# Verifica se l'utente esiste già
EXISTING=$(docker exec sla-mongodb mongo admin --quiet --eval "db.getUser('$USER') ? 'YES' : 'NO'" 2>/dev/null | tail -1)

if [ "$EXISTING" = "YES" ]; then
  echo "✓ L'utente '$USER' esiste già. Aggiorno la password..."
  docker exec sla-mongodb mongo admin --quiet --eval "db.updateUser('$USER', {pwd: '$PASS'})" >/dev/null
else
  echo "[1/2] Creazione utente admin..."
  docker exec sla-mongodb mongo admin --quiet --eval "
    db.createUser({
      user: '$USER',
      pwd: '$PASS',
      roles: [{role: 'root', db: 'admin'}]
    })
  " >/dev/null
  echo "✓ Utente creato"
fi

echo "[2/2] Test connessione con auth..."
TEST=$(docker exec sla-mongodb mongo admin -u "$USER" -p "$PASS" --quiet --eval "db.runCommand({ ping: 1 }).ok" 2>/dev/null | tail -1)
if [ "$TEST" = "1" ]; then
  echo "✓ Auth funziona"
else
  echo "❌ Test fallito"
  exit 1
fi

echo ""
echo "==================================="
echo "  ✅ MIGRAZIONE COMPLETATA"
echo "==================================="
echo ""
echo "Ora rebuilda i container:"
echo "  cd /opt/portale-sla/docker"
echo "  docker compose down"
echo "  docker compose up -d --build"
echo ""
echo "Dopo l'avvio, il DB sarà raggiungibile SOLO con username/password."
echo ""
