#!/bin/bash
# ==============================================================
# Setup Tailscale per Raspberry Pi (DietPi)
# ==============================================================
# Tailscale è una VPN privata che ti permette di accedere al Pi
# da qualunque rete del mondo come fosse rete locale.
# 
# Cosa fa questo script:
# 1. Installa Tailscale
# 2. Lo avvia come servizio
# 3. Genera un link da aprire sul browser per autenticarsi
# 
# DOPO che funziona puoi fare SSH al Pi anche da fuori casa:
#   ssh root@<ip-tailscale-del-pi>
# (l'IP sarà tipo 100.x.y.z, te lo dice Tailscale dopo il login)
# ==============================================================

set -e

echo "==================================="
echo "  Setup Tailscale - Portale SLA"
echo "==================================="
echo ""

# Verifica esecuzione come root
if [ "$EUID" -ne 0 ]; then
  echo "❌ Esegui come root: sudo bash $0"
  exit 1
fi

# Check se già installato
if command -v tailscale &> /dev/null; then
  echo "✓ Tailscale già installato. Stato attuale:"
  tailscale status 2>/dev/null || echo "  (non ancora autenticato)"
  echo ""
  read -p "Vuoi ri-eseguire login? (s/N): " choice
  if [[ ! "$choice" =~ ^[sS]$ ]]; then
    echo "Operazione annullata."
    exit 0
  fi
else
  echo "[1/3] Installazione Tailscale (richiede ~1 min)..."
  curl -fsSL https://tailscale.com/install.sh | sh
  echo "✓ Tailscale installato"
fi

echo ""
echo "[2/3] Avvio servizio..."
systemctl enable tailscaled
systemctl start tailscaled
sleep 2

echo ""
echo "[3/3] Avvio autenticazione..."
echo ""
echo "⚠️  IMPORTANTE: tra qualche secondo apparirà un LINK."
echo "   Aprilo su un browser (anche dal tuo telefono) e fai login"
echo "   con account Google/Microsoft/GitHub (è gratis)."
echo ""
sleep 2

# Avvia tailscale; mostra il link di login e lascia stampato l'IP finale
tailscale up --ssh

echo ""
echo "==================================="
echo "  ✅ SETUP COMPLETATO"
echo "==================================="
echo ""
echo "IP Tailscale di questo Pi:"
tailscale ip -4
echo ""
echo "Da QUALUNQUE rete con Tailscale attivo, ora puoi fare:"
echo "  ssh root@$(tailscale ip -4)"
echo ""
echo "Per disinstallare (in futuro):"
echo "  tailscale logout && apt remove tailscale -y"
echo ""
