# Portale SLA — PRD

## Original Problem
Portale gestionale "Sindacato Lavoratori Autostradali" (SLA) per 30 concessionarie autostradali. Sistema con 8 ruoli **multi-assegnabili** (SuperAdmin, SuperUser, Admin, Cassiere, Segretario, Segreteria, Delegato, Iscritto). Funzionalità: registrazione differenziata, rimborsi con calcolo KM via Google Maps, modulistica/documenti (max 5MB), bacheca/comunicati, notifiche, export PDF/Excel. Deploy locale Raspberry Pi 4 (DietPi) con Docker.

## Tech Stack
- Frontend: React + Tailwind + shadcn/ui
- Backend: FastAPI + MongoDB
- Deploy: Docker Compose su Raspberry Pi 4
- Hosting pubblico: Cloudflare Tunnel + dominio Aruba `portale-sla.it`
- Backup automatico: rclone → Google Drive (cron 03:00 DB / 03:15 uploads)
- Maps: Google Directions API

## Stato attuale
- ✅ Online su https://portale-sla.it via Cloudflare Tunnel (HTTPS)
- ✅ Backup MongoDB cifrati AES-256 + uploads + Google Drive sync verificati (30/05/2026)
- ✅ Multi-upload ricevute + Export PDF/Excel/CSV verificati
- ✅ **Multi-ruolo (31/05/2026)**: un utente può possedere PIÙ ruoli contemporaneamente (es. Admin+Cassiere, Delegato+Cassiere). Solo `Iscritto` resta single-role.

## Ruoli (permessi BASE — atomici)
| Ruolo | Crea rimborso | Approva/Rifiuta | Paga rimborso | Vede rimborsi |
|---|:---:|:---:|:---:|---|
| delegato | ✅ | ❌ | ❌ | Solo i suoi |
| segretario | ✅ | ❌ | ❌ | Della sua sede |
| segreteria | ✅ | ❌ | ❌ | Della sua sede |
| cassiere | ❌ | ❌ | ✅ | Della sua sede |
| admin | ✅ | ✅ | ✅ | Della sua sede |
| superadmin | ✅ | ✅ | ✅ | Tutte le sedi |
| superuser | ❌ | ❌ | ❌ | Tutte (read-only) |
| iscritto | ❌ | ❌ | ❌ | Nulla |

**Multi-ruolo**: l'utente eredita l'UNIONE dei permessi dei ruoli che possiede. Esempio: `["cassiere", "delegato"]` → può creare E pagare rimborsi.

## Modello dati chiave
- `users`: email, password_hash, **`ruolo`** (legacy, = ruoli[0]), **`ruoli: List[str]`** (sorgente di verità), sede_id, nome, cognome, iban, indirizzo, disabled, must_change_password
- `sedi`: nome, codice, indirizzo, tariffa_km, rimborso_pasti, rimborso_autostrada
- `motivi_rimborso`: nome, richiede_note
- `rimborsi`: user_id, sede_id, data, motivo_id, km, importi, stato (in_attesa→approvato→pagato | rifiutato), contabile, ricevute, ricevute_spese, pagato_by_nome
- `annunci`: titolo, contenuto, link_documento, allegato_filename, allegato_path, sede_id, autore
- `documenti`: nome, categoria, descrizione, filename, path, sede_id
- `notifiche`: user_id, sede_id, tipo, titolo, messaggio, letto
- `contatti`: titolo, descrizione, tipo (link|whatsapp|telegram|email|telefono), valore, sede_id
- `audit_log`: actor_name, action, target_type, target_label, old_value, new_value

## Flusso Rimborsi
```
Iscritto → "in_attesa" (BIANCO)
                ↓
Admin/Cassiere approva  → "approvato" (GIALLO) → carica contabile → "pagato" (VERDE)
Admin/Cassiere rifiuta  → "rifiutato" (ROSSO)
Admin/Cassiere paga diretto (con contabile) → "pagato" (VERDE)
```
- Contabile **obbligatoria** per arrivare a "pagato"
- Notifiche: nuovo rimborso → Admin + Cassiere; approvato/rifiutato → utente; pagato → utente + admin + cassiere

