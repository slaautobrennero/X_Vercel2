"""
==============================================
SLA PORTALE - Server FastAPI
==============================================

Entry point dell'applicazione backend.
Gestisce tutte le API per il portale rimborsi del Sindacato Lavoratori Autostradali.

Funzionalità principali:
- Autenticazione JWT multi-ruolo (7 ruoli)
- Gestione rimborsi con calcolo KM automatico/manuale
- Upload documenti e modulistica
- Bacheca e notifiche
- Export PDF/Excel rendiconti

Per avviare in sviluppo:
    uvicorn server:app --reload --port 8001

Documentazione API automatica:
    http://localhost:8001/docs (Swagger)
    http://localhost:8001/redoc (ReDoc)

==============================================
"""

# ==================== IMPORTS ====================

# Environment variables - Load FIRST before other imports
from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# FastAPI framework
from fastapi import FastAPI, APIRouter, HTTPException, Request, Response, Depends, UploadFile, File, Form
from fastapi.responses import FileResponse, StreamingResponse
from starlette.middleware.cors import CORSMiddleware

# Database - MongoDB async driver
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

# Standard library
import os
import logging
import secrets
import io
import csv
import uuid
import math
from datetime import datetime, timezone, timedelta
from typing import List, Optional

# Security & External APIs
import bcrypt  # Password hashing
import jwt     # JSON Web Tokens
import aiofiles  # Async file operations
import httpx   # HTTP client for Google Maps API

# Data validation
from pydantic import BaseModel, Field, EmailStr

# ==================== CONFIGURAZIONE ====================

# MongoDB - Database NoSQL per tutti i dati
# NOTA: MONGO_URL viene da /app/backend/.env
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT - Autenticazione con JSON Web Tokens
# NOTA: JWT_SECRET deve essere una chiave segreta robusta in produzione
JWT_SECRET = os.environ['JWT_SECRET']
JWT_ALGORITHM = "HS256"

# Google Maps API - Calcolo chilometri automatico
# NOTA: Richiede API "Directions" abilitata su Google Cloud Console
GOOGLE_MAPS_API_KEY = os.environ.get('GOOGLE_MAPS_API_KEY', '')

# FastAPI App - Applicazione principale
app = FastAPI(
    title="SLA Sindacato - Portale Rimborsi",
    description="Gestione rimborsi e documenti per 30 concessionarie autostradali",
    version="1.0.0"
)
api_router = APIRouter(prefix="/api")  # Tutti gli endpoint hanno prefisso /api

# Logging - Per debug e monitoraggio
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Directory Upload - Per documenti, modulistica e ricevute
UPLOAD_DIR = ROOT_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB limite

# ==================== PYDANTIC MODELS ====================
# Definiscono la struttura dei dati in input/output delle API
# Pydantic valida automaticamente i dati e genera documentazione

# --- USER MODELS (Utenti) ---

class UserBase(BaseModel):
    """Base user fields - Campi comuni a tutti gli utenti"""
    email: EmailStr
    nome: str
    cognome: str
    telefono: Optional[str] = None
    indirizzo: Optional[str] = None  # NOTA: Non richiesto per ruolo "iscritto"
    citta: Optional[str] = None
    cap: Optional[str] = None
    iban: Optional[str] = None  # NOTA: Non richiesto per ruolo "iscritto"

class UserCreate(UserBase):
    """User registration - Registrazione nuovo utente"""
    password: str  # Verrà hashato con bcrypt
    sede_id: Optional[str] = None  # Riferimento alla sede (A22, CAV, etc.)
    ruolo: str = "iscritto"  # Default: iscritto (accesso solo bacheca/documenti)
    # Ruoli disponibili: superadmin, superuser, admin, cassiere, segretario, segreteria, delegato, iscritto

class UserUpdate(BaseModel):
    """User profile update - Aggiornamento profilo utente"""
    nome: Optional[str] = None
    cognome: Optional[str] = None
    telefono: Optional[str] = None
    indirizzo: Optional[str] = None
    citta: Optional[str] = None
    cap: Optional[str] = None
    iban: Optional[str] = None

class UserResponse(BaseModel):
    """User data response - Dati utente restituiti dalle API (senza password)"""
    id: str
    email: str
    nome: str
    cognome: str
    telefono: Optional[str] = None
    indirizzo: Optional[str] = None
    citta: Optional[str] = None
    cap: Optional[str] = None
    iban: Optional[str] = None
    ruolo: str
    sede_id: Optional[str] = None
    sede_nome: Optional[str] = None
    created_at: str

class LoginRequest(BaseModel):
    """Login credentials - Credenziali per l'accesso"""
    email: EmailStr
    password: str

# --- SEDE MODELS (Sedi/Concessionarie) ---

class SedeCreate(BaseModel):
    """Headquarter creation - Creazione nuova sede (A22, CAV, Autostrade, etc.)"""
    nome: str  # Es: "Autostrada del Brennero"
    codice: str  # Es: "A22"
    indirizzo: Optional[str] = None
    tariffa_km: float = 0.35  # €/km - Tariffa chilometrica per rimborsi
    rimborso_pasti: float = 15.0  # € - Rimborso standard pasti
    rimborso_autostrada: bool = True  # Se rimborsare i pedaggi

class SedeUpdate(BaseModel):
    """Headquarter update - Aggiornamento dati sede"""
    nome: Optional[str] = None
    indirizzo: Optional[str] = None
    tariffa_km: Optional[float] = None
    rimborso_pasti: Optional[float] = None
    rimborso_autostrada: Optional[bool] = None

# --- RIMBORSO MODELS (Reimbursements) ---

class MotivoRimborsoCreate(BaseModel):
    """Reimbursement reason - Motivo di rimborso (RSA, Sede, Corso, Altro)"""
    nome: str  # Es: "RSA", "Sede", "Altro"
    descrizione: Optional[str] = None
    richiede_note: bool = False  # Se True, le note sono obbligatorie

class MotivoRimborsoUpdate(BaseModel):
    """Update reimbursement reason - Aggiornamento motivo"""
    nome: Optional[str] = None
    descrizione: Optional[str] = None
    richiede_note: Optional[bool] = None

class RimborsoCreate(BaseModel):
    """
    Create reimbursement request - Creazione richiesta rimborso
    
    Flusso:
    1. Utente inserisce partenza/arrivo
    2. Sistema calcola KM con Google Maps (opzionale)
    3. Utente può modificare KM manualmente (genera alert per admin)
    4. Calcolo automatico: (KM * tariffa) + pasti + autostrada
    """
    data: str  # Data della trasferta
    motivo_id: str  # Riferimento al motivo (RSA/Sede/Altro)
    
    # Percorso
    indirizzo_partenza: str
    indirizzo_partenza_tipo: str = "manuale"  # "casa" o "manuale"
    indirizzo_arrivo: str
    
    # Chilometri
    km_andata: float  # KM inseriti dall'utente (calcolati o manuali)
    km_calcolati: Optional[float] = None  # KM originali da Google Maps (per confronto)
    km_modificati_manualmente: bool = False  # True se l'utente ha sovrascritto il calcolo
    andata_ritorno: bool = True  # Se True, KM totali = km_andata * 2
    
    # Autostrada
    uso_autostrada: bool = False
    costo_autostrada: float = 0  # Importo pedaggi
    
    # Pasti
    importo_pasti: float = 0  # Totale spese pasti (senza limiti)
    numero_partecipanti_pasto: int = 0  # Numero persone al pasto
    
    # Note
    note: Optional[str] = None  # OBBLIGATORIE se motivo="Altro"

class RimborsoUpdate(BaseModel):
    """Update reimbursement status - Aggiornamento stato rimborso (admin)"""
    stato: Optional[str] = None  # "in_attesa", "approvato", "rifiutato", "pagato"
    note_admin: Optional[str] = None  # Motivazione rifiuto o note interne
    km_approvati: Optional[bool] = None  # Conferma KM se inseriti manualmente

