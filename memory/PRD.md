# SLA - Portale Sindacato Lavoratori Autostradali

## Problem Statement
Sistema di Gestione Sindacale per 30 concessionarie autostradali (A22, CAV, Autostrade, ecc.). Ogni sede deve essere un compartimento stagno con isolamento dati completo.

## Architecture
- **Backend**: FastAPI + MongoDB
- **Frontend**: React + Tailwind CSS
- **Auth**: JWT con httpOnly cookies, protezione brute force
- **Database**: MongoDB con collezioni: users, sedi, rimborsi, annunci, documenti, notifiche, motivi_rimborso

## User Personas & Ruoli
| Ruolo | Bacheca | Documenti | Rimborsi | Gestione Rimborsi | Gestione Sede |
|-------|---------|-----------|----------|-------------------|---------------|
| Iscritto | ✅ Legge | ✅ Scarica | ❌ | ❌ | ❌ |
| Delegato | ✅ Legge | ✅ Scarica | ✅ Inserisce | ❌ | ❌ |
| Segreteria | ✅ Legge/Scrive | ✅ Carica | ✅ Inserisce | ❌ | ❌ |
| Segretario | ✅ Legge/Scrive | ✅ Carica | ✅ Inserisce | ⚠️ Sua sede | ⚠️ Sua sede |
| Admin | ✅ Tutto | ✅ Tutto | ✅ Tutto | ✅ Sua sede | ✅ Sua sede |
| SuperUser | ✅ Legge tutto | ✅ Legge tutto | ✅ Legge tutto | ❌ | ❌ |
| SuperAdmin | ✅ Tutto | ✅ Tutto | ✅ Tutto | ✅ Tutte | ✅ Tutte |

## Core Requirements
1. ✅ Registrazione multi-ruolo con dati personali (email, telefono, IBAN, indirizzo)
2. ✅ Isolamento dati per sede (compartimento stagno)
3. ✅ Gestione Rimborsi con calcolo automatico (KM, pasti, autostrada)
4. ✅ Bulletin Board per annunci
5. ✅ Modulistica e Documenti (upload PDF/JPG, max 5MB)
6. ✅ Notifiche in-app
7. ✅ Configurazione tariffe per sede

## What's Been Implemented (04/01/2026)
### Backend
- ✅ Auth JWT completa (login, register, logout, refresh)
- ✅ CRUD Sedi con tariffe personalizzate
- ✅ CRUD Rimborsi con calcolo automatico importi
- ✅ Upload ricevute e contabili
- ✅ CRUD Annunci (Bacheca)
- ✅ CRUD Documenti con categorizzazione
- ✅ Sistema Notifiche
- ✅ Gestione Utenti con cambio ruolo
- ✅ Report rimborsi annuali

### Frontend
- ✅ Login/Register con branding SLA
- ✅ Dashboard con statistiche
- ✅ Pagina Bacheca
- ✅ Pagina Documenti con filtri categoria
- ✅ Pagina Rimborsi con form completo
- ✅ Pagina Notifiche
- ✅ Pagina Utenti (admin)
- ✅ Pagina Sedi (superadmin)
- ✅ Pagina Profilo

## Sedi Pre-caricate
- A22 - Autostrada del Brennero (€0.35/km, €15 pasti)
- CAV - Concessioni Autostradali Venete (€0.30/km, €12 pasti)
- ASPI - Autostrade per l'Italia (€0.40/km, €18 pasti)

## Backlog P0/P1/P2
### P0 (Critico)
- Nessuno

### P1 (Importante)
- [ ] Export CSV/Excel rendiconti annuali
- [ ] Filtro rimborsi per periodo
- [ ] Gestione motivi rimborso da UI

### P2 (Nice to have)
- [ ] Dashboard con grafici (Recharts)
- [ ] Notifiche push/email
- [ ] Storico modifiche rimborsi
- [ ] Multi-lingua

## Next Tasks
1. Aggiungere altre 27 sedi concessionarie
2. Test con utenti reali di diverse sedi
3. Export rendiconti in PDF/Excel
