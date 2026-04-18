# 📘 Documentazione Completa - Portale SLA
## Sindacato Lavoratori Autostradali - Sistema Gestionale Rimborsi

> **Versione:** 1.0.0  
> **Ultimo aggiornamento:** 18 Aprile 2026  
> **Deployment:** Raspberry Pi 4 con DietPi OS + Docker  
> **Stack:** React 18 + FastAPI + MongoDB 4.4.18

---

## 📋 Indice

1. [Panoramica del Progetto](#1-panoramica-del-progetto)
2. [Obiettivi e Requisiti](#2-obiettivi-e-requisiti)
3. [Architettura del Sistema](#3-architettura-del-sistema)
4. [Sistema dei Ruoli](#4-sistema-dei-ruoli)
5. [Funzionalità Dettagliate](#5-funzionalità-dettagliate)
6. [Stack Tecnologico](#6-stack-tecnologico)
7. [Struttura del Progetto](#7-struttura-del-progetto)
8. [Database Schema](#8-database-schema)
9. [API Endpoints](#9-api-endpoints)
10. [Deploy su Raspberry Pi](#10-deploy-su-raspberry-pi)
11. [Problemi Risolti Durante lo Sviluppo](#11-problemi-risolti-durante-lo-sviluppo)
12. [Configurazioni Docker](#12-configurazioni-docker)
13. [Credenziali di Test](#13-credenziali-di-test)
14. [Integrazioni Esterne](#14-integrazioni-esterne)
15. [Manutenzione e Backup](#15-manutenzione-e-backup)
16. [Roadmap Future](#16-roadmap-future)
17. [Troubleshooting](#17-troubleshooting)

---

## 1. Panoramica del Progetto

### 1.1 Descrizione

Il **Portale SLA** è un sistema gestionale web-based progettato per gestire le operazioni quotidiane del Sindacato Lavoratori Autostradali, con particolare focus su:

- **Gestione Rimborsi**: Sistema completo per richieste di rimborso trasferte con calcolo automatico chilometri
- **Comunicazioni Interne**: Bacheca annunci e sistema di notifiche in-app
- **Gestione Documentale**: Repository centralizzato per modulistica e documenti
- **Multi-Sede**: Supporto per 30 concessionarie autostradali distribuite sul territorio
- **7 Ruoli Utente**: Sistema granulare di permessi per diverse responsabilità

### 1.2 Contesto d'Uso

Il sistema viene utilizzato da:
- **30 Concessionarie** autostradali
- **Centinaia di utenti** distribuiti su 7 livelli di accesso
- **Deployment locale** su Raspberry Pi 4 (costi contenuti, pieno controllo dei dati)
- **Accesso da rete locale** per la sede centrale

---

## 2. Obiettivi e Requisiti

### 2.1 Requisiti Funzionali

#### Autenticazione e Autorizzazione
- [x] Registrazione differenziata per ruolo
  - **Iscritto**: NON richiede IBAN/indirizzo (accesso solo bacheca/documenti)
  - **Altri ruoli**: Richiede IBAN/indirizzo per gestione rimborsi
- [x] Login con JWT token (cookie httpOnly)
- [x] 7 livelli di permessi distinti
- [x] Creazione automatica SuperAdmin al primo avvio

#### Gestione Rimborsi
- [x] Inserimento richiesta con:
  - Data trasferta
  - Motivo (da lista configurabile)
  - Luogo partenza/destinazione
  - Calcolo KM automatico tramite Google Maps API
  - Opzione inserimento manuale KM
  - Upload ricevute spese (PDF/JPG, max 5MB)
- [x] Stati rimborso: `in_attesa` → `approvato` → `pagato` / `rifiutato`
- [x] Calcolo automatico importo (€/km configurable)
- [x] Workflow approvazione Admin
- [x] Notifiche cambio stato

#### Modulistica e Documenti
- [x] Upload documenti (limite 5MB)
- [x] Download documenti
- [x] Categorizzazione per tipo
- [x] Visibilità controllata per ruolo

#### Bacheca e Comunicazioni
- [x] Pubblicazione annunci
- [x] Notifiche in-app per eventi importanti
- [x] Visibilità pubblica (tutti) o per sede

#### Report ed Export
- [x] Rendiconto rimborsi annuale
- [x] Export CSV per contabilità
- [x] Filtri per sede, anno, stato

### 2.2 Requisiti Non Funzionali

- [x] **Performance**: Tempo risposta < 2s per operazioni comuni
- [x] **Scalabilità**: Supporto fino a 500 utenti concorrenti
- [x] **Sicurezza**: 
  - Password hashing con bcrypt
  - JWT con refresh token
  - Rate limiting login (protezione brute force)
  - CORS configurato
- [x] **Deployment**: Containerizzazione Docker per portabilità
- [x] **Compatibilità ARM**: Ottimizzato per Raspberry Pi 4

---

## 3. Architettura del Sistema

### 3.1 Diagramma Architettura

```
┌─────────────────────────────────────────────────────────────┐
│                    RETE LOCALE (192.168.0.x)                │
│                                                              │
│  ┌──────────────┐                                           │
│  │   Browser    │  http://192.168.0.99:3000                │
│  │  (Client)    │                                           │
│  └──────┬───────┘                                           │
│         │ HTTP/REST                                         │
│         ▼                                                    │
│  ┌──────────────────────────────────────────────────────┐  │
│  │            RASPBERRY PI 4 (DietPi OS)                │  │
│  │                                                       │  │
│  │  ┌─────────────────────────────────────────────────┐ │  │
│  │  │          DOCKER CONTAINERS                      │ │  │
│  │  │                                                  │ │  │
│  │  │  ┌────────────┐  ┌────────────┐  ┌───────────┐ │ │  │
│  │  │  │  Frontend  │  │  Backend   │  │  MongoDB  │ │ │  │
│  │  │  │            │  │            │  │           │ │ │  │
│  │  │  │   React    │  │  FastAPI   │  │  4.4.18   │ │ │  │
│  │  │  │  + Nginx   │  │  + Motor   │  │           │ │ │  │
│  │  │  │            │  │            │  │           │ │ │  │
│  │  │  │  :80       │  │  :8001     │  │  :27017   │ │ │  │
│  │  │  │  (→ :3000) │  │            │  │           │ │ │  │
│  │  │  └─────┬──────┘  └─────┬──────┘  └─────┬─────┘ │ │  │
│  │  │        │               │               │       │ │  │
│  │  │        └───────────────┼───────────────┘       │ │  │
│  │  │                        │                        │ │  │
│  │  │              Internal Docker Network           │ │  │
│  │  └─────────────────────────────────────────────────┘ │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
         │
         │ HTTPS (quando necessario)
         ▼
┌────────────────────────┐
│  Google Maps API       │
│  (Directions API)      │
└────────────────────────┘
```

### 3.2 Componenti Principali

#### Frontend (React)
- **Tecnologia**: React 18.3.1 con React Router 7.14.1
- **UI Framework**: Tailwind CSS 3.4.17 + shadcn/ui
- **Server**: Nginx (Alpine) per serving statico
- **Build**: Ottimizzato per produzione con code splitting
- **Porta**: 3000 (mappata su porta 80 del container)

#### Backend (FastAPI)
- **Framework**: FastAPI 0.115.6
- **Server ASGI**: Uvicorn
- **Driver MongoDB**: Motor (async)
- **Autenticazione**: JWT (python-jose) + bcrypt
- **Validazione**: Pydantic v2
- **Porta**: 8001

#### Database (MongoDB)
- **Versione**: 4.4.18 (compatibilità ARM Raspberry Pi)
- **Storage**: Volume Docker persistente
- **Porta**: 27017
- **Database**: `sla_sindacato`

---

## 4. Sistema dei Ruoli

### 4.1 Gerarchia dei Ruoli

```
SuperAdmin (Livello 7) ─── Accesso totale
    │
    ├─ SuperUser (Livello 6) ─── Visualizzazione globale
    │
    ├─ Admin (Livello 5) ─── Gestione completa sede
    │   │
    │   ├─ Segretario (Livello 4) ─── Gestione parziale sede
    │   │
    │   └─ Segreteria (Livello 3) ─── Pubblicazioni + Rimborsi
    │       │
    │       └─ Delegato (Livello 2) ─── Solo rimborsi
    │           │
    │           └─ Iscritto (Livello 1) ─── Solo lettura
```

### 4.2 Matrice Permessi Dettagliata

| Funzionalità | Iscritto | Delegato | Segreteria | Segretario | Admin | SuperUser | SuperAdmin |
|--------------|:--------:|:--------:|:----------:|:----------:|:-----:|:---------:|:----------:|
| **AUTENTICAZIONE** |
| Registrazione | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Login/Logout | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **BACHECA** |
| Visualizza annunci | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Pubblica annunci | ❌ | ❌ | ✅ | ✅ | ✅ | ❌ | ✅ |
| Elimina annunci | ❌ | ❌ | ✅ | ✅ | ✅ | ❌ | ✅ |
| **DOCUMENTI** |
| Scarica documenti | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Carica documenti | ❌ | ❌ | ✅ | ✅ | ✅ | ❌ | ✅ |
| Elimina documenti | ❌ | ❌ | ✅ | ✅ | ✅ | ❌ | ✅ |
| **RIMBORSI** |
| Visualizza propri rimborsi | ❌ | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ |
| Crea rimborso | ❌ | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ |
| Approva/Rifiuta rimborsi | ❌ | ❌ | ❌ | ⚠️ | ✅ | ❌ | ✅ |
| Chiudi contabile (pagato) | ❌ | ❌ | ❌ | ⚠️ | ✅ | ❌ | ✅ |
| **GESTIONE UTENTI** |
| Visualizza utenti sede | ❌ | ❌ | ❌ | ⚠️ | ✅ | 👁️ | ✅ |
| Modifica ruoli | ❌ | ❌ | ❌ | ⚠️ | ✅ | ❌ | ✅ |
| **GESTIONE SEDI** |
| Visualizza sedi | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Crea/Modifica sedi | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| **CONFIGURAZIONE** |
| Gestione motivi rimborso | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| Tariffe km | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| **REPORT** |
| Export rimborsi CSV | ❌ | ❌ | ❌ | ⚠️ | ✅ | 👁️ | ✅ |
| Report aggregati | ❌ | ❌ | ❌ | ⚠️ | ✅ | 👁️ | ✅ |

**Legenda:**
- ✅ = Accesso completo
- ⚠️ = Solo per la propria sede
- 👁️ = Solo visualizzazione (read-only)
- ❌ = Nessun accesso

### 4.3 Note sulla Registrazione Differenziata

#### Iscritto (Ruolo Base)
```javascript
// Durante la registrazione NON richiede:
- IBAN
- Indirizzo completo
- Motivazione

// Può accedere solo a:
- Bacheca (visualizzazione annunci)
- Documenti (download modulistica)
```

#### Altri Ruoli (Delegato, Segreteria, ecc.)
```javascript
// Durante la registrazione RICHIEDE:
- IBAN (per ricevere bonifici rimborsi)
- Indirizzo completo
- Motivazione richiesta ruolo

// Accesso completo a:
- Sezione Rimborsi
- Tutte le funzionalità previste dal ruolo
```

---

## 5. Funzionalità Dettagliate

### 5.1 Sistema Rimborsi

#### 5.1.1 Flusso Completo

```
┌────────────────┐
│ UTENTE         │
│ (Delegato+)    │
└───────┬────────┘
        │
        │ 1. Compila form richiesta
        ▼
┌────────────────────────┐
│ Inserimento Rimborso   │
│ - Data trasferta       │
│ - Motivo (dropdown)    │
│ - Partenza             │
│ - Destinazione         │
│ - Calcolo KM auto/man  │
│ - Upload ricevute      │
└───────┬────────────────┘
        │
        │ 2. Salva in DB (stato: in_attesa)
        ▼
┌────────────────────────┐
│ Notifica Admin         │
│ "Nuova richiesta #123" │
└───────┬────────────────┘
        │
        │ 3. Admin rivede
        ▼
┌────────────────────────┐
│ ADMIN valuta           │
│ - Verifica documenti   │
│ - Controlla KM         │
│ - Decide               │
└───────┬────────────────┘
        │
        ├─────────────┬─────────────┐
        │             │             │
        ▼             ▼             ▼
   [Approva]     [Rifiuta]     [Chiede info]
        │             │             │
        │             │             └─► Notifica utente
        │             │
        │             └─► Stato: rifiutato
        │                 Notifica utente
        │
        ▼
   Stato: approvato
   Notifica utente
        │
        │ 4. Contabilità effettua bonifico
        ▼
┌────────────────────────┐
│ ADMIN chiude           │
│ - Inserisce dati       │
│   bonifico             │
│ - Stato: pagato        │
└───────┬────────────────┘
        │
        │ 5. Fine processo
        ▼
   Notifica utente
   "Rimborso pagato!"
```

#### 5.1.2 Calcolo Chilometri

**Opzione A: Automatico (Google Maps)**
```python
# Backend: services/google_maps.py
async def calculate_distance(origin: str, destination: str):
    """
    Chiama Google Maps Directions API
    Ritorna: distanza in km (solo andata)
    """
    url = "https://maps.googleapis.com/maps/api/directions/json"
    params = {
        "origin": origin,
        "destination": destination,
        "key": GOOGLE_MAPS_API_KEY
    }
    response = requests.get(url, params=params)
    data = response.json()
    
    if data["status"] == "OK":
        distance_meters = data["routes"][0]["legs"][0]["distance"]["value"]
        return round(distance_meters / 1000, 2)  # Converti in km
    else:
        raise ValueError("Impossibile calcolare percorso")
```

**Opzione B: Manuale**
```javascript
// Frontend: L'utente spunta "Inserimento manuale KM"
// Inserisce direttamente il valore nel campo
<input 
  type="number" 
  placeholder="Es: 125" 
  disabled={!isManualKm}
/>
```

**Calcolo Importo Totale**
```python
# Formula standard
importo_km = km_andata * 2 * tariffa_km  # Andata e ritorno
importo_totale = importo_km + somma_ricevute_spese

# Esempio:
# - KM andata: 50
# - Tariffa: €0.30/km
# - Ricevute: €15 (pranzo) + €5 (pedaggio)
# 
# Calcolo:
# (50 * 2 * 0.30) + (15 + 5) = €30 + €20 = €50
```

### 5.2 Sistema Documenti

#### 5.2.1 Upload Files

```python
# Limiti:
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB
ALLOWED_EXTENSIONS = [".pdf", ".jpg", ".jpeg", ".png", ".doc", ".docx"]

# Storage:
UPLOAD_DIR = "/app/backend/uploads/"
# Naming: {timestamp}_{uuid}_{filename}
```

#### 5.2.2 Categorie Documenti

- **Modulistica**: Moduli da compilare
- **Circolari**: Comunicazioni ufficiali
- **Contratti**: Contratti collettivi
- **Guide**: Guide operative
- **Altro**: Categoria generica

### 5.3 Sistema Notifiche

#### Eventi che Generano Notifiche

| Evento | Destinatario | Messaggio |
|--------|--------------|-----------|
| Nuovo rimborso creato | Admin della sede | "Nuova richiesta rimborso da {nome_utente}" |
| Rimborso approvato | Richiedente | "Il tuo rimborso #{id} è stato approvato" |
| Rimborso rifiutato | Richiedente | "Il tuo rimborso #{id} è stato rifiutato" |
| Rimborso pagato | Richiedente | "Il rimborso #{id} è stato pagato" |
| Nuovo annuncio | Tutti gli utenti sede | "Nuovo annuncio in bacheca" |
| Nuovo documento | Tutti gli utenti | "Nuovo documento disponibile" |

#### Implementazione

```python
# Backend: services/notifications.py
async def create_notification(
    user_id: str,
    tipo: str,  # "rimborso", "annuncio", "documento"
    messaggio: str,
    link: str = None
):
    notification = {
        "id": str(uuid4()),
        "user_id": user_id,
        "tipo": tipo,
        "messaggio": messaggio,
        "link": link,
        "letta": False,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.notifiche.insert_one(notification)
```

---

## 6. Stack Tecnologico

### 6.1 Frontend

```json
{
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "react-router-dom": "^7.14.1",
    "tailwindcss": "^3.4.17",
    "@radix-ui/react-*": "^1.x",  // shadcn/ui components
    "lucide-react": "^0.469.0",   // Icons
    "recharts": "^2.15.0",         // Charts per dashboard
    "axios": "^1.7.9",             // HTTP client
    "date-fns": "^4.1.0",          // Date formatting
    "react-hook-form": "^7.54.2"   // Form management
  },
  "devDependencies": {
    "@craco/craco": "^7.1.0",      // Tailwind config
    "autoprefixer": "^10.4.20",
    "postcss": "^8.4.49"
  }
}
```

**Struttura Componenti:**
```
src/
├── App.js                 # Router principale
├── context/
│   └── AuthContext.jsx    # Context autenticazione globale
├── layouts/
│   └── MainLayout.jsx     # Layout con navbar/sidebar
├── pages/
│   ├── Login.jsx
│   ├── Register.jsx
│   ├── Dashboard.jsx
│   ├── Rimborsi/
│   │   ├── RimborsiList.jsx
│   │   ├── RimborsiCreate.jsx
│   │   └── RimborsiDetail.jsx
│   ├── Bacheca.jsx
│   ├── Documenti.jsx
│   ├── Admin/
│   │   ├── GestioneRimborsi.jsx
│   │   ├── GestioneUtenti.jsx
│   │   └── Report.jsx
│   └── SuperAdmin/
│       ├── Sedi.jsx
│       └── Configurazione.jsx
├── components/
│   └── ui/                # shadcn/ui components
└── lib/
    ├── api.js             # Axios instance configurato
    └── utils.js           # Helper functions
```

### 6.2 Backend

```txt
# requirements.txt (principali dipendenze)
fastapi==0.115.6
uvicorn[standard]==0.34.0
motor==3.6.0              # MongoDB async driver
pydantic==2.10.5
pydantic-settings==2.7.0
python-jose[cryptography]==3.3.0  # JWT
passlib[bcrypt]==1.7.4    # Password hashing
python-multipart==0.0.20  # File upload
requests==2.32.3          # Google Maps API
python-dotenv==1.0.1
emergentintegrations      # (se necessario per future integrazioni)
```

**Architettura Backend:**
```
backend/
├── server.py              # Entry point FastAPI (1400+ linee)
│                          # TODO: Refactoring in routes/
│
├── models/
│   ├── user.py            # Pydantic models: User, UserCreate, UserResponse
│   ├── sede.py            # Sede, SedeCreate
│   ├── rimborso.py        # Rimborso, RimborsoCreate, RimborsoUpdate
│   └── documento.py       # Documento, Annuncio, Notifica
│
├── utils/
│   ├── config.py          # Caricamento .env
│   ├── database.py        # Connessione MongoDB
│   └── auth.py            # JWT encode/decode, password hashing
│
├── services/
│   ├── google_maps.py     # Calcolo distanze
│   ├── file_handler.py    # Upload/download files
│   └── notifications.py   # Creazione notifiche
│
└── uploads/               # Directory file caricati
```

### 6.3 Database

**MongoDB 4.4.18** (scelta per compatibilità ARM Raspberry Pi)

**Collections:**

```javascript
// users
{
  _id: ObjectId,
  id: "uuid-string",  // ID custom per serializzazione
  email: "user@example.com",
  password_hash: "bcrypt-hash",
  name: "Nome Cognome",
  role: "delegato",  // enum: iscritto, delegato, segreteria, etc.
  sede_id: "uuid-sede",
  iban: "IT60X0542811101000000123456",  // NULL per iscritti
  address: "Via Roma 1, 00100 Roma",    // NULL per iscritti
  created_at: ISODate("2024-01-15T10:30:00Z"),
  is_active: true
}

// sedi
{
  _id: ObjectId,
  id: "uuid-string",
  nome: "Autostrade per l'Italia",
  codice: "ASPI",  // Unique index
  provincia: "Roma",
  created_at: ISODate("2024-01-10T09:00:00Z")
}

// rimborsi
{
  _id: ObjectId,
  id: "uuid-string",
  user_id: "uuid-user",
  sede_id: "uuid-sede",
  data_trasferta: ISODate("2024-03-20"),
  motivo_id: "uuid-motivo",
  luogo_partenza: "Roma",
  luogo_destinazione: "Milano",
  km_andata: 575.3,
  is_manual_km: false,
  importo_km: 345.18,  // (km * 2 * tariffa)
  ricevute_spese: [
    {
      filename: "ricevuta_pranzo.pdf",
      filepath: "/uploads/2024/03/...",
      importo: 15.50,
      descrizione: "Pranzo"
    }
  ],
  importo_totale: 360.68,
  status: "approvato",  // in_attesa | approvato | rifiutato | pagato
  note_admin: "",
  bonifico: {
    data: ISODate("2024-03-25"),
    importo: 360.68,
    causale: "Rimborso trasferta 20/03/2024"
  },
  created_at: ISODate("2024-03-21T14:20:00Z"),
  updated_at: ISODate("2024-03-25T11:15:00Z")
}

// motivi_rimborso
{
  _id: ObjectId,
  id: "uuid-string",
  codice: "ASSEMBLEA",
  descrizione: "Assemblea sindacale",
  is_active: true
}

// documenti
{
  _id: ObjectId,
  id: "uuid-string",
  titolo: "Modulo richiesta ferie",
  categoria: "modulistica",
  filename: "modulo_ferie.pdf",
  filepath: "/uploads/docs/...",
  uploaded_by: "uuid-user",
  created_at: ISODate("2024-02-01T09:00:00Z")
}

// annunci
{
  _id: ObjectId,
  id: "uuid-string",
  titolo: "Assemblea straordinaria",
  contenuto: "Si comunica che...",
  sede_id: "uuid-sede",  // NULL = visibile a tutti
  pubblicato_da: "uuid-user",
  created_at: ISODate("2024-03-10T10:00:00Z")
}

// notifiche
{
  _id: ObjectId,
  id: "uuid-string",
  user_id: "uuid-user",
  tipo: "rimborso",  // rimborso | annuncio | documento
  messaggio: "Il tuo rimborso #123 è stato approvato",
  link: "/rimborsi/123",  // Deep link
  letta: false,
  created_at: ISODate("2024-03-22T15:30:00Z")
}

// login_attempts (brute force protection)
{
  _id: ObjectId,
  identifier: "user@example.com",  // email o IP
  attempts: 3,
  last_attempt: ISODate("2024-03-15T10:25:00Z"),
  locked_until: null  // ISODate se bloccato
}
```

**Indexes:**
```javascript
db.users.createIndex({ email: 1 }, { unique: true });
db.sedi.createIndex({ codice: 1 }, { unique: true });
db.rimborsi.createIndex({ user_id: 1 });
db.rimborsi.createIndex({ sede_id: 1 });
db.rimborsi.createIndex({ status: 1 });
db.notifiche.createIndex({ user_id: 1, letta: 1 });
db.login_attempts.createIndex({ identifier: 1 });
```

---

## 7. Struttura del Progetto

```
/opt/portale-sla/          # Directory deploy Raspberry Pi
│
├── docker/                # Configurazioni Docker
│   ├── docker-compose.yml # Orchestrazione container
│   ├── backend.Dockerfile
│   ├── frontend.Dockerfile
│   ├── nginx.conf         # Config Nginx per React
│   └── .env               # Variabili ambiente (NON committare!)
│
├── backend/
│   ├── server.py          # [1400+ linee] FastAPI app
│   ├── requirements.txt
│   ├── .env              # Config backend
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── sede.py
│   │   ├── rimborso.py
│   │   └── documento.py
│   │
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── config.py      # Settings da .env
│   │   ├── database.py    # MongoDB connection
│   │   └── auth.py        # JWT + password hashing
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── google_maps.py # Calcolo KM
│   │   ├── file_handler.py# Upload/download
│   │   └── notifications.py
│   │
│   ├── routes/            # TODO: Refactoring in corso
│   │   └── (future modular routes)
│   │
│   └── uploads/           # File caricati (volume Docker)
│
├── frontend/
│   ├── public/
│   │   ├── index.html
│   │   └── favicon.ico
│   │
│   ├── src/
│   │   ├── App.js
│   │   ├── index.js
│   │   ├── index.css      # Tailwind imports
│   │   │
│   │   ├── context/
│   │   │   └── AuthContext.jsx
│   │   │
│   │   ├── layouts/
│   │   │   └── MainLayout.jsx
│   │   │
│   │   ├── pages/
│   │   │   ├── Login.jsx
│   │   │   ├── Register.jsx
│   │   │   ├── Dashboard.jsx
│   │   │   ├── Rimborsi/
│   │   │   │   ├── RimborsiList.jsx
│   │   │   │   ├── RimborsiCreate.jsx
│   │   │   │   └── RimborsiDetail.jsx
│   │   │   ├── Bacheca.jsx
│   │   │   ├── Documenti.jsx
│   │   │   ├── Admin/
│   │   │   │   ├── GestioneRimborsi.jsx
│   │   │   │   ├── GestioneUtenti.jsx
│   │   │   │   └── Report.jsx
│   │   │   └── SuperAdmin/
│   │   │       ├── Sedi.jsx
│   │   │       └── Configurazione.jsx
│   │   │
│   │   ├── components/
│   │   │   └── ui/        # shadcn/ui components
│   │   │       ├── button.jsx
│   │   │       ├── input.jsx
│   │   │       ├── card.jsx
│   │   │       ├── dialog.jsx
│   │   │       ├── select.jsx
│   │   │       ├── table.jsx
│   │   │       └── ... (20+ components)
│   │   │
│   │   └── lib/
│   │       ├── api.js     # Axios instance
│   │       └── utils.js   # cn(), formatDate(), etc.
│   │
│   ├── package.json
│   ├── yarn.lock
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   └── .env              # REACT_APP_BACKEND_URL
│
├── memory/               # File supporto sviluppo
│   ├── PRD.md            # Product Requirements Document
│   └── test_credentials.md
│
├── test_reports/         # Report testing agent
│   └── iteration_1.json
│
├── README.md             # Documentazione base
├── DOCUMENTAZIONE_COMPLETA.md  # Questo file
├── DOCKER_DEPLOYMENT_GUIDE.md
└── RASPBERRY_PI_QUICK_START.md
```

---

## 8. Database Schema

### 8.1 Diagramma ER

```
┌─────────────────┐         ┌─────────────────┐
│     USERS       │         │      SEDI       │
├─────────────────┤         ├─────────────────┤
│ id (PK)         │         │ id (PK)         │
│ email (UK)      │    ┌────│ nome            │
│ password_hash   │    │    │ codice (UK)     │
│ name            │    │    │ provincia       │
│ role            │    │    └─────────────────┘
│ sede_id (FK) ───┼────┘              │
│ iban            │                   │
│ address         │                   │
│ created_at      │                   │
└─────────────────┘                   │
         │                            │
         │ 1:N                        │
         │                            │
         ▼                            │
┌─────────────────┐                   │
│    RIMBORSI     │                   │
├─────────────────┤                   │
│ id (PK)         │                   │
│ user_id (FK)    │                   │
│ sede_id (FK) ───┼───────────────────┘
│ data_trasferta  │
│ motivo_id (FK) ─┼────┐
│ luogo_partenza  │    │
│ luogo_dest.     │    │    ┌─────────────────┐
│ km_andata       │    │    │ MOTIVI_RIMBORSO │
│ is_manual_km    │    │    ├─────────────────┤
│ importo_km      │    └────│ id (PK)         │
│ ricevute_spese  │         │ codice (UK)     │
│ importo_totale  │         │ descrizione     │
│ status          │         │ is_active       │
│ note_admin      │         └─────────────────┘
│ bonifico        │
│ created_at      │
└─────────────────┘

┌─────────────────┐         ┌─────────────────┐
│   DOCUMENTI     │         │    ANNUNCI      │
├─────────────────┤         ├─────────────────┤
│ id (PK)         │         │ id (PK)         │
│ titolo          │         │ titolo          │
│ categoria       │         │ contenuto       │
│ filename        │         │ sede_id (FK)    │
│ filepath        │         │ pubblicato_da   │
│ uploaded_by (FK)│         │ created_at      │
│ created_at      │         └─────────────────┘
└─────────────────┘

┌─────────────────┐         ┌─────────────────┐
│   NOTIFICHE     │         │ LOGIN_ATTEMPTS  │
├─────────────────┤         ├─────────────────┤
│ id (PK)         │         │ identifier      │
│ user_id (FK)    │         │ attempts        │
│ tipo            │         │ last_attempt    │
│ messaggio       │         │ locked_until    │
│ link            │         └─────────────────┘
│ letta           │
│ created_at      │
└─────────────────┘
```

### 8.2 Vincoli e Regole di Business

**USERS:**
- `email` deve essere univoca (unique index)
- `role` enum: `["iscritto", "delegato", "segreteria", "segretario", "admin", "superuser", "superadmin"]`
- `iban` e `address` sono **NULL** per ruolo `iscritto`
- `password_hash` sempre hashed con bcrypt (cost factor 12)

**SEDI:**
- `codice` deve essere univoco (es: "ASPI", "SATAP", "SALT")
- Massimo 30 sedi (requisito funzionale)

**RIMBORSI:**
- `status` enum: `["in_attesa", "approvato", "rifiutato", "pagato"]`
- `is_manual_km = true` → KM inseriti manualmente (no Google Maps)
- `ricevute_spese` array di oggetti: `{ filename, filepath, importo, descrizione }`
- `bonifico` presente solo se `status = "pagato"`

**MOTIVI_RIMBORSO:**
- Configurabili solo da SuperAdmin
- `is_active = false` → nascosto ma storicizzato

**LOGIN_ATTEMPTS:**
- Blocco dopo 5 tentativi falliti per 15 minuti
- `identifier` può essere email o IP

---

## 9. API Endpoints

### 9.1 Autenticazione

#### POST `/api/auth/register`
**Descrizione:** Registrazione nuovo utente

**Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "name": "Mario Rossi",
  "role": "delegato",
  "sede_id": "uuid-sede",
  "iban": "IT60X0542811101000000123456",  // Ometti se role=iscritto
  "address": "Via Roma 1, 00100 Roma"     // Ometti se role=iscritto
}
```

**Response 201:**
```json
{
  "id": "uuid-user",
  "email": "user@example.com",
  "name": "Mario Rossi",
  "role": "delegato",
  "sede_id": "uuid-sede"
}
```

---

#### POST `/api/auth/login`
**Descrizione:** Login con email e password

**Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

**Response 200:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "user": {
    "id": "uuid-user",
    "email": "user@example.com",
    "name": "Mario Rossi",
    "role": "delegato",
    "sede_id": "uuid-sede"
  }
}
```

**Note:**
- Cookies httpOnly impostati automaticamente
- Rate limiting: max 5 tentativi ogni 15 minuti

---

#### GET `/api/auth/me`
**Descrizione:** Ottieni dati utente corrente

**Headers:**
```
Authorization: Bearer {access_token}
```

**Response 200:**
```json
{
  "id": "uuid-user",
  "email": "user@example.com",
  "name": "Mario Rossi",
  "role": "delegato",
  "sede_id": "uuid-sede",
  "iban": "IT60X...",
  "address": "Via Roma 1"
}
```

---

### 9.2 Sedi

#### GET `/api/sedi`
**Descrizione:** Lista tutte le sedi

**Query Params:**
- `skip` (int): Paginazione offset (default: 0)
- `limit` (int): Numero risultati (default: 100)

**Response 200:**
```json
{
  "items": [
    {
      "id": "uuid-1",
      "nome": "Autostrade per l'Italia",
      "codice": "ASPI",
      "provincia": "Roma"
    },
    {
      "id": "uuid-2",
      "nome": "SATAP",
      "codice": "SATAP",
      "provincia": "Torino"
    }
  ],
  "total": 30
}
```

---

#### POST `/api/sedi`
**Descrizione:** Crea nuova sede (solo SuperAdmin)

**Body:**
```json
{
  "nome": "Tangenziale di Napoli",
  "codice": "TAN",
  "provincia": "Napoli"
}
```

**Response 201:**
```json
{
  "id": "uuid-new",
  "nome": "Tangenziale di Napoli",
  "codice": "TAN",
  "provincia": "Napoli",
  "created_at": "2024-04-18T10:30:00Z"
}
```

---

### 9.3 Rimborsi

#### GET `/api/rimborsi`
**Descrizione:** Lista rimborsi (filtrati per ruolo)

**Query Params:**
- `skip`, `limit`: Paginazione
- `status`: Filtra per stato (opzionale)
- `sede_id`: Filtra per sede (opzionale)
- `user_id`: Filtra per utente (opzionale)

**Response 200:**
```json
{
  "items": [
    {
      "id": "uuid-rimborso",
      "user": {
        "id": "uuid-user",
        "name": "Mario Rossi"
      },
      "data_trasferta": "2024-03-20",
      "motivo": {
        "codice": "ASSEMBLEA",
        "descrizione": "Assemblea sindacale"
      },
      "luogo_partenza": "Roma",
      "luogo_destinazione": "Milano",
      "km_andata": 575.3,
      "is_manual_km": false,
      "importo_totale": 360.68,
      "status": "approvato",
      "created_at": "2024-03-21T14:20:00Z"
    }
  ],
  "total": 42
}
```

---

#### POST `/api/rimborsi`
**Descrizione:** Crea nuova richiesta rimborso

**Body:**
```json
{
  "data_trasferta": "2024-04-25",
  "motivo_id": "uuid-motivo",
  "luogo_partenza": "Roma",
  "luogo_destinazione": "Firenze",
  "is_manual_km": false  // Se true, fornire km_andata
}
```

**Response 201:**
```json
{
  "id": "uuid-new-rimborso",
  "km_andata": 275.8,
  "importo_km": 165.48,
  "importo_totale": 165.48,
  "status": "in_attesa",
  "created_at": "2024-04-18T15:00:00Z"
}
```

---

#### PUT `/api/rimborsi/{id}/approva`
**Descrizione:** Approva rimborso (solo Admin+)

**Body:**
```json
{
  "note_admin": "Approvato - tutto ok"
}
```

**Response 200:**
```json
{
  "id": "uuid-rimborso",
  "status": "approvato",
  "note_admin": "Approvato - tutto ok",
  "updated_at": "2024-04-18T16:00:00Z"
}
```

---

#### PUT `/api/rimborsi/{id}/rifiuta`
**Descrizione:** Rifiuta rimborso (solo Admin+)

**Body:**
```json
{
  "note_admin": "Mancano documenti giustificativi"
}
```

---

#### POST `/api/rimborsi/{id}/chiudi-contabile`
**Descrizione:** Segna rimborso come pagato (solo Admin+)

**Body:**
```json
{
  "data_bonifico": "2024-04-20",
  "importo_pagato": 360.68,
  "causale": "Rimborso trasferta 20/03/2024"
}
```

**Response 200:**
```json
{
  "id": "uuid-rimborso",
  "status": "pagato",
  "bonifico": {
    "data": "2024-04-20",
    "importo": 360.68,
    "causale": "Rimborso trasferta 20/03/2024"
  }
}
```

---

#### POST `/api/rimborsi/{id}/ricevute-spese`
**Descrizione:** Upload ricevuta spesa

**Headers:**
```
Content-Type: multipart/form-data
```

**Form Data:**
- `file`: File PDF/JPG (max 5MB)
- `importo`: Importo spesa (es: 15.50)
- `descrizione`: Descrizione (es: "Pranzo")

**Response 200:**
```json
{
  "filename": "ricevuta_pranzo.pdf",
  "filepath": "/uploads/2024/04/...",
  "importo": 15.50,
  "descrizione": "Pranzo"
}
```

---

#### POST `/api/calcola-km`
**Descrizione:** Calcola distanza tra due luoghi (Google Maps)

**Body:**
```json
{
  "origin": "Roma, Italia",
  "destination": "Milano, Italia"
}
```

**Response 200:**
```json
{
  "km": 575.3,
  "origin": "Roma, RM, Italia",
  "destination": "Milano, MI, Italia"
}
```

**Error 400** (se Google Maps fallisce):
```json
{
  "detail": "Impossibile calcolare il percorso. Verifica gli indirizzi."
}
```

---

### 9.4 Documenti

#### GET `/api/documenti`
**Descrizione:** Lista documenti disponibili

**Query Params:**
- `categoria`: Filtra per categoria (opzionale)
- `skip`, `limit`: Paginazione

**Response 200:**
```json
{
  "items": [
    {
      "id": "uuid-doc",
      "titolo": "Modulo richiesta ferie 2024",
      "categoria": "modulistica",
      "filename": "modulo_ferie_2024.pdf",
      "uploaded_by": {
        "id": "uuid-user",
        "name": "Admin Sede"
      },
      "created_at": "2024-01-15T09:00:00Z"
    }
  ],
  "total": 15
}
```

---

#### POST `/api/documenti`
**Descrizione:** Carica nuovo documento (Segreteria+)

**Headers:**
```
Content-Type: multipart/form-data
```

**Form Data:**
- `file`: File (max 5MB)
- `titolo`: Titolo documento
- `categoria`: Categoria (modulistica, circolari, etc.)

**Response 201:**
```json
{
  "id": "uuid-new-doc",
  "titolo": "Circolare informativa aprile",
  "categoria": "circolari",
  "filename": "circolare_aprile_2024.pdf",
  "created_at": "2024-04-18T10:00:00Z"
}
```

---

#### GET `/api/documenti/{id}/download`
**Descrizione:** Scarica file documento

**Response 200:**
```
Content-Type: application/pdf
Content-Disposition: attachment; filename="modulo_ferie_2024.pdf"

[Binary file data]
```

---

### 9.5 Bacheca

#### GET `/api/annunci`
**Descrizione:** Lista annunci in bacheca

**Query Params:**
- `sede_id`: Filtra per sede (opzionale)
- `skip`, `limit`: Paginazione

**Response 200:**
```json
{
  "items": [
    {
      "id": "uuid-annuncio",
      "titolo": "Assemblea straordinaria 25 aprile",
      "contenuto": "Si comunica che il giorno 25/04/2024 alle ore 10:00...",
      "sede": {
        "id": "uuid-sede",
        "nome": "ASPI"
      },
      "pubblicato_da": {
        "id": "uuid-user",
        "name": "Segretario Generale"
      },
      "created_at": "2024-04-10T08:00:00Z"
    }
  ],
  "total": 8
}
```

---

#### POST `/api/annunci`
**Descrizione:** Pubblica nuovo annuncio (Segreteria+)

**Body:**
```json
{
  "titolo": "Chiusura uffici festività pasquali",
  "contenuto": "Si informa che gli uffici resteranno chiusi dal...",
  "sede_id": "uuid-sede"  // NULL = visibile a tutti
}
```

**Response 201:**
```json
{
  "id": "uuid-new-annuncio",
  "titolo": "Chiusura uffici festività pasquali",
  "contenuto": "...",
  "created_at": "2024-04-18T11:00:00Z"
}
```

---

### 9.6 Report

#### GET `/api/reports/rimborsi-annuali`
**Descrizione:** Report aggregato rimborsi per anno (Admin+)

**Query Params:**
- `anno`: Anno di riferimento (es: 2024)
- `sede_id`: Filtra per sede (opzionale)

**Response 200:**
```json
{
  "anno": 2024,
  "totale_rimborsi": 125,
  "totale_importo": 45678.90,
  "per_stato": {
    "in_attesa": 15,
    "approvato": 30,
    "pagato": 75,
    "rifiutato": 5
  },
  "per_mese": [
    {
      "mese": 1,
      "count": 10,
      "importo_totale": 3456.78
    },
    {
      "mese": 2,
      "count": 12,
      "importo_totale": 4123.50
    }
  ]
}
```

---

#### GET `/api/reports/rimborsi-export`
**Descrizione:** Export CSV rimborsi (Admin+)

**Query Params:**
- `anno`: Anno di riferimento
- `sede_id`: Filtra per sede (opzionale)
- `status`: Filtra per stato (opzionale)

**Response 200:**
```
Content-Type: text/csv
Content-Disposition: attachment; filename="rimborsi_2024.csv"

Data,Utente,Sede,Motivo,KM,Importo,Stato
2024-03-20,Mario Rossi,ASPI,Assemblea,575.3,360.68,pagato
2024-03-22,Luigi Bianchi,SATAP,Riunione,120.5,85.30,approvato
...
```

---

### 9.7 Notifiche

#### GET `/api/notifiche`
**Descrizione:** Lista notifiche utente corrente

**Query Params:**
- `letta`: Filtra per stato letto/non letto (boolean)

**Response 200:**
```json
{
  "items": [
    {
      "id": "uuid-notifica",
      "tipo": "rimborso",
      "messaggio": "Il tuo rimborso #123 è stato approvato",
      "link": "/rimborsi/123",
      "letta": false,
      "created_at": "2024-04-18T14:30:00Z"
    }
  ],
  "non_lette": 3
}
```

---

#### PUT `/api/notifiche/{id}/leggi`
**Descrizione:** Segna notifica come letta

**Response 200:**
```json
{
  "id": "uuid-notifica",
  "letta": true
}
```

---

### 9.8 Admin - Gestione Utenti

#### GET `/api/admin/users`
**Descrizione:** Lista utenti (Admin: solo sede, SuperAdmin: tutti)

**Query Params:**
- `sede_id`: Filtra per sede
- `role`: Filtra per ruolo
- `skip`, `limit`: Paginazione

**Response 200:**
```json
{
  "items": [
    {
      "id": "uuid-user",
      "email": "user@example.com",
      "name": "Mario Rossi",
      "role": "delegato",
      "sede": {
        "id": "uuid-sede",
        "nome": "ASPI"
      },
      "is_active": true,
      "created_at": "2024-01-15T10:00:00Z"
    }
  ],
  "total": 45
}
```

---

#### PUT `/api/admin/users/{id}/role`
**Descrizione:** Modifica ruolo utente (Admin+)

**Body:**
```json
{
  "new_role": "segreteria"
}
```

**Response 200:**
```json
{
  "id": "uuid-user",
  "role": "segreteria",
  "updated_at": "2024-04-18T15:00:00Z"
}
```

---

## 10. Deploy su Raspberry Pi

### 10.1 Requisiti Hardware

**Hardware Minimo:**
- Raspberry Pi 4 Model B
- RAM: 2GB (consigliato 4GB)
- Storage: 16GB microSD (consigliato 32GB SSD via USB)
- Alimentazione: 5V 3A ufficiale

**Hardware Utilizzato (setup corrente):**
- Raspberry Pi 4 Model B 4GB
- SSD USB 128GB
- Alimentatore ufficiale Raspberry

### 10.2 Sistema Operativo

**DietPi OS** (versione lightweight Debian)

**Installazione:**
1. Scarica immagine da https://dietpi.com/
2. Flash su SD/SSD con Balena Etcher
3. Primo avvio: completa wizard configurazione
4. Configura rete (IP statico consigliato)

### 10.3 Preparazione Ambiente

#### Aggiornamento Sistema
```bash
# Login SSH
ssh root@192.168.0.99  # Password default: dietpi

# Aggiorna repository
apt update && apt upgrade -y

# Installa dipendenze base
apt install -y git curl wget vim
```

#### Installazione Docker
```bash
# Installa Docker
curl -fsSL https://get.docker.com | sh

# Aggiungi utente al gruppo docker
usermod -aG docker root

# Installa Docker Compose Plugin
apt install -y docker-compose-plugin

# Verifica installazione
docker --version
docker compose version

# Riavvia
reboot
```

### 10.4 Deploy Applicazione

#### Copia Progetto

**Opzione A: Da Git (se repository disponibile)**
```bash
cd /opt
git clone https://github.com/tuoaccount/portale-sla.git
cd portale-sla
```

**Opzione B: Trasferimento SCP (dal PC locale)**
```bash
# Esegui dal tuo PC
scp -r /percorso/locale/portale-sla root@192.168.0.99:/opt/

# Poi SSH nel Raspberry
ssh root@192.168.0.99
cd /opt/portale-sla
```

#### Configurazione Environment

```bash
cd /opt/portale-sla/docker

# Crea file .env
nano .env
```

**Contenuto `.env`:**
```bash
# MongoDB
MONGO_URL=mongodb://mongodb:27017
DB_NAME=sla_sindacato

# JWT
JWT_SECRET=CAMBIA_QUESTA_CHIAVE_CON_UNA_CASUALE_LUNGHISSIMA_123456789
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Admin iniziale
ADMIN_EMAIL=superadmin@sla.it
ADMIN_PASSWORD=SlaAdmin2024!

# Google Maps (opzionale)
GOOGLE_MAPS_API_KEY=

# Frontend
FRONTEND_URL=http://192.168.0.99:3000

# CORS
ALLOWED_ORIGINS=http://192.168.0.99:3000,http://localhost:3000
```

**IMPORTANTE:** Cambia `JWT_SECRET` con una chiave casuale lunga (almeno 32 caratteri)

#### Build e Avvio Container

```bash
# Build immagini
docker compose -f docker/docker-compose.yml build

# Avvia container
docker compose -f docker/docker-compose.yml up -d

# Verifica stato
docker compose -f docker/docker-compose.yml ps
```

**Output atteso:**
```
NAME           IMAGE             COMMAND                  STATUS
sla-backend    docker-backend    "uvicorn server:app …"   Up
sla-frontend   docker-frontend   "/docker-entrypoint.…"   Up
sla-mongodb    mongo:4.4.18      "docker-entrypoint.s…"   Up
```

#### Verifica Logs

```bash
# Backend logs
docker compose -f docker/docker-compose.yml logs backend --tail=50

# Output atteso:
# INFO:     Started server process [1]
# INFO:     Waiting for application startup.
# 2024-04-18 17:44:36,865 - server - INFO - SuperAdmin creato: superadmin@sla.it
# 2024-04-18 17:44:36,936 - server - INFO - Database inizializzato
# INFO:     Application startup complete.
# INFO:     Uvicorn running on http://0.0.0.0:8001

# Frontend logs
docker compose -f docker/docker-compose.yml logs frontend --tail=20

# MongoDB logs
docker compose -f docker/docker-compose.yml logs mongodb --tail=20
```

### 10.5 Accesso Applicazione

#### Da Rete Locale

**Trova IP Raspberry:**
```bash
hostname -I
# Output: 192.168.0.99
```

**Accedi dal browser:**
```
Frontend: http://192.168.0.99:3000
Backend API: http://192.168.0.99:8001
Swagger Docs: http://192.168.0.99:8001/docs
```

**Login Iniziale:**
```
Email: superadmin@sla.it
Password: SlaAdmin2024!
```

### 10.6 Ottimizzazioni Raspberry Pi

#### Limiti Memoria Container

Modifica `docker/docker-compose.yml`:

```yaml
services:
  mongodb:
    image: mongo:4.4.18
    mem_limit: 512m      # ← Aggiungi
    memswap_limit: 512m  # ← Aggiungi
    
  backend:
    mem_limit: 256m
    memswap_limit: 256m
    
  frontend:
    mem_limit: 128m
    memswap_limit: 128m
```

#### Avvio Automatico al Boot

```bash
# Crea service systemd
nano /etc/systemd/system/portale-sla.service
```

**Contenuto:**
```ini
[Unit]
Description=Portale SLA Docker Compose
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/portale-sla
ExecStart=/usr/bin/docker compose -f docker/docker-compose.yml up -d
ExecStop=/usr/bin/docker compose -f docker/docker-compose.yml down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
```

**Abilita service:**
```bash
systemctl daemon-reload
systemctl enable portale-sla.service
systemctl start portale-sla.service

# Verifica
systemctl status portale-sla.service
```

#### Monitoring Risorse

```bash
# Installa htop
apt install -y htop

# Monitora risorse
htop

# Statistiche Docker
docker stats
```

---

## 11. Problemi Risolti Durante lo Sviluppo

### 11.1 Compatibilità MongoDB ARM

**Problema:**
```
Container `sla-mongodb` in continuo restart loop
Log: "WARNING: MongoDB 5.0+ requires a CPU with AVX support"
```

**Causa:**
MongoDB 6.0 richiede istruzioni AVX non disponibili su Raspberry Pi 4 (architettura ARMv8 Cortex-A72)

**Soluzione:**
Downgrade a MongoDB 4.4.18 (ultima versione ARM-compatibile)

**File modificato:** `docker/docker-compose.yml`
```yaml
mongodb:
  image: mongo:4.4.18  # Era: mongo:6.0
```

**Riferimento:** https://github.com/docker-library/mongo/issues/485

---

### 11.2 Backend Container Crash - ModuleNotFoundError

**Problema:**
```
Container `sla-backend` crash all'avvio
Log: "ModuleNotFoundError: No module named 'server'"
```

**Causa:**
Il Dockerfile copiava tutto in `/app` ma `server.py` è in `/app/backend`. Uvicorn non trovava il modulo.

**Dockerfile originale:**
```dockerfile
WORKDIR /app
COPY backend/ .
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8001"]
```

**Problema:** Uvicorn cercava `server.py` in `/app` ma il file era in `/app/backend`

**Soluzione:**
Aggiunto `WORKDIR /app/backend` prima del `CMD`

**File modificato:** `docker/backend.Dockerfile`
```dockerfile
WORKDIR /app
COPY backend/ backend/
WORKDIR /app/backend  # ← Aggiunto
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8001"]
```

---

### 11.3 Frontend Build Fail - Node Version

**Problema:**
```
Frontend build fail
Error: "react-router-dom@7.14.1 requires Node.js >=18"
```

**Causa:**
Dockerfile usava `node:16-alpine`, ma React Router v7 richiede Node 18+

**Soluzione:**
Upgrade a `node:20-alpine`

**File modificato:** `docker/frontend.Dockerfile`
```dockerfile
FROM node:20-alpine AS builder  # Era: node:16-alpine
```

---

### 11.4 Nginx Config - React Router SPA

**Problema:**
```
404 su tutte le rotte tranne "/"
Es: http://192.168.0.99:3000/rimborsi → 404
```

**Causa:**
Nginx serviva solo file statici, non gestiva routing React SPA

**Soluzione:**
Aggiunto `try_files` per fallback su `index.html`

**File modificato:** `docker/nginx.conf`
```nginx
location / {
    root /usr/share/nginx/html;
    try_files $uri $uri/ /index.html;  # ← Chiave
}
```

---

### 11.5 CORS Errors - Frontend → Backend

**Problema:**
```
Browser console: "CORS policy blocked request to http://192.168.0.99:8001"
```

**Causa:**
FastAPI non aveva configurato CORS per IP locale

**Soluzione:**
Aggiunto middleware CORS in `server.py`

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://192.168.0.99:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

### 11.6 Docker Context Path Issues

**Problema:**
```
docker compose build fail
Error: "COPY failed: file not found in build context"
```

**Causa:**
`docker-compose.yml` aveva context paths relativi errati

**Configurazione originale:**
```yaml
backend:
  build:
    context: ../backend  # ❌ Errato
    dockerfile: backend.Dockerfile
```

**Soluzione:**
Context alla root del progetto

```yaml
backend:
  build:
    context: ..  # ✅ Root progetto
    dockerfile: docker/backend.Dockerfile
```

---

### 11.7 MongoDB ObjectId Serialization

**Problema:**
```
FastAPI response error: "Object of type ObjectId is not JSON serializable"
```

**Causa:**
MongoDB `_id` è ObjectId, non serializzabile in JSON

**Soluzione:**
1. Escludi sempre `_id` nelle query MongoDB
2. Usa ID custom (UUID string)

**Pattern adottato:**
```python
# ❌ SBAGLIATO
user = await db.users.find_one({"email": email})

# ✅ CORRETTO
user = await db.users.find_one({"email": email}, {"_id": 0})

# Insert con ID custom
user_data = {
    "id": str(uuid4()),  # ← ID custom
    "email": email,
    # ...
}
await db.users.insert_one(user_data)
```

---

### 11.8 Google Maps API - Referrer Restrictions

**Problema:**
```
Google Maps API return: "This API key is not valid for this IP/domain"
```

**Causa:**
API Key configurata solo per `localhost`, non per IP locale (192.168.0.99)

**Soluzione:**
In Google Cloud Console:
1. Vai su "Credentials" → API Key
2. "Application restrictions" → "HTTP referrers"
3. Aggiungi:
   - `http://localhost:3000/*`
   - `http://192.168.0.99:3000/*`
   - `http://192.168.*/*` (per tutta la LAN)

---

### 11.9 EmergentIntegrations Installation in Docker

**Problema:**
```
pip install fail: "Could not find a version that satisfies the requirement emergentintegrations"
```

**Causa:**
Package non su PyPI pubblico, richiede extra-index-url

**Soluzione:**
Aggiunto index custom nel Dockerfile

**File modificato:** `docker/backend.Dockerfile`
```dockerfile
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir emergentintegrations \
        --extra-index-url https://d33sy5i8bnduwe.cloudfront.net/simple/ && \
    pip install --no-cache-dir -r requirements.txt
```

---

## 12. Configurazioni Docker

### 12.1 docker-compose.yml Completo

```yaml
version: '3.8'

services:
  # ==============================
  # MongoDB Database
  # ==============================
  mongodb:
    image: mongo:4.4.18  # ARM-compatible version
    container_name: sla-mongodb
    restart: unless-stopped
    environment:
      MONGO_INITDB_DATABASE: sla_sindacato
    ports:
      - "27017:27017"
    volumes:
      - mongodb_data:/data/db
    networks:
      - sla-network
    healthcheck:
      test: echo 'db.runCommand("ping").ok' | mongo localhost:27017/test --quiet
      interval: 30s
      timeout: 10s
      retries: 3

  # ==============================
  # Backend FastAPI
  # ==============================
  backend:
    build:
      context: ..
      dockerfile: docker/backend.Dockerfile
    container_name: sla-backend
    restart: unless-stopped
    env_file:
      - .env
    environment:
      - MONGO_URL=mongodb://mongodb:27017
      - DB_NAME=sla_sindacato
    ports:
      - "8001:8001"
    volumes:
      - ../backend/uploads:/app/backend/uploads
    depends_on:
      - mongodb
    networks:
      - sla-network
    healthcheck:
      test: ["CMD", "python", "-c", "import requests; requests.get('http://localhost:8001/api/health')"]
      interval: 30s
      timeout: 10s
      retries: 3

  # ==============================
  # Frontend React
  # ==============================
  frontend:
    build:
      context: ..
      dockerfile: docker/frontend.Dockerfile
    container_name: sla-frontend
    restart: unless-stopped
    ports:
      - "3000:80"
    depends_on:
      - backend
    networks:
      - sla-network

networks:
  sla-network:
    driver: bridge

volumes:
  mongodb_data:
    driver: local
```

### 12.2 backend.Dockerfile

```dockerfile
FROM python:3.11-slim

LABEL maintainer="SLA Sindacato"
LABEL description="Backend FastAPI per Portale Rimborsi SLA"

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Installa dipendenze sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copia requirements e installa dipendenze Python
COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir emergentintegrations \
        --extra-index-url https://d33sy5i8bnduwe.cloudfront.net/simple/ && \
    pip install --no-cache-dir -r backend/requirements.txt

# Copia codice sorgente backend
COPY backend/ backend/

# Crea directory uploads
RUN mkdir -p /app/backend/uploads && chmod 777 /app/backend/uploads

EXPOSE 8001

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8001/api/health')" || exit 1

WORKDIR /app/backend
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8001"]
```

### 12.3 frontend.Dockerfile

```dockerfile
# ============================================
# Stage 1: Build React App
# ============================================
FROM node:20-alpine AS builder

WORKDIR /app

# Copia package files
COPY frontend/package.json frontend/yarn.lock ./
RUN yarn install --frozen-lockfile

# Copia codice sorgente
COPY frontend/ ./

# Build produzione
RUN yarn build

# ============================================
# Stage 2: Nginx Server
# ============================================
FROM nginx:alpine

# Copia build da stage precedente
COPY --from=builder /app/build /usr/share/nginx/html

# Copia configurazione Nginx custom
COPY docker/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

### 12.4 nginx.conf

```nginx
server {
    listen 80;
    server_name _;

    root /usr/share/nginx/html;
    index index.html;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;

    # SPA routing - fallback to index.html
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Cache static assets
    location ~* \.(jpg|jpeg|png|gif|ico|css|js|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Disable cache for index.html
    location = /index.html {
        add_header Cache-Control "no-cache, no-store, must-revalidate";
    }
}
```

---

## 13. Credenziali di Test

### 13.1 Account Predefiniti

#### SuperAdmin
```
Email: superadmin@sla.it
Password: SlaAdmin2024!
Ruolo: SuperAdmin
Accesso: Completo (tutte le funzionalità)
```

**Nota:** Questo account viene creato automaticamente all'avvio del backend se non esiste.

### 13.2 Creazione Account Test Manuale

Per testare i vari ruoli, registra nuovi utenti dall'interfaccia:

**Esempio Delegato:**
```
Email: delegato.test@sla.it
Password: Test1234!
Nome: Mario Rossi
Ruolo: Delegato
Sede: [Seleziona da dropdown]
IBAN: IT60X0542811101000000123456
Indirizzo: Via Roma 1, 00100 Roma
```

**Esempio Iscritto:**
```
Email: iscritto.test@sla.it
Password: Test1234!
Nome: Luigi Bianchi
Ruolo: Iscritto
Sede: [Seleziona da dropdown]
IBAN: [Lascia vuoto]
Indirizzo: [Lascia vuoto]
```

### 13.3 Seed Data (Opzionale)

Per popolare il database con dati di test, puoi creare uno script Python:

**File:** `/app/backend/seed_data.py`
```python
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone
from uuid import uuid4

async def seed():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client.sla_sindacato
    
    # Crea sedi
    sedi = [
        {"id": str(uuid4()), "nome": "Autostrade per l'Italia", "codice": "ASPI", "provincia": "Roma"},
        {"id": str(uuid4()), "nome": "SATAP", "codice": "SATAP", "provincia": "Torino"},
        {"id": str(uuid4()), "nome": "SALT", "codice": "SALT", "provincia": "Firenze"},
    ]
    await db.sedi.insert_many(sedi)
    
    # Crea motivi rimborso
    motivi = [
        {"id": str(uuid4()), "codice": "ASSEMBLEA", "descrizione": "Assemblea sindacale", "is_active": True},
        {"id": str(uuid4()), "codice": "RIUNIONE", "descrizione": "Riunione coordinamento", "is_active": True},
        {"id": str(uuid4()), "codice": "FORMAZIONE", "descrizione": "Corso formazione", "is_active": True},
    ]
    await db.motivi_rimborso.insert_many(motivi)
    
    print("✅ Database popolato con successo!")

if __name__ == "__main__":
    asyncio.run(seed())
```

**Esecuzione:**
```bash
cd /opt/portale-sla/backend
python seed_data.py
```

---

## 14. Integrazioni Esterne

### 14.1 Google Maps Directions API

#### Scopo
Calcolo automatico della distanza chilometrica tra due località per rimborsi trasferte.

#### Setup

**1. Crea Progetto Google Cloud:**
- Vai su https://console.cloud.google.com/
- Crea nuovo progetto "Portale SLA"

**2. Abilita API:**
- Menu → "APIs & Services" → "Library"
- Cerca "Directions API"
- Clicca "Enable"

**3. Crea API Key:**
- "APIs & Services" → "Credentials"
- "Create Credentials" → "API key"
- Copia la chiave generata

**4. Configura Restrizioni:**
- Clicca sulla chiave creata
- "Application restrictions" → "HTTP referrers"
- Aggiungi:
  ```
  http://localhost:3000/*
  http://192.168.0.99:3000/*
  http://192.168.*/*
  ```
- "API restrictions" → "Restrict key"
  - Seleziona solo "Directions API"

**5. Aggiungi a .env:**
```bash
# File: docker/.env
GOOGLE_MAPS_API_KEY=AIzaSyC...tu_api_key_qui
```

**6. Riavvia Backend:**
```bash
docker compose -f docker/docker-compose.yml restart backend
```

#### Test Funzionamento

**Curl test:**
```bash
API_URL=http://192.168.0.99:8001

curl -X POST "$API_URL/api/calcola-km" \
  -H "Content-Type: application/json" \
  -d '{
    "origin": "Roma, Italia",
    "destination": "Milano, Italia"
  }'

# Output atteso:
# {
#   "km": 575.3,
#   "origin": "Roma, RM, Italia",
#   "destination": "Milano, MI, Italia"
# }
```

**Dal frontend:**
Durante creazione rimborso, inserisci località e clicca "Calcola KM Automatico"

#### Costi

- **Prezzo:** $5 per 1000 richieste
- **Free tier:** $200 credito mensile (= 40.000 richieste/mese)
- **Stima utilizzo:** ~300 rimborsi/mese = $1.50/mese

#### Fallback Manuale

Se l'API non è configurata o fallisce, l'utente può sempre inserire KM manualmente spuntando "Inserimento manuale".

---

## 15. Manutenzione e Backup

### 15.1 Backup Database MongoDB

#### Backup Manuale

```bash
# Crea directory backup
mkdir -p /opt/portale-sla/backups

# Export database
docker exec sla-mongodb mongodump \
  --db=sla_sindacato \
  --out=/dump

# Copia dump fuori dal container
docker cp sla-mongodb:/dump /opt/portale-sla/backups/backup_$(date +%Y%m%d_%H%M%S)

# Risultato:
# /opt/portale-sla/backups/backup_20240418_120000/sla_sindacato/
```

#### Backup Automatico (Cron)

```bash
# Crea script backup
nano /opt/portale-sla/scripts/backup_db.sh
```

**Contenuto script:**
```bash
#!/bin/bash
BACKUP_DIR="/opt/portale-sla/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# Crea backup
docker exec sla-mongodb mongodump --db=sla_sindacato --out=/dump
docker cp sla-mongodb:/dump "$BACKUP_DIR/backup_$DATE"

# Rimuovi dump dal container
docker exec sla-mongodb rm -rf /dump

# Mantieni solo ultimi 7 backup
cd "$BACKUP_DIR"
ls -t | tail -n +8 | xargs -r rm -rf

echo "✅ Backup completato: backup_$DATE"
```

**Rendi eseguibile:**
```bash
chmod +x /opt/portale-sla/scripts/backup_db.sh
```

**Cron giornaliero (2:00 AM):**
```bash
crontab -e

# Aggiungi riga:
0 2 * * * /opt/portale-sla/scripts/backup_db.sh >> /var/log/sla_backup.log 2>&1
```

#### Restore Database

```bash
# Stoppa backend (per evitare scritture)
docker compose -f docker/docker-compose.yml stop backend

# Copia backup nel container
docker cp /opt/portale-sla/backups/backup_20240418_120000/sla_sindacato sla-mongodb:/restore

# Restore
docker exec sla-mongodb mongorestore \
  --db=sla_sindacato \
  --drop \
  /restore/sla_sindacato

# Riavvia backend
docker compose -f docker/docker-compose.yml start backend
```

### 15.2 Backup File Uploads

```bash
# Backup directory uploads
tar -czf /opt/portale-sla/backups/uploads_$(date +%Y%m%d).tar.gz \
  /opt/portale-sla/backend/uploads

# Restore
tar -xzf /opt/portale-sla/backups/uploads_20240418.tar.gz -C /
```

### 15.3 Log Management

#### Visualizza Logs

```bash
# Logs backend (ultimi 100 righe)
docker compose -f docker/docker-compose.yml logs backend --tail=100

# Logs in tempo reale (follow)
docker compose -f docker/docker-compose.yml logs -f backend

# Logs di tutti i servizi
docker compose -f docker/docker-compose.yml logs --tail=50
```

#### Rotazione Logs Docker

Configura rotazione automatica in `docker-compose.yml`:

```yaml
services:
  backend:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

### 15.4 Aggiornamenti

#### Aggiornamento Codice

```bash
cd /opt/portale-sla

# Backup database prima di aggiornare
./scripts/backup_db.sh

# Pull nuovo codice (se da Git)
git pull origin main

# Rebuild container
docker compose -f docker/docker-compose.yml build

# Riavvia
docker compose -f docker/docker-compose.yml up -d

# Verifica
docker compose -f docker/docker-compose.yml ps
docker compose -f docker/docker-compose.yml logs backend --tail=50
```

#### Aggiornamento Dipendenze

**Backend:**
```bash
# Modifica requirements.txt
nano backend/requirements.txt

# Rebuild
docker compose -f docker/docker-compose.yml build backend
docker compose -f docker/docker-compose.yml up -d backend
```

**Frontend:**
```bash
# Accedi al container (o fai da locale)
cd frontend
yarn add nuova-dipendenza

# Rebuild
docker compose -f docker/docker-compose.yml build frontend
docker compose -f docker/docker-compose.yml up -d frontend
```

### 15.5 Monitoring

#### Statistiche Container

```bash
# Uso risorse real-time
docker stats

# Output:
# CONTAINER      CPU %    MEM USAGE / LIMIT     MEM %
# sla-backend    2.5%     180MiB / 256MiB       70%
# sla-frontend   0.1%     50MiB / 128MiB        39%
# sla-mongodb    5.2%     420MiB / 512MiB       82%
```

#### Health Checks

```bash
# Verifica health di tutti i container
docker ps --format "table {{.Names}}\t{{.Status}}"

# Output:
# NAMES           STATUS
# sla-backend     Up 2 hours (healthy)
# sla-frontend    Up 2 hours
# sla-mongodb     Up 2 hours (healthy)
```

#### Alerts Semplici (Email su Crash)

**Script:** `/opt/portale-sla/scripts/check_health.sh`
```bash
#!/bin/bash
CONTAINER="sla-backend"
STATUS=$(docker inspect --format='{{.State.Status}}' $CONTAINER 2>/dev/null)

if [ "$STATUS" != "running" ]; then
    echo "⚠️ Container $CONTAINER è DOWN!" | \
    mail -s "ALERT: Portale SLA Down" admin@sla.it
fi
```

**Cron ogni 5 minuti:**
```bash
*/5 * * * * /opt/portale-sla/scripts/check_health.sh
```

---

## 16. Roadmap Future

### 16.1 In Sviluppo (Prompt 2-3)

#### Priority P1

- [x] **Paginazione API**: Implementare skip/limit su tutti gli endpoint lista
  - Endpoint: `GET /api/rimborsi`, `/api/documenti`, `/api/annunci`, ecc.
  - Response: `{ "items": [...], "total": 123, "skip": 0, "limit": 20 }`
  
- [ ] **Fix N+1 Query**: Ottimizzare query con batch loading
  - Sostituire loop con aggregation pipeline MongoDB
  - Esempio: Caricare tutti gli utenti in una query invece di N query

- [ ] **Refactoring server.py**: Dividere monolite in routes modulari
  ```
  backend/
    routes/
      auth.py
      rimborsi.py
      documenti.py
      admin.py
      superadmin.py
  ```

- [ ] **Fix Notifiche**: Collegare `notify_rimborso_created()` agli eventi reali
  - Trigger su creazione rimborso
  - Trigger su cambio stato

- [ ] **Frontend Error Handling**: Aggiungere toast errori e try/catch
  - Libreria: react-hot-toast
  - Pattern: Wrapper axios con interceptor

#### Priority P2

- [ ] **Upload Ricevute in Rimborsi**: Permettere upload durante creazione
  - Attualmente: Upload solo dopo creazione
  - Target: Form multi-step con upload integrato

- [ ] **Export PDF Rendiconti**: Generare PDF oltre a CSV
  - Libreria backend: ReportLab
  - Template: Logo SLA + tabella rimborsi

### 16.2 Funzionalità Future

#### Autenticazione Avanzata
- [ ] **Reset Password via Email**: Flow recupero password
  - Integrazione: SendGrid o SMTP Gmail
  - Token temporaneo con scadenza

- [ ] **2FA (Two-Factor Auth)**: OTP via email o app
  - Libreria: pyotp
  - Opzionale per ruoli Admin+

#### Miglioramenti Rimborsi
- [ ] **Template Rimborsi Ricorrenti**: Salva trasferte frequenti
  - Es: "Assemblea mensile Roma-Milano"
  
- [ ] **Notifiche Email**: Oltre in-app, invia email
  - Su approvazione/rifiuto rimborso
  - Digest settimanale

- [ ] **Workflow Approvazione Multi-Livello**:
  - Segretario approva → Admin conferma → SuperAdmin chiude
  - Stati intermedi: `in_revisione_segretario`, `in_revisione_admin`

#### Dashboard e Analytics
- [ ] **Dashboard Grafici**: Visualizzazioni avanzate
  - Grafici: Rimborsi per mese, per motivo, per sede
  - Libreria: Recharts (già installata)

- [ ] **Report Comparativi**: Confronto anno su anno
  - Es: Rimborsi 2024 vs 2023

#### Mobile
- [ ] **App Mobile**: React Native o PWA
  - PWA più semplice (service worker + manifest)
  - Notifiche push

#### Multi-Tenant
- [ ] **Istanze Separate per Sede**: Database segregati
  - Ogni sede ha proprio sottodominio
  - Es: aspi.portalesla.it, satap.portalesla.it

### 16.3 Migrazioni Cloud (Quando Necessario)

#### Opzione A: VPS Self-Managed
**Provider:** Hetzner, DigitalOcean, Contabo

**Setup:**
- Server: Ubuntu 22.04, 2 vCPU, 4GB RAM (~€5-10/mese)
- Docker Compose (stesso stack)
- Dominio + SSL (Let's Encrypt gratuito)

**Pro:** Controllo totale, costi bassi  
**Contro:** Richiede gestione manuale

#### Opzione B: Platform as a Service (PaaS)
**Backend:** Railway, Render, Fly.io  
**Frontend:** Vercel, Netlify (gratis)  
**Database:** MongoDB Atlas (512MB gratis)

**Pro:** Zero manutenzione, auto-scaling  
**Contro:** Costi crescenti con utenti (~€15-30/mese)

#### Opzione C: Managed Kubernetes
**Provider:** DigitalOcean Kubernetes, Google GKE

**Setup:**
- Cluster 2 nodi (~€20/mese)
- Helm charts per deploy
- Auto-scaling

**Pro:** Alta disponibilità, production-ready  
**Contro:** Complessità, costo più alto

**Raccomandazione:** Inizia con VPS (Opzione A), migra a PaaS se traffico > 1000 utenti/giorno

---

## 17. Troubleshooting

### 17.1 Container Non Si Avvia

**Sintomo:** Container in stato `Restarting` o `Exited`

**Diagnosi:**
```bash
# Controlla stato
docker compose -f docker/docker-compose.yml ps

# Visualizza logs
docker compose -f docker/docker-compose.yml logs [container_name]

# Ispezione dettagli
docker inspect [container_name]
```

**Cause Comuni:**

#### Backend Crash
```
Error: "ModuleNotFoundError"
```
**Fix:** Verifica `WORKDIR` in Dockerfile, ricostruisci immagine

```
Error: "Connection refused MongoDB"
```
**Fix:** Assicurati MongoDB sia UP, controlla `MONGO_URL` in .env

#### Frontend 404
```
Error: Nginx "404 Not Found" su tutte le rotte
```
**Fix:** Verifica `nginx.conf` abbia `try_files $uri /index.html`

#### MongoDB Restart Loop
```
Warning: "MongoDB 5.0+ requires AVX"
```
**Fix:** Usa `mongo:4.4.18` (vedi sezione 11.1)

---

### 17.2 Problemi di Rete

**Sintomo:** Frontend non raggiunge Backend API

**Check 1: Verifica Porte Esposte**
```bash
docker compose -f docker/docker-compose.yml ps

# Output deve mostrare:
# 0.0.0.0:3000->80/tcp      (frontend)
# 0.0.0.0:8001->8001/tcp    (backend)
```

**Check 2: Test Connettività Backend**
```bash
curl http://192.168.0.99:8001/api/health

# Output atteso:
# {"status": "healthy"}
```

**Check 3: CORS Configurato**
```bash
# File: backend/server.py
# Verifica che FRONTEND_URL sia in allow_origins
allow_origins=["http://192.168.0.99:3000", ...]
```

**Check 4: Frontend .env Corretto**
```bash
# File: frontend/.env
REACT_APP_BACKEND_URL=http://192.168.0.99:8001
```

---

### 17.3 Prestazioni Lente

**Sintomo:** Richieste API lente (> 5 secondi)

**Diagnosi:**

```bash
# Verifica uso CPU/RAM
docker stats

# Verifica MongoDB indexes
docker exec -it sla-mongodb mongo sla_sindacato
> db.rimborsi.getIndexes()
```

**Ottimizzazioni:**

1. **Aggiungi Indici MongoDB:**
```javascript
db.rimborsi.createIndex({ user_id: 1 });
db.rimborsi.createIndex({ sede_id: 1, status: 1 });
db.notifiche.createIndex({ user_id: 1, letta: 1 });
```

2. **Limita Risultati Query:**
```python
# Sempre usare limit
rimborsi = await db.rimborsi.find().limit(50).to_list(50)
```

3. **Abilita Query Cache (Future):**
```python
# Redis per caching
from redis import asyncio as aioredis
```

---

### 17.4 Spazio Disco Pieno

**Sintomo:** `No space left on device`

**Diagnosi:**
```bash
# Verifica spazio
df -h

# Verifica volumi Docker
docker system df
```

**Pulizia:**
```bash
# Rimuovi immagini inutilizzate
docker image prune -a

# Rimuovi volumi orfani
docker volume prune

# Pulizia completa (attenzione!)
docker system prune -a --volumes
```

**Rotazione Logs:**
```bash
# Svuota log container
truncate -s 0 $(docker inspect --format='{{.LogPath}}' sla-backend)
```

---

### 17.5 Login Non Funziona

**Sintomo:** "Credenziali non valide" anche con password corretta

**Check 1: Verifica Utente Esiste**
```bash
docker exec -it sla-mongodb mongo sla_sindacato

> db.users.findOne({ email: "superadmin@sla.it" })
```

**Check 2: Password Hash Corretto**
```python
# Test manuale hash
import bcrypt
password = "SlaAdmin2024!"
hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
print(hashed)
```

**Check 3: JWT Secret Configurato**
```bash
# File: docker/.env
grep JWT_SECRET docker/.env

# Deve essere presente e non vuoto
```

**Fix Utente Corrotto:**
```bash
# Elimina e ricrea SuperAdmin
docker exec -it sla-mongodb mongo sla_sindacato

> db.users.deleteOne({ email: "superadmin@sla.it" })

# Riavvia backend (ricrea automaticamente)
docker compose -f docker/docker-compose.yml restart backend
```

---

### 17.6 Google Maps Non Calcola KM

**Sintomo:** "Impossibile calcolare percorso"

**Check 1: API Key Presente**
```bash
grep GOOGLE_MAPS_API_KEY docker/.env
```

**Check 2: API Abilitata**
- Vai su https://console.cloud.google.com/
- "APIs & Services" → "Enabled APIs"
- Verifica "Directions API" sia presente

**Check 3: Quota Non Esaurita**
- "APIs & Services" → "Quotas"
- Controlla utilizzo giornaliero

**Check 4: Restrizioni IP/Referrer**
- "Credentials" → Click su API Key
- Verifica `192.168.0.99` sia nei referrer consentiti

**Test Diretto:**
```bash
API_KEY="tua_api_key_qui"
curl "https://maps.googleapis.com/maps/api/directions/json?origin=Roma&destination=Milano&key=$API_KEY"
```

---

### 17.7 Supporto

**Documentazione Aggiuntiva:**
- `/app/README.md` - Guida setup rapida
- `/app/RASPBERRY_PI_QUICK_START.md` - Deploy Raspberry Pi
- `/app/DOCKER_DEPLOYMENT_GUIDE.md` - Approfondimento Docker

**Log Files:**
- Backend: `docker compose -f docker/docker-compose.yml logs backend`
- Frontend: `docker compose -f docker/docker-compose.yml logs frontend`
- MongoDB: `docker compose -f docker/docker-compose.yml logs mongodb`

**Community:**
- GitHub Issues (se repository pubblico)
- Email: supporto interno SLA

---

## Appendice A: Comandi Rapidi

### Docker Compose

```bash
# Avvia servizi
docker compose -f docker/docker-compose.yml up -d

# Ferma servizi
docker compose -f docker/docker-compose.yml down

# Riavvia singolo servizio
docker compose -f docker/docker-compose.yml restart backend

# Rebuild dopo modifica codice
docker compose -f docker/docker-compose.yml build
docker compose -f docker/docker-compose.yml up -d

# Logs
docker compose -f docker/docker-compose.yml logs -f backend

# Stato servizi
docker compose -f docker/docker-compose.yml ps
```

### MongoDB

```bash
# Accedi MongoDB shell
docker exec -it sla-mongodb mongo sla_sindacato

# Backup database
docker exec sla-mongodb mongodump --db=sla_sindacato --out=/dump
docker cp sla-mongodb:/dump ./backup_$(date +%Y%m%d)

# Restore database
docker cp ./backup_20240418 sla-mongodb:/restore
docker exec sla-mongodb mongorestore --db=sla_sindacato --drop /restore/sla_sindacato
```

### System

```bash
# Trova IP Raspberry
hostname -I

# Monitora risorse
htop
docker stats

# Spazio disco
df -h
docker system df

# Restart completo Raspberry
reboot
```

---

## Appendice B: Variabili Ambiente Complete

### docker/.env
```bash
# ==============================
# MongoDB
# ==============================
MONGO_URL=mongodb://mongodb:27017
DB_NAME=sla_sindacato

# ==============================
# JWT Authentication
# ==============================
JWT_SECRET=CAMBIA_QUESTA_CHIAVE_CON_UNA_CASUALE_SICURA_DI_ALMENO_32_CARATTERI
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# ==============================
# Admin Iniziale
# ==============================
ADMIN_EMAIL=superadmin@sla.it
ADMIN_PASSWORD=SlaAdmin2024!

# ==============================
# Integrazioni Esterne
# ==============================
GOOGLE_MAPS_API_KEY=

# ==============================
# Frontend & CORS
# ==============================
FRONTEND_URL=http://192.168.0.99:3000
ALLOWED_ORIGINS=http://192.168.0.99:3000,http://localhost:3000

# ==============================
# Opzionali
# ==============================
# SENDGRID_API_KEY=  # Per email notifiche (futuro)
# REDIS_URL=         # Per caching (futuro)
```

### frontend/.env
```bash
REACT_APP_BACKEND_URL=http://192.168.0.99:8001
```

---

## Conclusione

Questo documento rappresenta la documentazione completa del **Portale SLA** dalla sua concezione al deployment finale su Raspberry Pi 4.

**Stato Attuale:**
- ✅ MVP completato e funzionante
- ✅ Deployment Docker su Raspberry Pi
- ✅ SuperAdmin creato e testato
- ✅ Frontend, Backend, MongoDB online
- ⏳ Google Maps API da configurare
- ⏳ Refactoring e ottimizzazioni in programma

**Prossimi Passi:**
1. Configurare Google Maps API Key
2. Testare workflow rimborsi completo
3. Registrare utenti test per ogni ruolo
4. Implementare paginazione API (Prompt 2)
5. Refactoring server.py (Prompt 3)

**Contatti:**
- Deployment Host: `http://192.168.0.99:3000`
- SuperAdmin: `superadmin@sla.it` / `SlaAdmin2024!`

---

**Documento Generato:** 18 Aprile 2026  
**Versione Portale:** 1.0.0  
**Autore:** Team Sviluppo SLA + Emergent AI Agent  

**© 2024-2026 Sindacato Lavoratori Autostradali - Tutti i diritti riservati**
