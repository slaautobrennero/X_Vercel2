# Portale SLA — PRD

## Original Problem
Portale gestionale "Sindacato Lavoratori Autostradali" (SLA) per 30 concessionarie autostradali. Sistema con 8 ruoli (SuperAdmin, SuperUser, Admin, Cassiere, Segretario, Segreteria, Delegato, Iscritto). Funzionalità: registrazione differenziata, rimborsi con calcolo KM via Google Maps, modulistica/documenti (max 5MB), bacheca/comunicati, notifiche, export PDF/Excel. Deploy locale Raspberry Pi 4 (DietPi) con Docker.

## Tech Stack
- Frontend: React + Tailwind + shadcn/ui
- Backend: FastAPI + MongoDB
- Deploy: Docker Compose su Raspberry Pi 4
- Hosting pubblico: Cloudflare Tunnel + dominio Aruba `portale-sla.it`
- Backup automatico: rclone → Google Drive (cron 03:00)
- Maps: Google Directions API

## Stato attuale
✅ Online su https://portale-sla.it via Cloudflare Tunnel (HTTPS)  
✅ Tunnel configurato come servizio systemd (auto-start)  
✅ Backup automatici GDrive  
✅ Login funzionante (SuperAdmin)

## Ruoli
- **SuperAdmin / SuperUser**: tutto, multi-sede
- **Admin**: gestione completa concessionaria (rimborsi, utenti, contatti, bacheca)
- **Cassiere** (NUOVO 28/04): come admin sui rimborsi (approva, paga, vede report)
- **Segretario**: gestione utenti, contatti, bacheca, documenti
- **Segreteria**: contatti, bacheca, documenti
- **Delegato**: solo creazione/visualizzazione propri rimborsi
- **Iscritto**: solo bacheca/documenti, niente rimborsi

## Modello dati chiave
- `users`: email, password_hash, ruolo, sede_id, nome, cognome, iban, indirizzo
- `sedi`: nome, codice, indirizzo, tariffa_km, rimborso_pasti, rimborso_autostrada
- `motivi_rimborso`: nome, richiede_note
- `rimborsi`: user_id, sede_id, data, motivo_id, km, importi, stato (in_attesa→approvato→pagato | rifiutato), contabile, ricevute_spese, pagato_by_nome
- `annunci`: titolo, contenuto, link_documento, allegato_filename, allegato_path, sede_id, autore
- `documenti`: nome, categoria, descrizione, filename, path, sede_id
- `notifiche`: user_id, sede_id, tipo, titolo, messaggio, letto
- `contatti` (NUOVO): titolo, descrizione, tipo (link|whatsapp|telegram|email|telefono), valore, sede_id

## Flusso Rimborsi (aggiornato 28/04)
```
Iscritto → "in_attesa" (BIANCO)
                ↓
Admin/Cassiere approva  → "approvato" (GIALLO) → carica contabile → "pagato" (VERDE)
Admin/Cassiere rifiuta  → "rifiutato" (ROSSO)
Admin/Cassiere paga diretto (con contabile) → "pagato" (VERDE)
```
- Contabile **obbligatoria** per arrivare a "pagato"
- Notifiche: nuovo rimborso → Admin + Cassiere; approvato/rifiutato → utente; pagato → utente + admin + cassiere

## Backlog prossime sessioni
1. Favicon SLA tab
2. Mostra valore contatto + copia
3. Reset password (admin/segretario)
4. Cancella + disattiva utente
5. Cambio password da Profilo
6. Password dimenticata via email
7. Storico azioni admin (audit log)
8. Filtri/ricerca rimborsi
9. Export PDF/Excel rendiconti
10. Email notifica rimborso pagato (no contabile)
11. Auto-logout 30 min
12. PWA installabile
13. Conferma email registrazione
14. GDPR (consenso + export + cancellazione)
15. Multi-allegati ricevute con anteprima
16. Promemoria rimborsi pendenti (>7gg)
17. Ricerca globale
18. Storico variazioni rimborsi

## Endpoint principali
- `/api/auth/login`, `/api/auth/register`, `/api/auth/logout`
- `/api/sedi`, `/api/motivi-rimborso`
- `/api/rimborsi` (GET/POST/PUT)
- `/api/rimborsi/{id}/contabile` (pagamento + upload obbligatorio)
- `/api/rimborsi/{id}/ricevute`, `/ricevute-spese`
- `/api/calcola-km` (Google Directions)
- `/api/annunci` (con allegato file), `/api/annunci/{id}/download`
- `/api/documenti` (upload), `/api/documenti/{id}/download`
- `/api/notifiche`
- `/api/contatti` (CRUD) — NUOVO
- `/api/users`, `/api/users/{id}/ruolo`
- `/api/reports/rimborsi-annuali`, `/rimborsi-export`