## Architettura Multi-Ruolo (31/05/2026)
**Backend**:
- Helper centralizzati: `user_has_role(user, "X")`, `user_has_any_role(user, [...])`, `_user_roles(user)`
- `_notify_users_by_role` query con `$or: [{ruolo: ...}, {ruoli: ...}]` (legacy + nuovo)
- Migrazione automatica su startup: utenti senza `ruoli` → `ruoli: [ruolo]`
- Endpoint `PUT /users/{id}/ruolo` accetta JSON `{ruoli: [...]}` (validato, dedup, iscritto-exclusive)
- Tutti i `user["ruolo"] in [...]` sostituiti con helper

**Frontend**:
- Helper `hasRole(user, role)`, `hasAnyRole(user, roles)`, `getUserRoles(user)` in `lib/utils.js`
- `RUOLO_BADGE_COLOR` mappa colori per badge per ruolo
- Sidebar mostra tutte le voci di menu in base all'unione dei ruoli
- `UtentiPage`: checkbox multipli con vincolo "iscritto esclusivo"
- Lista utenti / Profilo / Dashboard: visualizza tutti i ruoli come pillole separate

## Architettura backend (refactoring 08/06/2026)
```
backend/
├── server.py          (~2050 righe — routes + startup)
├── models_api.py      Pydantic models (User, Sede, Rimborso, ...)
├── core/
│   ├── config.py      env, paths, logger, CORS regex
│   ├── db.py          connessione MongoDB
│   ├── auth.py        JWT, password, get_current_user
│   ├── roles.py       multi-ruolo (helper, validazione)
│   ├── notifications.py  _notify_users_by_role/_user/_all_in_sede
│   ├── audit.py       _log_audit
│   └── scheduler.py   promemoria rimborsi >7gg (loop async)
├── routes/            (vuota, pronta per estrazione successiva)
└── server.py.bak      backup pre-refactoring
```
Le route HTTP sono ancora dentro `server.py` (estrazione completa pianificata in step successivo).
Tutti gli endpoint funzionano identici a prima (verified via curl).

## Sicurezza (10/06/2026)
- **MongoDB con autenticazione** username/password (configurato via `docker/.env`)
- **Security headers HTTP** (CSP, HSTS, X-Frame-Options, X-Content-Type-Options, Referrer-Policy, Permissions-Policy)
- **2FA TOTP** opzionale per admin/superadmin (compatibile Google Authenticator/Authy/1Password)
- **Backup MongoDB cifrati AES-256** (già esistente)
- **Rate limit login** 5 tentativi → lockout 15 min (già esistente)
- **JWT in cookie httpOnly + Secure + SameSite=None** (già esistente)
- **bcrypt** per password (già esistente)

## Backlog prossime sessioni
- 🟠 P1: Filtri avanzati rimborsi (date range, stato, utente, importo)
- 🟠 P1: Promemoria rimborsi pendenti >7gg (notifiche admin/cassieri)
- 🟡 P2: PWA installabile (manifest.json + service-worker già pronti)
- 🟡 P2: GDPR (consenso privacy, export dati personali, cancellazione)
- 🟡 P2: Email integration (Resend/SendGrid: forgot-password, conferma registrazione, notifica pagamento)
- 🔵 P3: Ricerca globale, Favicon SLA, Auto-logout 30 min
- 🔵 P3: Refactoring `server.py` (>2400 righe) in moduli `routes/`
- 🔵 P3: Fase 4 multi-ruolo — rimozione campo legacy `ruolo` quando tutto stabile

## Endpoint principali
- `/api/auth/login`, `/api/auth/register`, `/api/auth/logout`, `/api/auth/me`
- `/api/sedi`, `/api/motivi-rimborso`
- `/api/rimborsi` (GET/POST/PUT)
- `/api/rimborsi/{id}/contabile`, `/ricevute`, `/ricevute-multi`, `/ricevute-spese`
- `/api/calcola-km` (Google Directions)
- `/api/annunci` (con allegato file), `/api/annunci/{id}/download`
- `/api/documenti` (upload), `/api/documenti/{id}/download`
- `/api/notifiche`, `/api/contatti` (CRUD)
- `/api/users` (lista include `ruoli` array), `/api/users/{id}/ruolo` (PUT con `{ruoli: [...]}`)
- `/api/reports/rimborsi-annuali`, `/api/reports/rimborsi-export?formato=pdf|xlsx|csv`
- `/api/audit-log`