# --- COMMUNICATION MODELS (Bacheca/Documenti) ---

class AnnuncioCreate(BaseModel):
    """Create announcement - Creazione comunicato per bacheca"""
    titolo: str
    contenuto: str
    link_documento: Optional[str] = None  # Link a documento allegato

class DocumentoCreate(BaseModel):
    """Upload document - Caricamento documento/modulistica"""
    nome: str  # Nome file
    categoria: str  # "modulistica", "documento", "altro"
    descrizione: Optional[str] = None  # Descrizione opzionale

class CalcoloKmRequest(BaseModel):
    """Google Maps distance request - Richiesta calcolo KM tra due indirizzi"""
    origine: str  # Indirizzo partenza
    destinazione: str  # Indirizzo arrivo

# --- CONTATTI / LINK SIDEBAR ---

class ContattoBase(BaseModel):
    """Contatto/Link sidebar - per concessionaria"""
    titolo: str  # Es: "Ufficio Sede"
    descrizione: Optional[str] = None  # Es: "Lun-Ven 9-18"
    tipo: str  # link | whatsapp | telegram | email | telefono
    valore: str  # URL completo, numero tel, email...

class ContattoCreate(ContattoBase):
    pass

class ContattoUpdate(BaseModel):
    titolo: Optional[str] = None
    descrizione: Optional[str] = None
    tipo: Optional[str] = None
    valore: Optional[str] = None

# ==================== AUTH HELPERS ====================
# Funzioni per autenticazione JWT e gestione password

