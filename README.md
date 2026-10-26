# Portale SLA - CISAL (Sindacato Lavoratori Autostradali)

Portale gestionale per le sedi/concessionarie: rimborsi chilometrici, documenti in cartelle, bacheca e comunicati, registrazioni con approvazione, report, GDPR, Sede Nazionale, notifiche push ed email configurabili per sede.

- **Stack:** React + FastAPI + MongoDB, in Docker Compose su Raspberry Pi, pubblicato con Cloudflare Tunnel.
- **Installazione, aggiornamento, backup, ripristino:** [`docs/GUIDA_TECNICA.md`](docs/GUIDA_TECNICA.md)
- **Guide per gli utenti:** dentro il portale, voce *Guida*.

| Cartella | Contenuto |
|---|---|
| `backend/` | API FastAPI (`server.py`, `routes/`, `core/`), test in `backend/tests/` |
| `frontend/` | Interfaccia React |
| `docker/` | Dockerfile, `docker-compose.yml`, Nginx, `.env.example` |
| `scripts/` | Backup/ripristino cifrati, pulizia Docker, Tailscale |
| `brochure/` | Sorgente della brochure (genera i file in `frontend/public/brochure/`) |
