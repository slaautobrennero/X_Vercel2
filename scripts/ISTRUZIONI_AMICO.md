# 📦 Deploy Portale SLA — Istruzioni per l'amico

Ciao! Devi aiutare a deployare 3 piccoli aggiornamenti sul Raspberry Pi del portale.
Tutto è già pronto su GitHub, devi solo eseguire i comandi qui sotto.

## 🔌 Step 1 — Connettiti al Pi
Dovrebbe esserci una password che ti è stata fornita.

```bash
ssh root@<ip-del-pi-locale>     # es. 192.168.1.100
# oppure se DietPi ha un hostname:
ssh root@dietpi
```

Una volta dentro, vai nella cartella del progetto:
```bash
cd /opt/portale-sla
```

## 🌐 Step 2 — Configura Tailscale (opzionale ma molto utile)
Questo serve così in futuro il proprietario potrà accedere al Pi da fuori casa.

```bash
sudo bash /opt/portale-sla/scripts/setup_tailscale.sh
```

Lo script ti farà vedere un **link** tipo `https://login.tailscale.com/a/abc123`.
**Copialo e mandalo via WhatsApp/SMS al proprietario** così lui può fare login col suo account Google.

> Se non funziona o non hai tempo, salta pure questo step e passa allo Step 3. Si può fare in un altro momento.

## 🚀 Step 3 — Deploy degli aggiornamenti (5 min)

```bash
cd /opt/portale-sla
git pull origin main
```

Dovresti vedere "Fast-forward" + lista di file modificati. Se vedi conflitti, fermati e chiedi al proprietario.

Poi rebuilda i container:
```bash
cd /opt/portale-sla/docker
docker compose build backend frontend
docker compose up -d
```

Il build può richiedere 5-10 minuti (è normale).

## ✅ Step 4 — Verifica che funzioni

```bash
sleep 5
docker logs sla-backend --tail 30
```

Devi vedere righe tipo:
```
Database inizializzato
Scheduler promemoria rimborsi avviato
Application startup complete.
```

Se vedi qualcosa di rosso/ERROR, **mandami screenshot al proprietario**.

Apri sul browser https://portale-sla.it e prova a fare login. Se entra, è tutto OK ✅

## 📞 Problemi
Se qualcosa va storto, fai screenshot dell'errore e mandalo al proprietario. **Non cancellare nulla**.

---

Grazie! 🙏