def hash_password(password: str) -> str:
    """
    Hash password with bcrypt
    Cripta la password usando bcrypt (algoritmo sicuro con salt)
    """
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify password against hash
    Verifica se la password corrisponde all'hash salvato
    """
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))

def create_access_token(user_id: str, email: str) -> str:
    """
    Create JWT access token (expires in 24h)
    Crea token di accesso JWT valido per 24 ore
    """
    payload = {
        "sub": user_id,
        "email": email,
        "exp": datetime.now(timezone.utc) + timedelta(hours=24),
        "type": "access"
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def create_refresh_token(user_id: str) -> str:
    """
    Create JWT refresh token (expires in 7 days)
    Crea token di refresh valido per 7 giorni
    """
    payload = {
        "sub": user_id,
        "exp": datetime.now(timezone.utc) + timedelta(days=7),
        "type": "refresh"
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

async def get_current_user(request: Request) -> dict:
    """
    Get authenticated user from JWT token
    Estrae e valida l'utente dal token JWT (cookie o header Authorization)
    
    Returns: User dict senza password
    Raises: HTTPException 401 se token mancante/invalido/scaduto
    """
    # Try to get token from cookie first
    token = request.cookies.get("access_token")
    if not token:
        # Fallback to Authorization header
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
    if not token:
        raise HTTPException(status_code=401, detail="Non autenticato")
    
    try:
        # Decode and validate token
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Token non valido")
        
        # Fetch user from database
        user = await db.users.find_one({"_id": ObjectId(payload["sub"])})
        if not user:
            raise HTTPException(status_code=401, detail="Utente non trovato")
        
        # Format user data (remove MongoDB _id, add string id)
        user["id"] = str(user["_id"])
        user.pop("_id", None)
        user.pop("password_hash", None)  # NEVER return password
        
        # Add sede name if user belongs to a sede
        if user.get("sede_id"):
            sede = await db.sedi.find_one({"_id": ObjectId(user["sede_id"])})
            if sede:
                user["sede_nome"] = sede["nome"]
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token scaduto")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token non valido")

# ==================== NOTIFICATION HELPERS ====================

async def _notify_users_by_role(roles: list, sede_id: Optional[str], notifica_data: dict, include_global: bool = False):
    """
    Crea una notifica per ogni utente che ha uno dei ruoli indicati nella sede.
    Se include_global=True include anche superadmin/superuser (sede_id None).
    """
    if sede_id and include_global:
        query = {
            "$and": [
                {"ruolo": {"$in": roles}},
                {"$or": [{"sede_id": sede_id}, {"sede_id": None}]}
            ]
        }
    elif sede_id:
        query = {"ruolo": {"$in": roles}, "sede_id": sede_id}
    else:
        query = {"ruolo": {"$in": roles}}

    notifiche_to_insert = []
    async for u in db.users.find(query, {"_id": 1}):
        notifiche_to_insert.append({
            **notifica_data,
            "user_id": str(u["_id"]),
            "letto": False,
            "created_at": datetime.now(timezone.utc).isoformat()
        })
    if notifiche_to_insert:
        await db.notifiche.insert_many(notifiche_to_insert)


async def _notify_user(user_id: str, notifica_data: dict):
    """Crea una notifica per un singolo utente."""
    await db.notifiche.insert_one({
        **notifica_data,
        "user_id": user_id,
        "letto": False,
        "created_at": datetime.now(timezone.utc).isoformat()
    })


async def _notify_all_in_sede(sede_id: Optional[str], notifica_data: dict, exclude_user_id: Optional[str] = None):
    """
    Notifica TUTTI gli utenti: se sede_id è valorizzato, gli utenti di quella sede + utenti globali (sede_id None).
    Se sede_id è None, notifica tutti gli utenti del sistema.
    Esclude opzionalmente l'autore.
    """
    if sede_id:
        base_query = {"$or": [{"sede_id": sede_id}, {"sede_id": None}]}
    else:
        base_query = {}

    if exclude_user_id:
        try:
            query = {"$and": [base_query, {"_id": {"$ne": ObjectId(exclude_user_id)}}]} if base_query else {"_id": {"$ne": ObjectId(exclude_user_id)}}
        except Exception:
            query = base_query
    else:
        query = base_query

    notifiche_to_insert = []
    async for u in db.users.find(query, {"_id": 1}):
        notifiche_to_insert.append({
            **notifica_data,
            "user_id": str(u["_id"]),
            "letto": False,
            "created_at": datetime.now(timezone.utc).isoformat()
        })
    if notifiche_to_insert:
        await db.notifiche.insert_many(notifiche_to_insert)



# ==================== AUTH ROUTES ====================
# API per registrazione, login, logout e gestione sessioni

@api_router.post("/auth/register")
async def register(user_data: UserCreate, response: Response):
    """
    POST /api/auth/register
    Registrazione nuovo utente
    
    Regole:
    - Email univoca
    - Auto-registrazione solo per "iscritto" o "delegato"
    - "Iscritto": IBAN e indirizzo NON richiesti
    - "Delegato": IBAN e indirizzo OBBLIGATORI (per ricevere rimborsi)
    - Altri ruoli possono essere assegnati solo da admin
    """
    email = user_data.email.lower()
    
    # Check email già registrata
    existing = await db.users.find_one({"email": email})
    if existing:
        raise HTTPException(status_code=400, detail="Email già registrata")
    
    # Only allow iscritto or delegato for self-registration
    allowed_roles = ["iscritto", "delegato"]
    ruolo = user_data.ruolo if user_data.ruolo in allowed_roles else "iscritto"
    
    # Validate sede exists if provided
    if user_data.sede_id:
        sede = await db.sedi.find_one({"_id": ObjectId(user_data.sede_id)})
        if not sede:
            raise HTTPException(status_code=400, detail="Sede non trovata")
    
    # REGOLA: Delegato DEVE avere IBAN e indirizzo (per rimborsi)
    if ruolo == "delegato":
        if not user_data.indirizzo:
            raise HTTPException(status_code=400, detail="Indirizzo obbligatorio per i delegati")
        if not user_data.iban:
            raise HTTPException(status_code=400, detail="IBAN obbligatorio per i delegati")
    
    user_doc = {
        "email": email,
        "password_hash": hash_password(user_data.password),
        "nome": user_data.nome,
        "cognome": user_data.cognome,
        "telefono": user_data.telefono,
        "indirizzo": user_data.indirizzo if ruolo != "iscritto" else None,
        "citta": user_data.citta if ruolo != "iscritto" else None,
        "cap": user_data.cap if ruolo != "iscritto" else None,
        "iban": user_data.iban if ruolo != "iscritto" else None,
        "ruolo": ruolo,
        "sede_id": user_data.sede_id,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    result = await db.users.insert_one(user_doc)
    user_id = str(result.inserted_id)
    
    access_token = create_access_token(user_id, email)
    refresh_token = create_refresh_token(user_id)
    
    response.set_cookie(key="access_token", value=access_token, httponly=True, secure=False, samesite="lax", max_age=86400, path="/")
    response.set_cookie(key="refresh_token", value=refresh_token, httponly=True, secure=False, samesite="lax", max_age=604800, path="/")
    
    user_doc["id"] = user_id
    user_doc.pop("password_hash")
    user_doc.pop("_id", None)
    
    return user_doc

@api_router.post("/auth/login")
async def login(login_data: LoginRequest, request: Request, response: Response):
    email = login_data.email.lower()
    identifier = f"{request.client.host}:{email}"
    
    attempts = await db.login_attempts.find_one({"identifier": identifier})
    if attempts and attempts.get("count", 0) >= 5:
        lockout_time = attempts.get("last_attempt")
        if lockout_time:
            lockout_dt = datetime.fromisoformat(lockout_time) if isinstance(lockout_time, str) else lockout_time
            if datetime.now(timezone.utc) - lockout_dt < timedelta(minutes=15):
                raise HTTPException(status_code=429, detail="Troppi tentativi. Riprova tra 15 minuti.")
    
    user = await db.users.find_one({"email": email})
    if not user or not verify_password(login_data.password, user["password_hash"]):
        await db.login_attempts.update_one(
            {"identifier": identifier},
            {"$inc": {"count": 1}, "$set": {"last_attempt": datetime.now(timezone.utc).isoformat()}},
            upsert=True
        )
        raise HTTPException(status_code=401, detail="Credenziali non valide")
    
    await db.login_attempts.delete_one({"identifier": identifier})
    
    user_id = str(user["_id"])
    access_token = create_access_token(user_id, email)
    refresh_token = create_refresh_token(user_id)
    
    response.set_cookie(key="access_token", value=access_token, httponly=True, secure=False, samesite="lax", max_age=86400, path="/")
    response.set_cookie(key="refresh_token", value=refresh_token, httponly=True, secure=False, samesite="lax", max_age=604800, path="/")
    
    user_response = {
        "id": user_id,
        "email": user["email"],
        "nome": user["nome"],
        "cognome": user["cognome"],
        "telefono": user.get("telefono"),
        "indirizzo": user.get("indirizzo"),
        "citta": user.get("citta"),
        "cap": user.get("cap"),
        "iban": user.get("iban"),
        "ruolo": user["ruolo"],
        "sede_id": user.get("sede_id"),
        "created_at": user["created_at"]
    }
    
    if user.get("sede_id"):
        sede = await db.sedi.find_one({"_id": ObjectId(user["sede_id"])})
        if sede:
            user_response["sede_nome"] = sede["nome"]
    
    return user_response

@api_router.post("/auth/logout")
async def logout(response: Response):
    response.delete_cookie(key="access_token", path="/")
    response.delete_cookie(key="refresh_token", path="/")
    return {"message": "Logout effettuato"}

@api_router.get("/auth/me")
async def get_me(request: Request):
    user = await get_current_user(request)
    return user

@api_router.post("/auth/refresh")
async def refresh_token(request: Request, response: Response):
    token = request.cookies.get("refresh_token")
    if not token:
        raise HTTPException(status_code=401, detail="Token di refresh non trovato")
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Token non valido")
        user_id = payload["sub"]
        user = await db.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise HTTPException(status_code=401, detail="Utente non trovato")
        access_token = create_access_token(user_id, user["email"])
        response.set_cookie(key="access_token", value=access_token, httponly=True, secure=False, samesite="lax", max_age=86400, path="/")
        return {"message": "Token aggiornato"}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token scaduto")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token non valido")

# ==================== GOOGLE MAPS ====================

@api_router.post("/calcola-km")
async def calcola_km(data: CalcoloKmRequest, request: Request):
    await get_current_user(request)
    
    if not GOOGLE_MAPS_API_KEY:
        raise HTTPException(status_code=500, detail="Google Maps API non configurata")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://maps.googleapis.com/maps/api/directions/json",
                params={
                    "origin": data.origine,
                    "destination": data.destinazione,
                    "key": GOOGLE_MAPS_API_KEY,
                    "language": "it"
                }
            )
            result = response.json()
            
            if result.get("status") != "OK":
                raise HTTPException(status_code=400, detail=f"Impossibile calcolare il percorso: {result.get('status')}")
            
            # Get distance in meters and convert to km, round up
            distance_meters = result["routes"][0]["legs"][0]["distance"]["value"]
            distance_km = math.ceil(distance_meters / 1000)
            
            return {
                "km": distance_km,
                "origine": result["routes"][0]["legs"][0]["start_address"],
                "destinazione": result["routes"][0]["legs"][0]["end_address"],
                "durata": result["routes"][0]["legs"][0]["duration"]["text"]
            }
    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail=f"Errore di connessione: {str(e)}")

# ==================== SEDI ROUTES ====================

@api_router.get("/sedi")
async def get_sedi(request: Request):
    # Allow unauthenticated access for registration
    sedi = []
    async for sede in db.sedi.find({}, {"_id": 1, "nome": 1, "codice": 1, "indirizzo": 1, "tariffa_km": 1, "rimborso_pasti": 1, "rimborso_autostrada": 1}):
        sede["id"] = str(sede["_id"])
        sede.pop("_id")
        sedi.append(sede)
    return sedi

@api_router.post("/sedi")
async def create_sede(sede_data: SedeCreate, request: Request):
    user = await get_current_user(request)
    if user["ruolo"] not in ["superadmin"]:
        raise HTTPException(status_code=403, detail="Solo il SuperAdmin può creare sedi")
    
    existing = await db.sedi.find_one({"codice": sede_data.codice})
    if existing:
        raise HTTPException(status_code=400, detail="Codice sede già esistente")
    
    sede_doc = {
        "nome": sede_data.nome,
        "codice": sede_data.codice,
        "indirizzo": sede_data.indirizzo,
        "tariffa_km": sede_data.tariffa_km,
        "rimborso_pasti": sede_data.rimborso_pasti,
        "rimborso_autostrada": sede_data.rimborso_autostrada,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    result = await db.sedi.insert_one(sede_doc)
    sede_doc["id"] = str(result.inserted_id)
    sede_doc.pop("_id", None)
    return sede_doc

@api_router.put("/sedi/{sede_id}")
async def update_sede(sede_id: str, sede_data: SedeUpdate, request: Request):
    user = await get_current_user(request)
    if user["ruolo"] not in ["superadmin", "admin"]:
        raise HTTPException(status_code=403, detail="Permessi insufficienti")
    
    update_data = {k: v for k, v in sede_data.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="Nessun dato da aggiornare")
    
    result = await db.sedi.update_one({"_id": ObjectId(sede_id)}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Sede non trovata")
    
    return {"message": "Sede aggiornata"}

@api_router.delete("/sedi/{sede_id}")
async def delete_sede(sede_id: str, request: Request):
    user = await get_current_user(request)
    if user["ruolo"] not in ["superadmin"]:
        raise HTTPException(status_code=403, detail="Solo il SuperAdmin può eliminare sedi")
    
    result = await db.sedi.delete_one({"_id": ObjectId(sede_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Sede non trovata")
    
    return {"message": "Sede eliminata"}

# ==================== MOTIVI RIMBORSO ROUTES ====================

@api_router.get("/motivi-rimborso")
async def get_motivi_rimborso(request: Request):
    await get_current_user(request)
    motivi = []
    async for motivo in db.motivi_rimborso.find({}):
        motivo["id"] = str(motivo["_id"])
        motivo.pop("_id")
        motivi.append(motivo)
    return motivi

@api_router.post("/motivi-rimborso")
async def create_motivo_rimborso(motivo_data: MotivoRimborsoCreate, request: Request):
    user = await get_current_user(request)
    if user["ruolo"] not in ["superadmin"]:
        raise HTTPException(status_code=403, detail="Solo il SuperAdmin può gestire i motivi")
    
    motivo_doc = {
        "nome": motivo_data.nome,
        "descrizione": motivo_data.descrizione,
        "richiede_note": motivo_data.richiede_note,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    result = await db.motivi_rimborso.insert_one(motivo_doc)
    motivo_doc["id"] = str(result.inserted_id)
    motivo_doc.pop("_id", None)
    return motivo_doc

@api_router.put("/motivi-rimborso/{motivo_id}")
async def update_motivo_rimborso(motivo_id: str, motivo_data: MotivoRimborsoUpdate, request: Request):
    user = await get_current_user(request)
    if user["ruolo"] not in ["superadmin"]:
        raise HTTPException(status_code=403, detail="Solo il SuperAdmin può gestire i motivi")
    
    update_data = {k: v for k, v in motivo_data.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="Nessun dato da aggiornare")
    
    result = await db.motivi_rimborso.update_one({"_id": ObjectId(motivo_id)}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Motivo non trovato")
    
    return {"message": "Motivo aggiornato"}

@api_router.delete("/motivi-rimborso/{motivo_id}")
async def delete_motivo_rimborso(motivo_id: str, request: Request):
    user = await get_current_user(request)
    if user["ruolo"] not in ["superadmin"]:
        raise HTTPException(status_code=403, detail="Solo il SuperAdmin può gestire i motivi")
    
    result = await db.motivi_rimborso.delete_one({"_id": ObjectId(motivo_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Motivo non trovato")
    
    return {"message": "Motivo eliminato"}

# ==================== RIMBORSI ROUTES ====================

@api_router.get("/rimborsi")
async def get_rimborsi(request: Request, stato: Optional[str] = None, anno: Optional[int] = None):
    user = await get_current_user(request)
    
    query = {}
    
    if user["ruolo"] not in ["superadmin", "superuser"]:
        if user["ruolo"] in ["admin", "cassiere"]:
            query["sede_id"] = user.get("sede_id")
        else:
            query["user_id"] = user["id"]
    
    if stato:
        query["stato"] = stato
    
    if anno:
        query["data"] = {"$regex": f"^{anno}"}
    
    rimborsi = []
    async for rimborso in db.rimborsi.find(query).sort("created_at", -1):
        rimborso["id"] = str(rimborso["_id"])
        rimborso.pop("_id")
        
        rimborso_user = await db.users.find_one({"_id": ObjectId(rimborso["user_id"])})
        if rimborso_user:
            rimborso["user_nome"] = f"{rimborso_user['nome']} {rimborso_user['cognome']}"
        
        if rimborso.get("motivo_id"):
            motivo = await db.motivi_rimborso.find_one({"_id": ObjectId(rimborso["motivo_id"])})
            if motivo:
                rimborso["motivo_nome"] = motivo["nome"]
        
        rimborsi.append(rimborso)
    
    return rimborsi

@api_router.post("/rimborsi")
async def create_rimborso(rimborso_data: RimborsoCreate, request: Request):
    """
    POST /api/rimborsi
    Crea una nuova richiesta di rimborso
    
    Flusso:
    1. Verifica permessi (ruolo iscritto NON può creare rimborsi)
    2. Verifica note obbligatorie se motivo="Altro"
    3. Calcola totale: (KM * tariffa) + pasti + autostrada
    4. Crea notifica per admin se KM modificati manualmente
    
    Regole speciali:
    - Se km_modificati_manualmente=True, genera alert per admin
    - Ricevute pasti: nessun limite di costo (campo importo_pasti libero)
    """
    user = await get_current_user(request)
    
    # REGOLA: Solo ruoli con accesso alla sezione rimborsi possono crearli
    if user["ruolo"] not in ["delegato", "segreteria", "segretario", "admin", "superadmin"]:
        raise HTTPException(status_code=403, detail="Gli iscritti non possono richiedere rimborsi")
    
    # Check if motivo requires note (es: "Altro" richiede sempre note)
    motivo = await db.motivi_rimborso.find_one({"_id": ObjectId(rimborso_data.motivo_id)})
    if motivo and motivo.get("richiede_note") and not rimborso_data.note:
        raise HTTPException(status_code=400, detail="Per questo motivo le note sono obbligatorie")
    
    # Get sede tariffs (tariffa chilometrica della sede)
    sede = None
    if user.get("sede_id"):
        sede = await db.sedi.find_one({"_id": ObjectId(user["sede_id"])})
    
    tariffa_km = sede["tariffa_km"] if sede else 0.35
    
    # CALCOLO TOTALE RIMBORSO
    km_totali = rimborso_data.km_andata * (2 if rimborso_data.andata_ritorno else 1)
    importo_km = km_totali * tariffa_km
    importo_autostrada = rimborso_data.costo_autostrada if rimborso_data.uso_autostrada else 0
    importo_pasti = rimborso_data.importo_pasti  # Nessun limite, inserito dall'utente
    importo_totale = importo_km + importo_pasti + importo_autostrada
    
    rimborso_doc = {
        "user_id": user["id"],
        "sede_id": user.get("sede_id"),
        "data": rimborso_data.data,
        "motivo_id": rimborso_data.motivo_id,
        "indirizzo_partenza": rimborso_data.indirizzo_partenza,
        "indirizzo_partenza_tipo": rimborso_data.indirizzo_partenza_tipo,
        "indirizzo_arrivo": rimborso_data.indirizzo_arrivo,
        "km_andata": rimborso_data.km_andata,
        "km_calcolati": rimborso_data.km_calcolati,
        "km_modificati_manualmente": rimborso_data.km_modificati_manualmente,
        "andata_ritorno": rimborso_data.andata_ritorno,
        "km_totali": km_totali,
        "uso_autostrada": rimborso_data.uso_autostrada,
        "costo_autostrada": importo_autostrada,
        "importo_pasti": importo_pasti,
        "numero_partecipanti_pasto": rimborso_data.numero_partecipanti_pasto,
        "tariffa_km": tariffa_km,
        "importo_km": importo_km,
        "importo_totale": importo_totale,
        "note": rimborso_data.note,
        "stato": "in_attesa",
        "ricevute": [],
        "ricevute_spese": [],
        "km_approvati": None,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    result = await db.rimborsi.insert_one(rimborso_doc)
    rimborso_doc["id"] = str(result.inserted_id)
    rimborso_doc.pop("_id", None)
    
    # Notifica Admin + Cassiere della sede
    notifica_msg = f"{user['nome']} {user['cognome']} ha inviato una richiesta di rimborso di €{importo_totale:.2f}"
    if rimborso_data.km_modificati_manualmente:
        notifica_msg += " - ATTENZIONE: KM modificati manualmente!"
    
    await _notify_users_by_role(
        roles=["admin", "cassiere"],
        sede_id=user.get("sede_id"),
        notifica_data={
            "tipo": "rimborso",
            "titolo": "Nuova richiesta rimborso" + (" ⚠️ KM MODIFICATI" if rimborso_data.km_modificati_manualmente else ""),
            "messaggio": notifica_msg,
            "rimborso_id": str(result.inserted_id),
            "alert_km": rimborso_data.km_modificati_manualmente,
        },
        include_global=False
    )
    
    return rimborso_doc

@api_router.post("/rimborsi/{rimborso_id}/ricevute")
async def upload_ricevuta(rimborso_id: str, request: Request, file: UploadFile = File(...)):
    user = await get_current_user(request)
    
    rimborso = await db.rimborsi.find_one({"_id": ObjectId(rimborso_id)})
    if not rimborso:
        raise HTTPException(status_code=404, detail="Rimborso non trovato")
    
    if rimborso["user_id"] != user["id"] and user["ruolo"] not in ["admin", "superadmin"]:
        raise HTTPException(status_code=403, detail="Non autorizzato")
    
    if file.content_type not in ["application/pdf", "image/jpeg", "image/png", "image/jpg"]:
        raise HTTPException(status_code=400, detail="Formato file non supportato. Usa PDF, JPG o PNG")
    
    content = await file.read()
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File troppo grande. Max 5MB")
    
    file_id = str(uuid.uuid4())
    ext = file.filename.split(".")[-1] if "." in file.filename else "pdf"
    filename = f"{file_id}.{ext}"
    filepath = UPLOAD_DIR / filename
    
    async with aiofiles.open(filepath, "wb") as f:
        await f.write(content)
    
    ricevuta = {
        "id": file_id,
        "filename": file.filename,
        "path": filename,
        "uploaded_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.rimborsi.update_one(
        {"_id": ObjectId(rimborso_id)},
        {"$push": {"ricevute": ricevuta}}
    )
    
    return ricevuta

@api_router.post("/rimborsi/{rimborso_id}/ricevute-spese")
async def upload_ricevuta_spesa(rimborso_id: str, request: Request, file: UploadFile = File(...), tipo: str = Form(...), descrizione: str = Form(None)):
    """Upload ricevuta spesa (pasto, altro)"""
    user = await get_current_user(request)
    
    rimborso = await db.rimborsi.find_one({"_id": ObjectId(rimborso_id)})
    if not rimborso:
        raise HTTPException(status_code=404, detail="Rimborso non trovato")
    
    if rimborso["user_id"] != user["id"] and user["ruolo"] not in ["admin", "superadmin"]:
        raise HTTPException(status_code=403, detail="Non autorizzato")
    
    if file.content_type not in ["application/pdf", "image/jpeg", "image/png", "image/jpg"]:
        raise HTTPException(status_code=400, detail="Formato file non supportato")
    
    content = await file.read()
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File troppo grande. Max 5MB")
    
    file_id = str(uuid.uuid4())
    ext = file.filename.split(".")[-1] if "." in file.filename else "pdf"
    filename = f"spesa_{file_id}.{ext}"
    filepath = UPLOAD_DIR / filename
    
    async with aiofiles.open(filepath, "wb") as f:
        await f.write(content)
    
    ricevuta_spesa = {
        "id": file_id,
        "filename": file.filename,
        "path": filename,
        "tipo": tipo,
        "descrizione": descrizione,
        "uploaded_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.rimborsi.update_one(
        {"_id": ObjectId(rimborso_id)},
        {"$push": {"ricevute_spese": ricevuta_spesa}}
    )
    
    return ricevuta_spesa

@api_router.put("/rimborsi/{rimborso_id}")
async def update_rimborso(rimborso_id: str, rimborso_data: RimborsoUpdate, request: Request):
    user = await get_current_user(request)
    
    if user["ruolo"] not in ["admin", "cassiere", "superadmin"]:
        raise HTTPException(status_code=403, detail="Solo admin/cassiere può gestire i rimborsi")
    
    rimborso = await db.rimborsi.find_one({"_id": ObjectId(rimborso_id)})
    if not rimborso:
        raise HTTPException(status_code=404, detail="Rimborso non trovato")
    
    if user["ruolo"] in ["admin", "cassiere"] and rimborso.get("sede_id") != user.get("sede_id"):
        raise HTTPException(status_code=403, detail="Non autorizzato per questa sede")
    
    # Lo stato "pagato" può essere impostato SOLO via /contabile (con upload obbligatorio)
    if rimborso_data.stato == "pagato":
        raise HTTPException(
            status_code=400,
            detail="Per pagare un rimborso devi caricare la contabile tramite l'apposito endpoint /contabile"
        )
    
    update_data = {k: v for k, v in rimborso_data.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="Nessun dato da aggiornare")
    
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.rimborsi.update_one({"_id": ObjectId(rimborso_id)}, {"$set": update_data})
    
    # Notifica all'utente richiedente per approvato/rifiutato
    stato_msg = {
        "approvato": "approvata",
        "rifiutato": "rifiutata",
    }
    if rimborso_data.stato and rimborso_data.stato in stato_msg:
        await _notify_user(
            user_id=rimborso["user_id"],
            notifica_data={
                "sede_id": rimborso.get("sede_id"),
                "tipo": "rimborso",
                "titolo": f"Richiesta rimborso {stato_msg[rimborso_data.stato]}",
                "messaggio": f"La tua richiesta di rimborso del {rimborso['data']} è stata {stato_msg[rimborso_data.stato]}",
                "rimborso_id": rimborso_id,
            }
        )
    
    return {"message": "Rimborso aggiornato"}

@api_router.post("/rimborsi/{rimborso_id}/contabile")
async def upload_contabile(rimborso_id: str, request: Request, file: UploadFile = File(...)):
    user = await get_current_user(request)
    
    if user["ruolo"] not in ["admin", "cassiere", "superadmin"]:
        raise HTTPException(status_code=403, detail="Solo admin/cassiere può caricare contabili")
    
    rimborso = await db.rimborsi.find_one({"_id": ObjectId(rimborso_id)})
    if not rimborso:
        raise HTTPException(status_code=404, detail="Rimborso non trovato")
    
    if user["ruolo"] in ["admin", "cassiere"] and rimborso.get("sede_id") != user.get("sede_id"):
        raise HTTPException(status_code=403, detail="Non autorizzato per questa sede")
    
    if rimborso.get("stato") == "rifiutato":
        raise HTTPException(status_code=400, detail="Impossibile pagare un rimborso rifiutato")
    
    if rimborso.get("stato") == "pagato":
        raise HTTPException(status_code=400, detail="Rimborso già pagato")
    
    # Validazione file
    if file.content_type not in ["application/pdf", "image/jpeg", "image/png", "image/jpg"]:
        raise HTTPException(status_code=400, detail="Formato file non supportato (solo PDF, JPG, PNG)")
    
    content = await file.read()
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File troppo grande. Max 5MB")
    
    file_id = str(uuid.uuid4())
    ext = file.filename.split(".")[-1] if "." in file.filename else "pdf"
    filename = f"contabile_{file_id}.{ext}"
    filepath = UPLOAD_DIR / filename
    
    async with aiofiles.open(filepath, "wb") as f:
        await f.write(content)
    
    # Se rimborso in_attesa, salta direttamente a pagato (auto-approvazione + pagamento)
    pagamento_diretto = rimborso.get("stato") == "in_attesa"
    
    await db.rimborsi.update_one(
        {"_id": ObjectId(rimborso_id)},
        {"$set": {
            "stato": "pagato",
            "contabile": {"filename": file.filename, "path": filename},
            "pagato_at": datetime.now(timezone.utc).isoformat(),
            "pagato_by": user["id"],
            "pagato_by_nome": f"{user['nome']} {user['cognome']}"
        }}
    )
    
    # Notifica all'utente richiedente
    if pagamento_diretto:
        msg_user = f"Il tuo rimborso del {rimborso['data']} è stato approvato e pagato. Contabile disponibile."
        titolo_user = "Rimborso approvato e pagato"
    else:
        msg_user = f"Il tuo rimborso del {rimborso['data']} è stato pagato. Contabile disponibile."
        titolo_user = "Rimborso pagato"
    
    await _notify_user(
        user_id=rimborso["user_id"],
        notifica_data={
            "sede_id": rimborso.get("sede_id"),
            "tipo": "rimborso",
            "titolo": titolo_user,
            "messaggio": msg_user,
            "rimborso_id": rimborso_id,
        }
    )
    
    # Notifica anche Admin + Cassiere della sede (escluso chi ha appena pagato)
    notifiche_admin = []
    async for u in db.users.find(
        {"ruolo": {"$in": ["admin", "cassiere"]}, "sede_id": rimborso.get("sede_id"), "_id": {"$ne": ObjectId(user["id"])}},
        {"_id": 1}
    ):
        notifiche_admin.append({
            "user_id": str(u["_id"]),
            "sede_id": rimborso.get("sede_id"),
            "tipo": "rimborso",
            "titolo": "Rimborso pagato",
            "messaggio": f"{user['nome']} {user['cognome']} ha pagato il rimborso del {rimborso['data']}",
            "rimborso_id": rimborso_id,
            "letto": False,
            "created_at": datetime.now(timezone.utc).isoformat()
        })
    if notifiche_admin:
        await db.notifiche.insert_many(notifiche_admin)
    
    return {"message": "Contabile caricata e rimborso pagato"}

# ==================== ANNUNCI (BULLETIN BOARD) ROUTES ====================

@api_router.get("/annunci")
async def get_annunci(request: Request):
    user = await get_current_user(request)
    
    query = {}
    if user["ruolo"] not in ["superadmin", "superuser"]:
        query["$or"] = [
            {"sede_id": user.get("sede_id")},
            {"sede_id": None}
        ]
    
    annunci = []
    async for annuncio in db.annunci.find(query).sort("created_at", -1).limit(50):
        annuncio["id"] = str(annuncio["_id"])
        annuncio.pop("_id")
        annunci.append(annuncio)
    
    return annunci

@api_router.post("/annunci")
async def create_annuncio(
    request: Request,
    titolo: str = Form(...),
    contenuto: str = Form(...),
    link_documento: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None)
):
    user = await get_current_user(request)
    
    if user["ruolo"] not in ["segreteria", "segretario", "admin", "superadmin"]:
        raise HTTPException(status_code=403, detail="Permessi insufficienti")
    
    allegato_filename = None
    allegato_path = None
    
    # Gestione upload file opzionale
    if file and file.filename:
        if file.content_type not in ["application/pdf", "image/jpeg", "image/png", "image/jpg"]:
            raise HTTPException(status_code=400, detail="Formato file non supportato (solo PDF, JPG, PNG)")
        
        content = await file.read()
        if len(content) > 5 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File troppo grande. Max 5MB")
        
        file_id = str(uuid.uuid4())
        ext = file.filename.split(".")[-1] if "." in file.filename else "pdf"
        stored_name = f"annuncio_{file_id}.{ext}"
        filepath = UPLOAD_DIR / stored_name
        
        async with aiofiles.open(filepath, "wb") as f:
            await f.write(content)
        
        allegato_filename = file.filename
        allegato_path = stored_name
    
    annuncio_doc = {
        "titolo": titolo,
        "contenuto": contenuto,
        "link_documento": link_documento if link_documento else None,
        "allegato_filename": allegato_filename,
        "allegato_path": allegato_path,
        "sede_id": user.get("sede_id") if user["ruolo"] != "superadmin" else None,
        "autore_id": user["id"],
        "autore_nome": f"{user['nome']} {user['cognome']}",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    result = await db.annunci.insert_one(annuncio_doc)
    annuncio_doc["id"] = str(result.inserted_id)
    annuncio_doc.pop("_id", None)
    
    # Notifica TUTTI gli utenti della sede (o globali se sede_id None)
    await _notify_all_in_sede(
        sede_id=annuncio_doc["sede_id"],
        notifica_data={
            "sede_id": annuncio_doc["sede_id"],
            "tipo": "annuncio",
            "titolo": "Nuovo comunicato in bacheca",
            "messaggio": f"{annuncio_doc['autore_nome']}: {titolo}",
            "annuncio_id": annuncio_doc["id"],
        },
        exclude_user_id=user["id"]
    )
    
    return annuncio_doc

@api_router.get("/annunci/{annuncio_id}/download")
async def download_allegato_annuncio(annuncio_id: str, request: Request):
    user = await get_current_user(request)
    
    annuncio = await db.annunci.find_one({"_id": ObjectId(annuncio_id)})
    if not annuncio:
        raise HTTPException(status_code=404, detail="Annuncio non trovato")
    
    if not annuncio.get("allegato_path"):
        raise HTTPException(status_code=404, detail="Nessun allegato per questo annuncio")
    
    # Controllo sede per utenti non super
    if user["ruolo"] not in ["superadmin", "superuser"]:
        if annuncio.get("sede_id") and annuncio["sede_id"] != user.get("sede_id"):
            raise HTTPException(status_code=403, detail="Non autorizzato")
    
    filepath = UPLOAD_DIR / annuncio["allegato_path"]
    if not filepath.exists():
        raise HTTPException(status_code=404, detail="File non trovato")
    
    return FileResponse(filepath, filename=annuncio.get("allegato_filename", "allegato"))

@api_router.delete("/annunci/{annuncio_id}")
async def delete_annuncio(annuncio_id: str, request: Request):
    user = await get_current_user(request)
    
    if user["ruolo"] not in ["segreteria", "segretario", "admin", "superadmin"]:
        raise HTTPException(status_code=403, detail="Permessi insufficienti")
    
    annuncio = await db.annunci.find_one({"_id": ObjectId(annuncio_id)})
    if not annuncio:
        raise HTTPException(status_code=404, detail="Annuncio non trovato")
    
    # Rimuovi il file fisico se presente
    if annuncio.get("allegato_path"):
        filepath = UPLOAD_DIR / annuncio["allegato_path"]
        if filepath.exists():
            filepath.unlink()
    
    await db.annunci.delete_one({"_id": ObjectId(annuncio_id)})
    
    return {"message": "Annuncio eliminato"}

# ==================== CONTATTI / LINK SIDEBAR ROUTES ====================

VALID_CONTATTO_TIPI = ["link", "whatsapp", "telegram", "email", "telefono"]
EDIT_CONTATTO_ROLES = ["admin", "segretario", "segreteria", "superadmin"]


@api_router.get("/contatti")
async def get_contatti(request: Request):
    """Restituisce i contatti della sede dell'utente. SuperAdmin/SuperUser vede tutti."""
    user = await get_current_user(request)
    
    query = {}
    if user["ruolo"] not in ["superadmin", "superuser"]:
        query["sede_id"] = user.get("sede_id")
    
    contatti = []
    async for c in db.contatti.find(query).sort("ordine", 1):
        c["id"] = str(c["_id"])
        c.pop("_id")
        contatti.append(c)
    
    return contatti


