#!/bin/bash
#############################################
# Pulizia spazio disco del Raspberry Pi - Portale SLA
# Uso:  sudo bash /opt/portale-sla/scripts/pulizia_raspberry.sh
# Chiede conferma per ogni voce. NON tocca il database del portale
# (volumi Docker) né i backup cifrati recenti.
#############################################

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'

if [ "$EUID" -ne 0 ]; then echo -e "${RED}Esegui con sudo${NC}"; exit 1; fi

chiedi() { read -r -p "$1 [s/N] " r; [[ "$r" =~ ^[sS]$ ]]; }
dimensione() { du -sh "$1" 2>/dev/null | cut -f1; }
titolo() { echo ""; echo -e "${YELLOW}== $1 ==${NC}"; }

PRIMA=$(df -h / | awk 'NR==2 {print $4}')
echo -e "${GREEN}Pulizia Raspberry - spazio libero ora: $PRIMA${NC}"
echo "Le 10 cartelle più pesanti (può richiedere qualche secondo):"
du -xh / --max-depth=2 2>/dev/null | sort -rh | head -10

# 1. Backup di sistema DietPi
titolo "1. Backup di sistema DietPi (dietpi-backup)"
echo "È una copia intera del sistema operativo, NON dei dati del portale."
echo "Se sta sulla stessa scheda SD, quando la scheda si rompe si perde insieme a tutto il resto."
echo "I dati del portale sono già salvati in /opt/portale-sla/backups e su Google Drive."
for d in /mnt/dietpi-backup /mnt/*/dietpi-backup /root/dietpi-backup /var/lib/dietpi/dietpi-backup; do
  [ -d "$d" ] || continue
  echo -e "Trovata: $d (${RED}$(dimensione "$d")${NC}) sul disco $(df "$d" | awk 'NR==2 {print $1}')"
  [ "$(df "$d" | awk 'NR==2 {print $1}')" != "$(df / | awk 'NR==2 {print $1}')" ] && echo "Sta su un disco diverso dalla scheda SD: lì è un backup utile, valuta se tenerlo."
  if chiedi "Eliminarla?"; then rm -rf "$d" && echo -e "${GREEN}Eliminata${NC}"; fi
done
IMP=/boot/dietpi/.dietpi-backup_settings
if [ -f "$IMP" ] && grep -q "^DAILY_BACKUP=1" "$IMP"; then
  echo "Il backup DietPi giornaliero è ATTIVO: ricreerebbe la cartella."
  if chiedi "Disattivare il backup DietPi giornaliero?"; then
    sed -i 's/^DAILY_BACKUP=1/DAILY_BACKUP=0/' "$IMP" && echo -e "${GREEN}Disattivato${NC}"
  fi
fi

# 2. Docker
titolo "2. Docker: immagini vecchie, container fermi, cache delle build"
docker system df 2>/dev/null
if chiedi "Pulire? (il portale resta acceso, i dati non vengono toccati)"; then
  docker container prune -f >/dev/null
  docker image prune -af >/dev/null
  docker builder prune -af >/dev/null
  echo -e "${GREEN}Fatto${NC}"
fi

# 3. Backup del portale troppo vecchi
titolo "3. Backup del portale più vecchi di 30 giorni"
B=/opt/portale-sla/backups
if [ -d "$B" ]; then
  N=$(find "$B" -type f -mtime +30 | wc -l)
  echo "File trovati: $N (le copie su Google Drive restano)"
  if [ "$N" -gt 0 ] && chiedi "Eliminarli?"; then find "$B" -type f -mtime +30 -delete && echo -e "${GREEN}Fatto${NC}"; fi
fi

# 4. Log di sistema
titolo "4. Log di sistema"
journalctl --disk-usage 2>/dev/null
echo "Log vecchi in /var/log: $(find /var/log -type f \( -name '*.gz' -o -name '*.[0-9]' \) 2>/dev/null | wc -l) file"
if chiedi "Tenere solo gli ultimi 7 giorni di log?"; then
  journalctl --vacuum-time=7d >/dev/null 2>&1
  find /var/log -type f \( -name '*.gz' -o -name '*.[0-9]' \) -delete 2>/dev/null
  echo -e "${GREEN}Fatto${NC}"
fi

# 5. Pacchetti e cache
titolo "5. Cache dei pacchetti e file temporanei"
echo "Cache apt: $(dimensione /var/cache/apt) - cache utente: $(dimensione /root/.cache) - file temporanei più vecchi di 2 giorni"
if chiedi "Pulire?"; then
  apt-get clean -y >/dev/null 2>&1
  apt-get autoremove -y >/dev/null 2>&1
  rm -rf /root/.cache/* 2>/dev/null
  find /tmp -mindepth 1 -mtime +2 -delete 2>/dev/null
  echo -e "${GREEN}Fatto${NC}"
fi

# 6. Vecchie copie del codice
titolo "6. Vecchie copie del codice del portale"
for d in /opt/portale-sla.old* /opt/portale-sla-backup* /root/portale-sla* /home/*/portale-sla*; do
  [ -e "$d" ] || continue
  echo "Trovata: $d ($(dimensione "$d"))"
  if chiedi "Eliminarla?"; then rm -rf "$d" && echo -e "${GREEN}Eliminata${NC}"; fi
done
N=$(git -C /opt/portale-sla stash list 2>/dev/null | wc -l)
if [ "$N" -gt 0 ]; then
  echo "Modifiche locali messe da parte da sla-update: $N"
  if chiedi "Eliminarle? (servono solo se avevi modificato file a mano sul Pi)"; then git -C /opt/portale-sla stash clear; fi
fi

DOPO=$(df -h / | awk 'NR==2 {print $4}')
echo ""
echo -e "${GREEN}Pulizia finita. Spazio libero: prima $PRIMA, ora $DOPO${NC}"
