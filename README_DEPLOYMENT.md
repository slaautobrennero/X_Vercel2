# 🚀 Guida Deployment Portale SLA - Vercel GRATUITO

## 📋 Indice
1. [Prerequisiti](#prerequisiti)
2. [Setup MongoDB Atlas (Database Gratuito)](#setup-mongodb-atlas)
3. [Deploy su Vercel (Hosting Gratuito)](#deploy-su-vercel)
4. [Configurazione Variabili d'Ambiente](#configurazione-variabili)
5. [Aggiornamenti e Manutenzione](#aggiornamenti)
6. [Troubleshooting](#troubleshooting)

---

## 1. Prerequisiti

Prima di iniziare, assicurati di avere:
- ✅ Un account GitHub (gratuito) - [Registrati qui](https://github.com/signup)
- ✅ Un account MongoDB Atlas (gratuito) - [Registrati qui](https://www.mongodb.com/cloud/atlas/register)
- ✅ Un account Vercel (gratuito) - [Registrati qui](https://vercel.com/signup)
- ✅ Il codice del portale salvato su GitHub

---

## 2. Setup MongoDB Atlas (Database Gratuito)

### Step 1: Crea un Cluster Gratuito
1. Vai su [MongoDB Atlas](https://cloud.mongodb.com/)
2. Click su **"Build a Database"**
3. Scegli **"M0 FREE"** (512MB gratis per sempre)
4. Seleziona una region vicina all'Italia (es: Frankfurt, Germany)
5. Click su **"Create Cluster"**

### Step 2: Configura Accesso
1. **Database Access** (menu laterale):
   - Click su **"Add New Database User"**
   - Username: `sla_admin` (o quello che preferisci)
   - Password: Genera una password sicura (SALVALA!)
   - Database User Privileges: **"Read and write to any database"**
   - Click **"Add User"**

2. **Network Access** (menu laterale):
   - Click su **"Add IP Address"**
   - Click su **"Allow Access from Anywhere"** (necessario per Vercel)
   - IP: `0.0.0.0/0`
   - Click **"Confirm"**

### Step 3: Ottieni la Connection String
1. Click su **"Connect"** sul tuo cluster
2. Scegli **"Connect your application"**
3. Copia la connection string (simile a):
   ```
   mongodb+srv://sla_admin:<password>@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
   ```
4. **IMPORTANTE**: Sostituisci `<password>` con la password vera dell'utente database

**Esempio finale**:
```
mongodb+srv://sla_admin:MiaPasswordSegreta123@cluster0.abcde.mongodb.net/?retryWrites=true&w=majority
```

✅ **SALVA questa stringa! Ti servirà dopo.**

---

## 3. Deploy su Vercel (Hosting Gratuito)

### Step 1: Salva il Codice su GitHub
1. Usa la funzione **"Save to GitHub"** di Emergent
2. Oppure, da terminale:
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/TUO-USERNAME/portale-sla.git
   git push -u origin main
   ```

### Step 2: Connetti Vercel a GitHub
1. Vai su [Vercel](https://vercel.com)
2. Click su **"Add New" → "Project"**
3. Click su **"Import Git Repository"**
4. Seleziona il repository del portale SLA
5. Click su **"Import"**

### Step 3: Configura il Progetto

#### **Root Directory**: Lascia vuoto (o imposta `/`)

#### **Framework Preset**: 
- Frontend: **Create React App**
- Backend: **Other** (Python)

#### **Build Settings**:
```
Build Command: cd frontend && yarn install && yarn build
Output Directory: frontend/build
Install Command: yarn install
```

### Step 4: Configura Variabili d'Ambiente
Nel pannello Vercel, vai su **"Environment Variables"** e aggiungi:

| Nome Variabile | Valore | Dove Usata |
|----------------|--------|------------|
| `MONGO_URL` | `mongodb+srv://sla_admin:password@cluster...` | Backend |
| `DB_NAME` | `sla_sindacato` | Backend |
| `JWT_SECRET` | `GENERA-UNA-STRINGA-CASUALE-LUNGA-E-SICURA` | Backend |
| `GOOGLE_MAPS_API_KEY` | `AIza...` (se hai l'API abilitata) | Backend |
| `REACT_APP_BACKEND_URL` | `/api` (Vercel gestisce il routing) | Frontend |

#### Come generare JWT_SECRET sicuro:
```bash
# Da terminale:
openssl rand -base64 32
```
Copia il risultato e usalo come JWT_SECRET.

### Step 5: Deploy!
1. Click su **"Deploy"**
2. Aspetta 2-5 minuti
3. ✅ Il tuo portale è ONLINE!

---

## 4. Configurazione Variabili d'Ambiente

### Frontend (`/frontend/.env`):
```env
# URL backend (in produzione Vercel usa routing interno)
REACT_APP_BACKEND_URL=/api
```

### Backend (`/backend/.env`):
```env
# MongoDB
MONGO_URL=mongodb+srv://username:password@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
DB_NAME=sla_sindacato

# JWT Security
JWT_SECRET=tua-stringa-segreta-lunga-e-casuale

# Google Maps (opzionale)
GOOGLE_MAPS_API_KEY=AIzaSy...
```

⚠️ **IMPORTANTE**: 
- NON committare mai le variabili d'ambiente su GitHub
- Usa sempre le Environment Variables di Vercel per produzione

---

## 5. Aggiornamenti e Manutenzione

### Come Aggiornare l'Applicazione:
1. **Salva modifiche su GitHub**:
   ```bash
   git add .
   git commit -m "Aggiornamento feature XYZ"
   git push
   ```

2. **Deploy Automatico**:
   - Vercel rileva il push e fa deploy automaticamente
   - Ogni push su `main` → deploy in produzione
   - Ogni push su altri branch → preview deployment

### URL della Tua App:
- **Produzione**: `https://portale-sla.vercel.app` (o dominio custom)
- **Preview**: Ogni branch ottiene un URL temporaneo

---

## 6. Troubleshooting

### ❌ Problema: Backend non si connette al database
**Soluzione**:
1. Verifica che `MONGO_URL` su Vercel sia corretta
2. Controlla che l'IP `0.0.0.0/0` sia autorizzato su MongoDB Atlas
3. Verifica username e password nella connection string

### ❌ Problema: "500 Internal Server Error"
**Soluzione**:
1. Vai su Vercel → "Deployments" → Click sull'ultimo deploy
2. Vai su "Functions" → Cerca errori nei log
3. Verifica tutte le variabili d'ambiente

### ❌ Problema: Google Maps calcolo KM non funziona
**Soluzione**:
1. Vai su [Google Cloud Console](https://console.cloud.google.com/)
2. Abilita **"Directions API"** (non solo Maps JavaScript API)
3. Copia la nuova API key
4. Aggiorna `GOOGLE_MAPS_API_KEY` su Vercel

### ❌ Problema: Frontend mostra pagina bianca
**Soluzione**:
1. Controlla i log del browser (F12 → Console)
2. Verifica che `REACT_APP_BACKEND_URL=/api` sia impostato
3. Ricostruisci il frontend: `cd frontend && yarn build`

---

## 📊 Limiti Piano Gratuito

### MongoDB Atlas M0 (Free):
- ✅ 512MB storage
- ✅ Condiviso tra 3 cluster
- ✅ Sufficiente per ~5000-10000 utenti
- ✅ Backup automatici non inclusi (fai backup manuali)

### Vercel Free Tier:
- ✅ 100GB bandwidth/mese
- ✅ Deploy illimitati
- ✅ HTTPS automatico
- ✅ Sufficiente per 10.000-50.000 visite/mese
- ⚠️ Funzioni serverless: 100 ore di esecuzione/mese

### Quando passare a piano a pagamento:
- MongoDB: Quando superi 512MB o serve backup automatico (~€9/mese)
- Vercel: Quando superi 100GB bandwidth (~€20/mese per Pro)

---

## 🎯 Prossimi Passi

1. ✅ Crea il primo utente SuperAdmin manualmente da MongoDB Atlas
2. ✅ Aggiungi le sedi (A22, CAV, etc.)
3. ✅ Invita i primi utenti a registrarsi
4. ✅ Testa tutte le funzionalità in produzione
5. ✅ Configura backup settimanali del database

---

## 📞 Supporto

Per problemi tecnici:
- 📧 MongoDB: https://www.mongodb.com/cloud/atlas/support
- 📧 Vercel: https://vercel.com/support
- 📚 Documentazione: Leggi i commenti nel codice!

---

**Buon deployment! 🚀**