@api_router.post("/contatti")
async def create_contatto(contatto_data: ContattoCreate, request: Request):
    user = await get_current_user(request)
    
    if user["ruolo"] not in EDIT_CONTATTO_ROLES:
        raise HTTPException(status_code=403, detail="Permessi insufficienti")
    
    if contatto_data.tipo not in VALID_CONTATTO_TIPI:
        raise HTTPException(status_code=400, detail=f"Tipo non valido. Usa: {', '.join(VALID_CONTATTO_TIPI)}")
    
    contatto_doc = {
        "titolo": contatto_data.titolo,
        "descrizione": contatto_data.descrizione,
        "tipo": contatto_data.tipo,
        "valore": contatto_data.valore,
        "sede_id": user.get("sede_id"),
        "ordine": 0,
        "created_by": user["id"],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    result = await db.contatti.insert_one(contatto_doc)
    contatto_doc["id"] = str(result.inserted_id)
    contatto_doc.pop("_id", None)
    
    return contatto_doc


@api_router.put("/contatti/{contatto_id}")
async def update_contatto(contatto_id: str, contatto_data: ContattoUpdate, request: Request):
    user = await get_current_user(request)
    
    if user["ruolo"] not in EDIT_CONTATTO_ROLES:
        raise HTTPException(status_code=403, detail="Permessi insufficienti")
    
    contatto = await db.contatti.find_one({"_id": ObjectId(contatto_id)})
    if not contatto:
        raise HTTPException(status_code=404, detail="Contatto non trovato")
    
    # Solo stessa sede (eccetto superadmin)
    if user["ruolo"] != "superadmin" and contatto.get("sede_id") != user.get("sede_id"):
        raise HTTPException(status_code=403, detail="Non autorizzato per questa sede")
    
    update_data = {k: v for k, v in contatto_data.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="Nessun dato da aggiornare")
    
    if "tipo" in update_data and update_data["tipo"] not in VALID_CONTATTO_TIPI:
        raise HTTPException(status_code=400, detail=f"Tipo non valido. Usa: {', '.join(VALID_CONTATTO_TIPI)}")
    
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.contatti.update_one({"_id": ObjectId(contatto_id)}, {"$set": update_data})
    
    return {"message": "Contatto aggiornato"}


@api_router.delete("/contatti/{contatto_id}")
async def delete_contatto(contatto_id: str, request: Request):
    user = await get_current_user(request)
    
    if user["ruolo"] not in EDIT_CONTATTO_ROLES:
        raise HTTPException(status_code=403, detail="Permessi insufficienti")
    
    contatto = await db.contatti.find_one({"_id": ObjectId(contatto_id)})
    if not contatto:
        raise HTTPException(status_code=404, detail="Contatto non trovato")
    
    if user["ruolo"] != "superadmin" and contatto.get("sede_id") != user.get("sede_id"):
        raise HTTPException(status_code=403, detail="Non autorizzato per questa sede")
    
    await db.contatti.delete_one({"_id": ObjectId(contatto_id)})
    
    return {"message": "Contatto eliminato"}



# ==================== DOCUMENTI ROUTES ====================

@api_router.get("/documenti")
async def get_documenti(request: Request, categoria: Optional[str] = None):
    user = await get_current_user(request)
    
    query = {}
    if user["ruolo"] not in ["superadmin", "superuser"]:
        query["$or"] = [
            {"sede_id": user.get("sede_id")},
            {"sede_id": None}
        ]
    
    if categoria:
        query["categoria"] = categoria
    
    documenti = []
    async for doc in db.documenti.find(query).sort("created_at", -1):
        doc["id"] = str(doc["_id"])
        doc.pop("_id")
        documenti.append(doc)
    
    return documenti

@api_router.post("/documenti")
async def upload_documento(
    request: Request,
    file: UploadFile = File(...),
    nome: str = Form(...),
    categoria: str = Form(...),
    descrizione: str = Form(None)
):
    user = await get_current_user(request)
    
    if user["ruolo"] not in ["segreteria", "segretario", "admin", "superadmin"]:
        raise HTTPException(status_code=403, detail="Permessi insufficienti")
    
    if file.content_type not in ["application/pdf", "image/jpeg", "image/png", "image/jpg"]:
        raise HTTPException(status_code=400, detail="Formato file non supportato")
    
    content = await file.read()
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File troppo grande. Max 5MB")
    
    file_id = str(uuid.uuid4())
    ext = file.filename.split(".")[-1] if "." in file.filename else "pdf"
    filename = f"doc_{file_id}.{ext}"
    filepath = UPLOAD_DIR / filename
    
    async with aiofiles.open(filepath, "wb") as f:
        await f.write(content)
    
    doc_record = {
        "nome": nome,
        "categoria": categoria,
        "descrizione": descrizione,
        "filename": file.filename,
        "path": filename,
        "sede_id": user.get("sede_id") if user["ruolo"] != "superadmin" else None,
        "uploaded_by": user["id"],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    result = await db.documenti.insert_one(doc_record)
    doc_record["id"] = str(result.inserted_id)
    doc_record.pop("_id", None)
    
    # Notifica TUTTI gli utenti della sede (o globali se sede_id None)
    await _notify_all_in_sede(
        sede_id=doc_record["sede_id"],
        notifica_data={
            "sede_id": doc_record["sede_id"],
            "tipo": "documento",
            "titolo": "Nuovo documento disponibile",
            "messaggio": f"{user['nome']} {user['cognome']} ha caricato: {nome}",
            "documento_id": doc_record["id"],
        },
        exclude_user_id=user["id"]
    )
    
    return doc_record

@api_router.get("/documenti/{doc_id}/download")
async def download_documento(doc_id: str, request: Request):
    user = await get_current_user(request)
    
    doc = await db.documenti.find_one({"_id": ObjectId(doc_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Documento non trovato")
    
    if user["ruolo"] not in ["superadmin", "superuser"]:
        if doc.get("sede_id") and doc["sede_id"] != user.get("sede_id"):
            raise HTTPException(status_code=403, detail="Non autorizzato")
    
    filepath = UPLOAD_DIR / doc["path"]
    if not filepath.exists():
        raise HTTPException(status_code=404, detail="File non trovato")
    
    return FileResponse(filepath, filename=doc["filename"])

@api_router.delete("/documenti/{doc_id}")
async def delete_documento(doc_id: str, request: Request):
    user = await get_current_user(request)
    
    if user["ruolo"] not in ["segreteria", "segretario", "admin", "superadmin"]:
        raise HTTPException(status_code=403, detail="Permessi insufficienti")
    
    doc = await db.documenti.find_one({"_id": ObjectId(doc_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Documento non trovato")
    
    filepath = UPLOAD_DIR / doc["path"]
    if filepath.exists():
        filepath.unlink()
    
    await db.documenti.delete_one({"_id": ObjectId(doc_id)})
    
    return {"message": "Documento eliminato"}

# ==================== NOTIFICHE ROUTES ====================

@api_router.get("/notifiche")
async def get_notifiche(request: Request):
    user = await get_current_user(request)
    
    # Notifiche dirette all'utente + retrocompatibilità con notifiche vecchie (user_id=None, sede_id specifica)
    query = {"$or": [
        {"user_id": user["id"]},
        {"user_id": None, "sede_id": user.get("sede_id")}
    ]}
    
    notifiche = []
    async for notifica in db.notifiche.find(query).sort("created_at", -1).limit(50):
        notifica["id"] = str(notifica["_id"])
        notifica.pop("_id")
        notifiche.append(notifica)
    
    return notifiche

@api_router.put("/notifiche/{notifica_id}/letto")
async def mark_notifica_letta(notifica_id: str, request: Request):
    user = await get_current_user(request)
    
    await db.notifiche.update_one(
        {"_id": ObjectId(notifica_id)},
        {"$set": {"letto": True}}
    )
    
    return {"message": "Notifica segnata come letta"}

@api_router.put("/notifiche/letto-tutte")
async def mark_all_notifiche_lette(request: Request):
    user = await get_current_user(request)
    
    query = {"$or": [
        {"user_id": user["id"]},
        {"user_id": None, "sede_id": user.get("sede_id")}
    ]}
    
    await db.notifiche.update_many(query, {"$set": {"letto": True}})
    
    return {"message": "Tutte le notifiche segnate come lette"}

# ==================== USERS MANAGEMENT ====================

@api_router.get("/users")
async def get_users(request: Request):
    user = await get_current_user(request)
    
    if user["ruolo"] not in ["admin", "cassiere", "superadmin", "superuser", "segretario"]:
        raise HTTPException(status_code=403, detail="Permessi insufficienti")
    
    query = {}
    if user["ruolo"] not in ["superadmin", "superuser"]:
        query["sede_id"] = user.get("sede_id")
    
    users = []
    async for u in db.users.find(query, {"password_hash": 0}):
        u["id"] = str(u["_id"])
        u.pop("_id")
        if u.get("sede_id"):
            sede = await db.sedi.find_one({"_id": ObjectId(u["sede_id"])})
            if sede:
                u["sede_nome"] = sede["nome"]
        users.append(u)
    
    return users

@api_router.put("/users/{user_id}")
async def update_user(user_id: str, user_data: UserUpdate, request: Request):
    current_user = await get_current_user(request)
    
    if user_id != current_user["id"] and current_user["ruolo"] not in ["admin", "superadmin"]:
        raise HTTPException(status_code=403, detail="Permessi insufficienti")
    
    update_data = {k: v for k, v in user_data.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="Nessun dato da aggiornare")
    
    await db.users.update_one({"_id": ObjectId(user_id)}, {"$set": update_data})
    
    return {"message": "Utente aggiornato"}

@api_router.put("/users/{user_id}/ruolo")
async def update_user_role(user_id: str, request: Request, ruolo: str = Form(...)):
    current_user = await get_current_user(request)
    
    if current_user["ruolo"] not in ["admin", "superadmin"]:
        raise HTTPException(status_code=403, detail="Permessi insufficienti")
    
    valid_roles = ["iscritto", "delegato", "segreteria", "segretario", "cassiere", "admin"]
    if current_user["ruolo"] == "superadmin":
        valid_roles.extend(["superuser", "superadmin"])
    
    if ruolo not in valid_roles:
        raise HTTPException(status_code=400, detail="Ruolo non valido")
    
    await db.users.update_one({"_id": ObjectId(user_id)}, {"$set": {"ruolo": ruolo}})
    
    return {"message": "Ruolo aggiornato"}

# ==================== REPORTS ====================

@api_router.get("/reports/rimborsi-annuali")
async def get_report_rimborsi_annuali(request: Request, anno: int):
    user = await get_current_user(request)
    
    if user["ruolo"] not in ["admin", "cassiere", "superadmin", "superuser"]:
        raise HTTPException(status_code=403, detail="Permessi insufficienti")
    
    query = {"data": {"$regex": f"^{anno}"}}
    if user["ruolo"] not in ["superadmin", "superuser"]:
        query["sede_id"] = user.get("sede_id")
    
    pipeline = [
        {"$match": query},
        {"$group": {
            "_id": "$user_id",
            "totale_rimborsi": {"$sum": 1},
            "totale_importo": {"$sum": "$importo_totale"},
            "totale_km": {"$sum": "$km_totali"},
            "rimborsi_pagati": {"$sum": {"$cond": [{"$eq": ["$stato", "pagato"]}, 1, 0]}},
            "importo_pagato": {"$sum": {"$cond": [{"$eq": ["$stato", "pagato"]}, "$importo_totale", 0]}}
        }}
    ]
    
    results = []
    async for result in db.rimborsi.aggregate(pipeline):
        user_doc = await db.users.find_one({"_id": ObjectId(result["_id"])})
        if user_doc:
            result["user_nome"] = f"{user_doc['nome']} {user_doc['cognome']}"
            result["user_email"] = user_doc["email"]
            result["user_iban"] = user_doc.get("iban", "")
        results.append(result)
    
    return results

@api_router.get("/reports/rimborsi-export")
async def export_rimborsi(request: Request, anno: int, formato: str = "csv"):
    user = await get_current_user(request)
    
    if user["ruolo"] not in ["admin", "cassiere", "superadmin", "superuser"]:
        raise HTTPException(status_code=403, detail="Permessi insufficienti")
    
    query = {"data": {"$regex": f"^{anno}"}}
    if user["ruolo"] not in ["superadmin", "superuser"]:
        query["sede_id"] = user.get("sede_id")
    
    rimborsi = []
    async for rimborso in db.rimborsi.find(query).sort("data", 1):
        rimborso_user = await db.users.find_one({"_id": ObjectId(rimborso["user_id"])})
        motivo = await db.motivi_rimborso.find_one({"_id": ObjectId(rimborso["motivo_id"])}) if rimborso.get("motivo_id") else None
        
        rimborsi.append({
            "Data": rimborso["data"],
            "Utente": f"{rimborso_user['nome']} {rimborso_user['cognome']}" if rimborso_user else "N/A",
            "Email": rimborso_user["email"] if rimborso_user else "",
            "IBAN": rimborso_user.get("iban", "") if rimborso_user else "",
            "Motivo": motivo["nome"] if motivo else "N/A",
            "Partenza": rimborso["indirizzo_partenza"],
            "Arrivo": rimborso["indirizzo_arrivo"],
            "KM Totali": rimborso["km_totali"],
            "Importo KM": f"{rimborso['importo_km']:.2f}",
            "Importo Pasti": f"{rimborso.get('importo_pasti', 0):.2f}",
            "Autostrada": f"{rimborso.get('costo_autostrada', 0):.2f}",
            "Totale": f"{rimborso['importo_totale']:.2f}",
            "Stato": rimborso["stato"],
            "Note": rimborso.get("note", "")
        })
    
    if formato == "csv":
        output = io.StringIO()
        if rimborsi:
            writer = csv.DictWriter(output, fieldnames=rimborsi[0].keys())
            writer.writeheader()
            writer.writerows(rimborsi)
        
        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=rimborsi_{anno}.csv"}
        )
    else:
        return rimborsi

# ==================== STARTUP ====================

@app.on_event("startup")
async def startup():
    await db.users.create_index("email", unique=True)
    await db.sedi.create_index("codice", unique=True)
    await db.login_attempts.create_index("identifier")
    
    admin_email = os.environ.get("ADMIN_EMAIL", "superadmin@sla.it")
    admin_password = os.environ.get("ADMIN_PASSWORD", "SlaAdmin2024!")
    
    existing = await db.users.find_one({"email": admin_email})
    if existing is None:
        hashed = hash_password(admin_password)
        await db.users.insert_one({
            "email": admin_email,
            "password_hash": hashed,
            "nome": "Super",
            "cognome": "Admin",
            "ruolo": "superadmin",
            "sede_id": None,
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        logger.info(f"SuperAdmin creato: {admin_email}")
    elif not verify_password(admin_password, existing["password_hash"]):
        await db.users.update_one(
            {"email": admin_email},
            {"$set": {"password_hash": hash_password(admin_password)}}
        )
        logger.info("Password SuperAdmin aggiornata")
    
    # Seed default motivi rimborso with richiede_note flag
    motivi_default = [
        {"nome": "RSA", "richiede_note": False},
        {"nome": "Sede", "richiede_note": False},
        {"nome": "Altro", "richiede_note": True}
    ]
    for motivo in motivi_default:
        existing_motivo = await db.motivi_rimborso.find_one({"nome": motivo["nome"]})
        if not existing_motivo:
            await db.motivi_rimborso.insert_one({
                "nome": motivo["nome"],
                "descrizione": None,
                "richiede_note": motivo["richiede_note"],
                "created_at": datetime.now(timezone.utc).isoformat()
            })
    
    # Remove old motivi that are not in the new list
    await db.motivi_rimborso.delete_many({"nome": {"$nin": ["RSA", "Sede", "Altro"]}})
    
    # Only keep A22 sede
    await db.sedi.delete_many({"codice": {"$nin": ["A22"]}})
    
    # Ensure A22 exists
    existing_a22 = await db.sedi.find_one({"codice": "A22"})
    if not existing_a22:
        await db.sedi.insert_one({
            "nome": "Autostrada del Brennero",
            "codice": "A22",
            "indirizzo": None,
            "tariffa_km": 0.35,
            "rimborso_pasti": 15.0,
            "rimborso_autostrada": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        })
    
    creds_path = Path("/app/memory/test_credentials.md")
    creds_path.parent.mkdir(exist_ok=True)
    creds_path.write_text(f"""# Test Credentials

## SuperAdmin
- Email: {admin_email}
- Password: {admin_password}
- Ruolo: superadmin

## Auth Endpoints
- POST /api/auth/register
- POST /api/auth/login
- POST /api/auth/logout
- GET /api/auth/me
- POST /api/auth/refresh

## Sedi
- A22 - Autostrada del Brennero

## Motivi Rimborso
- RSA (note non obbligatorie)
- Sede (note non obbligatorie)
- Altro (note OBBLIGATORIE)
""")
    
    logger.info("Database inizializzato")

@app.on_event("shutdown")
async def shutdown():
    client.close()

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.environ.get("FRONTEND_URL", "http://localhost:3000")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
