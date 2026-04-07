\"\"\"\n==============================================\nSLA PORTALE - Server FastAPI\n==============================================\n\nEntry point dell'applicazione backend.\nGestisce tutte le API per il portale rimborsi SLA.\n\nPer avviare in sviluppo:\n    uvicorn server:app --reload --port 8001\n\nPer avviare in produzione:\n    uvicorn server:app --host 0.0.0.0 --port 8001\n\nDocumentazione API automatica:\n    http://localhost:8001/docs (Swagger)\n    http://localhost:8001/redoc (ReDoc)\n\n==============================================\n\"\"\"

# Carica variabili ambiente PRIMA di tutto
from dotenv import load_dotenv
from pathlib import Path
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Import standard library
import os
import logging
from datetime import datetime, timezone, timedelta
import uuid
import math
import csv
import io

# Import FastAPI
from fastapi import FastAPI, APIRouter, HTTPException, Request, Response, Depends, UploadFile, File, Form
from fastapi.responses import FileResponse, StreamingResponse
from starlette.middleware.cors import CORSMiddleware

# Import database
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

# Import security
import bcrypt
import jwt
import httpx
import aiofiles

# ==============================================
# CONFIGURAZIONE
# ==============================================

# MongoDB
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'sla_sindacato')
client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

# JWT
JWT_SECRET = os.environ.get('JWT_SECRET', 'CAMBIA-QUESTA-CHIAVE')
JWT_ALGORITHM = "HS256"

# Google Maps
GOOGLE_MAPS_API_KEY = os.environ.get('GOOGLE_MAPS_API_KEY', '')

# Upload
UPLOAD_DIR = ROOT_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

# Logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ==============================================
# APP FASTAPI
# ==============================================

app = FastAPI(
    title="SLA Sindacato - Portale Rimborsi",
    description="API per gestione rimborsi e comunicazioni SLA",
    version="1.0.0"
)

api_router = APIRouter(prefix="/api")

# ==============================================
# MODELLI PYDANTIC
# ==============================================
# Definiscono la struttura dei dati in input/output

from pydantic import BaseModel, EmailStr
from typing import Optional

class UserCreate(BaseModel):
    """Dati per registrazione utente"""
    email: EmailStr
    password: str
    nome: str
    cognome: str
    telefono: Optional[str] = None
    indirizzo: Optional[str] = None
    citta: Optional[str] = None
    cap: Optional[str] = None
    iban: Optional[str] = None
    sede_id: Optional[str] = None
    ruolo: str = "iscritto"

class UserUpdate(BaseModel):
    """Campi aggiornabili profilo"""
    nome: Optional[str] = None
    cognome: Optional[str] = None
    telefono: Optional[str] = None
    indirizzo: Optional[str] = None
    citta: Optional[str] = None
    cap: Optional[str] = None
    iban: Optional[str] = None

class LoginRequest(BaseModel):
    """Dati login"""
    email: EmailStr
    password: str

class SedeCreate(BaseModel):
    """Crea nuova sede/concessionaria"""
    nome: str
    codice: str
    indirizzo: Optional[str] = None
    tariffa_km: float = 0.35
    rimborso_pasti: float = 15.0
    rimborso_autostrada: bool = True

class SedeUpdate(BaseModel):
    """Aggiorna sede esistente"""
    nome: Optional[str] = None
    indirizzo: Optional[str] = None
    tariffa_km: Optional[float] = None
    rimborso_pasti: Optional[float] = None
    rimborso_autostrada: Optional[bool] = None

class MotivoRimborsoCreate(BaseModel):
    """Crea motivo/causale rimborso"""
    nome: str
    descrizione: Optional[str] = None
    richiede_note: bool = False

class MotivoRimborsoUpdate(BaseModel):
    """Aggiorna motivo esistente"""
    nome: Optional[str] = None
    descrizione: Optional[str] = None
    richiede_note: Optional[bool] = None

class RimborsoCreate(BaseModel):
    \"\"\"
    Crea nuova richiesta rimborso.
    
    Campi principali:
    - data: Data della trasferta
    - motivo_id: Riferimento al motivo (RSA, Sede, Altro...)
    - indirizzo_*: Percorso effettuato
    - km_*: Chilometri (calcolati o manuali)
    - importo_pasti: Totale spese pasti
    \"\"\"
    data: str
    motivo_id: str
    indirizzo_partenza: str
    indirizzo_partenza_tipo: str = "manuale"
    indirizzo_arrivo: str
    km_andata: float
    km_calcolati: Optional[float] = None
    km_modificati_manualmente: bool = False
    andata_ritorno: bool = True
    uso_autostrada: bool = False
    costo_autostrada: float = 0
    importo_pasti: float = 0
    numero_partecipanti_pasto: int = 0
    note: Optional[str] = None

class RimborsoUpdate(BaseModel):
    """Aggiorna stato rimborso (solo Admin)"""
    stato: Optional[str] = None
    note_admin: Optional[str] = None
    km_approvati: Optional[bool] = None

class CalcoloKmRequest(BaseModel):
    """Richiesta calcolo KM con Google Maps"""
    origine: str
    destinazione: str

class AnnuncioCreate(BaseModel):
    """Crea annuncio in bacheca"""
    titolo: str
    contenuto: str
    link_documento: Optional[str] = None

# ==============================================
# FUNZIONI AUTENTICAZIONE
# ==============================================

def hash_password(password: str) -> str:
    """Hash password con bcrypt (salt automatico)"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica password contro hash"""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"), 
        hashed_password.encode("utf-8")
    )

def create_access_token(user_id: str, email: str) -> str:
    """Crea JWT access token (durata: 24 ore)"""
    payload = {
        "sub": user_id,
        "email": email,
        "exp": datetime.now(timezone.utc) + timedelta(hours=24),
        "type": "access"
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def create_refresh_token(user_id: str) -> str:
    """Crea JWT refresh token (durata: 7 giorni)"""
    payload = {
        "sub": user_id,
        "exp": datetime.now(timezone.utc) + timedelta(days=7),
        "type": "refresh"
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

async def get_current_user(request: Request) -> dict:
    \"\"\"
    Middleware: Estrae utente dal token JWT.
    
    Cerca token in:
    1. Cookie 'access_token'
    2. Header 'Authorization: Bearer <token>'
    
    Solleva HTTPException 401 se non autenticato.
    \"\"\"
    # Cerca token
    token = request.cookies.get("access_token")
    if not token:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
    
    if not token:
        raise HTTPException(status_code=401, detail="Non autenticato")
    
    try:
        # Decodifica JWT
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Token non valido")
        
        # Carica utente
        user = await db.users.find_one({"_id": ObjectId(payload["sub"])})
        if not user:
            raise HTTPException(status_code=401, detail="Utente non trovato")
        
        # Prepara risposta
        user["id"] = str(user["_id"])
        user.pop("_id", None)
        user.pop("password_hash", None)
        
        # Aggiungi nome sede
        if user.get("sede_id"):
            sede = await db.sedi.find_one({"_id": ObjectId(user["sede_id"])})
            if sede:
                user["sede_nome"] = sede["nome"]
        
        return user
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token scaduto")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token non valido")

# ==============================================
# ROUTE: AUTENTICAZIONE
# ==============================================

@api_router.post("/auth/register", tags=["Autenticazione"])
async def register(user_data: UserCreate, response: Response):
    \"\"\"
    Registra nuovo utente.
    
    - Ruoli disponibili in registrazione: iscritto, delegato
    - Per delegato: indirizzo e IBAN obbligatori
    - Ruoli superiori assegnati da Admin
    \"\"\"
    email = user_data.email.lower()
    
    # Check email esistente
    existing = await db.users.find_one({"email": email})
    if existing:
        raise HTTPException(status_code=400, detail="Email già registrata")
    
    # Valida ruolo (solo iscritto/delegato per auto-registrazione)
    allowed_roles = ["iscritto", "delegato"]
    ruolo = user_data.ruolo if user_data.ruolo in allowed_roles else "iscritto"
    
    # Valida sede
    if user_data.sede_id:
        sede = await db.sedi.find_one({"_id": ObjectId(user_data.sede_id)})
        if not sede:
            raise HTTPException(status_code=400, detail="Sede non trovata")
    
    # Per delegato: indirizzo e IBAN obbligatori
    if ruolo == "delegato":
        if not user_data.indirizzo:
            raise HTTPException(status_code=400, detail="Indirizzo obbligatorio per i delegati")
        if not user_data.iban:
            raise HTTPException(status_code=400, detail="IBAN obbligatorio per i delegati")
    
    # Crea documento utente
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
    
    # Genera token
    access_token = create_access_token(user_id, email)
    refresh_token = create_refresh_token(user_id)
    
    # Imposta cookie
    response.set_cookie(key="access_token", value=access_token, httponly=True, secure=False, samesite="lax", max_age=86400, path="/")
    response.set_cookie(key="refresh_token", value=refresh_token, httponly=True, secure=False, samesite="lax", max_age=604800, path="/")
    
    user_doc["id"] = user_id
    user_doc.pop("password_hash")
    return user_doc

@api_router.post("/auth/login", tags=["Autenticazione"])
async def login(login_data: LoginRequest, request: Request, response: Response):
    \"\"\"
    Login utente.
    
    - Protezione brute force: max 5 tentativi, poi blocco 15 minuti
    - Token salvati in cookie httpOnly
    \"\"\"
    email = login_data.email.lower()
    identifier = f"{request.client.host}:{email}"
    
    # Check brute force
    attempts = await db.login_attempts.find_one({"identifier": identifier})
    if attempts and attempts.get("count", 0) >= 5:
        lockout_time = attempts.get("last_attempt")
        if lockout_time:
            lockout_dt = datetime.fromisoformat(lockout_time) if isinstance(lockout_time, str) else lockout_time
            if datetime.now(timezone.utc) - lockout_dt < timedelta(minutes=15):
                raise HTTPException(status_code=429, detail="Troppi tentativi. Riprova tra 15 minuti.")
    
    # Verifica credenziali
    user = await db.users.find_one({"email": email})
    if not user or not verify_password(login_data.password, user["password_hash"]):
        await db.login_attempts.update_one(
            {"identifier": identifier},
            {"$inc": {"count": 1}, "$set": {"last_attempt": datetime.now(timezone.utc).isoformat()}},
            upsert=True
        )
        raise HTTPException(status_code=401, detail="Credenziali non valide")
    
    # Login OK: reset tentativi
    await db.login_attempts.delete_one({"identifier": identifier})
    
    # Genera token
    user_id = str(user["_id"])
    access_token = create_access_token(user_id, email)
    refresh_token = create_refresh_token(user_id)
    
    # Imposta cookie
    response.set_cookie(key="access_token", value=access_token, httponly=True, secure=False, samesite="lax", max_age=86400, path="/")
    response.set_cookie(key="refresh_token", value=refresh_token, httponly=True, secure=False, samesite="lax", max_age=604800, path="/")
    
    # Prepara risposta
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

@api_router.post("/auth/logout", tags=["Autenticazione"])
async def logout(response: Response):
    """Logout: elimina cookie di sessione"""
    response.delete_cookie(key="access_token", path="/")
    response.delete_cookie(key="refresh_token", path="/")
    return {"message": "Logout effettuato"}

@api_router.get("/auth/me", tags=["Autenticazione"])
async def get_me(request: Request):
    """Ritorna dati utente corrente"""
    return await get_current_user(request)

@api_router.post("/auth/refresh", tags=["Autenticazione"])
async def refresh_token(request: Request, response: Response):
    """Rinnova access token usando refresh token"""
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

# ==============================================
# ROUTE: GOOGLE MAPS
# ==============================================

@api_router.post("/calcola-km", tags=["Utilità"])
async def calcola_km(data: CalcoloKmRequest, request: Request):
    \"\"\"
    Calcola distanza KM tra due indirizzi con Google Maps.
    
    Richiede GOOGLE_MAPS_API_KEY configurata.
    KM arrotondati per eccesso al primo intero.
    \"\"\"
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

# ==============================================
# ROUTE: SEDI
# ==============================================

@api_router.get("/sedi", tags=["Sedi"])
async def get_sedi():
    """Lista tutte le sedi (pubblica per registrazione)"""
    sedi = []
    async for sede in db.sedi.find({}, {"_id": 1, "nome": 1, "codice": 1, "indirizzo": 1, "tariffa_km": 1, "rimborso_pasti": 1, "rimborso_autostrada": 1}):
        sede["id"] = str(sede["_id"])
        sede.pop("_id")
        sedi.append(sede)
    return sedi

@api_router.post("/sedi", tags=["Sedi"])
async def create_sede(sede_data: SedeCreate, request: Request):
    """Crea nuova sede (solo SuperAdmin)"""
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

@api_router.put("/sedi/{sede_id}", tags=["Sedi"])
async def update_sede(sede_id: str, sede_data: SedeUpdate, request: Request):
    """Aggiorna sede (Admin o SuperAdmin)"""
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

@api_router.delete("/sedi/{sede_id}", tags=["Sedi"])
async def delete_sede(sede_id: str, request: Request):
    """Elimina sede (solo SuperAdmin)"""
    user = await get_current_user(request)
    if user["ruolo"] not in ["superadmin"]:
        raise HTTPException(status_code=403, detail="Solo il SuperAdmin può eliminare sedi")
    
    result = await db.sedi.delete_one({"_id": ObjectId(sede_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Sede non trovata")
    return {"message": "Sede eliminata"}

# ==============================================
# ROUTE: MOTIVI RIMBORSO
# ==============================================

@api_router.get("/motivi-rimborso", tags=["Motivi Rimborso"])
async def get_motivi_rimborso(request: Request):
    """Lista motivi/causali rimborso"""
    await get_current_user(request)
    motivi = []
    async for motivo in db.motivi_rimborso.find({}):
        motivo["id"] = str(motivo["_id"])
        motivo.pop("_id")
        motivi.append(motivo)
    return motivi

@api_router.post("/motivi-rimborso", tags=["Motivi Rimborso"])
async def create_motivo_rimborso(motivo_data: MotivoRimborsoCreate, request: Request):
    """Crea nuovo motivo (solo SuperAdmin)"""
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

@api_router.put("/motivi-rimborso/{motivo_id}", tags=["Motivi Rimborso"])
async def update_motivo_rimborso(motivo_id: str, motivo_data: MotivoRimborsoUpdate, request: Request):
    """Aggiorna motivo esistente (solo SuperAdmin)"""
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

@api_router.delete("/motivi-rimborso/{motivo_id}", tags=["Motivi Rimborso"])
async def delete_motivo_rimborso(motivo_id: str, request: Request):
    """Elimina motivo (solo SuperAdmin)"""
    user = await get_current_user(request)
    if user["ruolo"] not in ["superadmin"]:
        raise HTTPException(status_code=403, detail="Solo il SuperAdmin può gestire i motivi")
    
    result = await db.motivi_rimborso.delete_one({"_id": ObjectId(motivo_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Motivo non trovato")
    return {"message": "Motivo eliminato"}

# ==============================================
# ROUTE: RIMBORSI
# ==============================================

@api_router.get("/rimborsi", tags=["Rimborsi"])
async def get_rimborsi(request: Request, stato: Optional[str] = None, anno: Optional[int] = None):
    \"\"\"
    Lista rimborsi.
    
    - Iscritti: non vedono nulla
    - Delegati: vedono solo i propri
    - Admin: vedono quelli della propria sede
    - SuperAdmin/SuperUser: vedono tutto
    \"\"\"
    user = await get_current_user(request)
    
    query = {}
    
    # Filtro per ruolo
    if user["ruolo"] not in ["superadmin", "superuser"]:
        if user["ruolo"] == "admin":
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
        
        # Aggiungi nome utente
        rimborso_user = await db.users.find_one({"_id": ObjectId(rimborso["user_id"])})
        if rimborso_user:
            rimborso["user_nome"] = f"{rimborso_user['nome']} {rimborso_user['cognome']}"
        
        # Aggiungi nome motivo
        if rimborso.get("motivo_id"):
            motivo = await db.motivi_rimborso.find_one({"_id": ObjectId(rimborso["motivo_id"])})
            if motivo:
                rimborso["motivo_nome"] = motivo["nome"]
        
        rimborsi.append(rimborso)
    
    return rimborsi

@api_router.post("/rimborsi", tags=["Rimborsi"])
async def create_rimborso(rimborso_data: RimborsoCreate, request: Request):
    \"\"\"
    Crea nuova richiesta rimborso.
    
    - Solo delegati+ possono richiedere
    - Se motivo richiede note, sono obbligatorie
    - Se KM modificati manualmente, admin riceve alert
    \"\"\"
    user = await get_current_user(request)
    
    if user["ruolo"] not in ["delegato", "segreteria", "segretario", "admin", "superadmin"]:
        raise HTTPException(status_code=403, detail="Gli iscritti non possono richiedere rimborsi")
    
    # Check note obbligatorie
    motivo = await db.motivi_rimborso.find_one({"_id": ObjectId(rimborso_data.motivo_id)})
    if motivo and motivo.get("richiede_note") and not rimborso_data.note:
        raise HTTPException(status_code=400, detail="Per questo motivo le note sono obbligatorie")
    
    # Carica tariffe sede
    sede = None
    if user.get("sede_id"):
        sede = await db.sedi.find_one({"_id": ObjectId(user["sede_id"])})
    
    tariffa_km = sede["tariffa_km"] if sede else 0.35
    
    # Calcola importi
    km_totali = rimborso_data.km_andata * (2 if rimborso_data.andata_ritorno else 1)
    importo_km = km_totali * tariffa_km
    importo_autostrada = rimborso_data.costo_autostrada if rimborso_data.uso_autostrada else 0
    importo_pasti = rimborso_data.importo_pasti
    importo_totale = importo_km + importo_pasti + importo_autostrada
    
    # Crea documento
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
    
    # Notifica admin
    notifica_msg = f"{user['nome']} {user['cognome']} ha inviato una richiesta di rimborso di €{importo_totale:.2f}"
    if rimborso_data.km_modificati_manualmente:
        notifica_msg += " - ATTENZIONE: KM modificati manualmente!"
    
    await db.notifiche.insert_one({
        "user_id": None,
        "sede_id": user.get("sede_id"),
        "tipo": "rimborso",
        "titolo": "Nuova richiesta rimborso" + (" ⚠️ KM MODIFICATI" if rimborso_data.km_modificati_manualmente else ""),
        "messaggio": notifica_msg,
        "rimborso_id": str(result.inserted_id),
        "alert_km": rimborso_data.km_modificati_manualmente,
        "letto": False,
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    return rimborso_doc

@api_router.post("/rimborsi/{rimborso_id}/ricevute", tags=["Rimborsi"])
async def upload_ricevuta(rimborso_id: str, request: Request, file: UploadFile = File(...)):
    """Upload ricevuta generica (pedaggi, etc)"""
    user = await get_current_user(request)
    
    rimborso = await db.rimborsi.find_one({"_id": ObjectId(rimborso_id)})
    if not rimborso:
        raise HTTPException(status_code=404, detail="Rimborso non trovato")
    
    if rimborso["user_id"] != user["id"] and user["ruolo"] not in ["admin", "superadmin"]:
        raise HTTPException(status_code=403, detail="Non autorizzato")
    
    # Valida file
    if file.content_type not in ["application/pdf", "image/jpeg", "image/png", "image/jpg"]:
        raise HTTPException(status_code=400, detail="Formato file non supportato. Usa PDF, JPG o PNG")
    
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File troppo grande. Max 5MB")
    
    # Salva file
    file_id = str(uuid.uuid4())
    ext = file.filename.split(".")[-1] if "." in file.filename else "pdf"
    filename = f"{file_id}.{ext}"
    filepath = UPLOAD_DIR / filename
    
    async with aiofiles.open(filepath, "wb") as f:
        await f.write(content)
    
    # Aggiorna rimborso
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

@api_router.post("/rimborsi/{rimborso_id}/ricevute-spese", tags=["Rimborsi"])
async def upload_ricevuta_spesa(
    rimborso_id: str, 
    request: Request, 
    file: UploadFile = File(...), 
    tipo: str = Form(...), 
    descrizione: str = Form(None)
):
    \"\"\"
    Upload ricevuta spesa (pasto, altro).
    
    Tipi: 'pasto', 'altro'
    \"\"\"
    user = await get_current_user(request)
    
    rimborso = await db.rimborsi.find_one({"_id": ObjectId(rimborso_id)})
    if not rimborso:
        raise HTTPException(status_code=404, detail="Rimborso non trovato")
    
    if rimborso["user_id"] != user["id"] and user["ruolo"] not in ["admin", "superadmin"]:
        raise HTTPException(status_code=403, detail="Non autorizzato")
    
    # Valida file
    if file.content_type not in ["application/pdf", "image/jpeg", "image/png", "image/jpg"]:
        raise HTTPException(status_code=400, detail="Formato file non supportato")
    
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File troppo grande. Max 5MB")
    
    # Salva
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

@api_router.put("/rimborsi/{rimborso_id}", tags=["Rimborsi"])
async def update_rimborso(rimborso_id: str, rimborso_data: RimborsoUpdate, request: Request):
    """Aggiorna stato rimborso (solo Admin)"""
    user = await get_current_user(request)
    
    if user["ruolo"] not in ["admin", "superadmin"]:
        raise HTTPException(status_code=403, detail="Solo admin può gestire i rimborsi")
    
    rimborso = await db.rimborsi.find_one({"_id": ObjectId(rimborso_id)})
    if not rimborso:
        raise HTTPException(status_code=404, detail="Rimborso non trovato")
    
    # Check permessi sede
    if user["ruolo"] == "admin" and rimborso.get("sede_id") != user.get("sede_id"):
        raise HTTPException(status_code=403, detail="Non autorizzato per questa sede")
    
    update_data = {k: v for k, v in rimborso_data.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="Nessun dato da aggiornare")
    
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    await db.rimborsi.update_one({"_id": ObjectId(rimborso_id)}, {"$set": update_data})
    
    # Notifica utente
    stati_msg = {"approvato": "approvata", "rifiutato": "rifiutata", "pagato": "pagata"}
    if rimborso_data.stato and rimborso_data.stato in stati_msg:
        await db.notifiche.insert_one({
            "user_id": rimborso["user_id"],
            "sede_id": rimborso.get("sede_id"),
            "tipo": "rimborso",
            "titolo": f"Richiesta rimborso {stati_msg[rimborso_data.stato]}",
            "messaggio": f"La tua richiesta di rimborso del {rimborso['data']} è stata {stati_msg[rimborso_data.stato]}",
            "letto": False,
            "created_at": datetime.now(timezone.utc).isoformat()
        })
    
    return {"message": "Rimborso aggiornato"}

@api_router.post("/rimborsi/{rimborso_id}/contabile", tags=["Rimborsi"])
async def upload_contabile(rimborso_id: str, request: Request, file: UploadFile = File(...)):
    \"\"\"
    Carica contabile bonifico e chiude rimborso.
    
    Imposta automaticamente stato = 'pagato'.
    \"\"\"
    user = await get_current_user(request)
    
    if user["ruolo"] not in ["admin", "superadmin"]:
        raise HTTPException(status_code=403, detail="Solo admin può caricare contabili")
    
    rimborso = await db.rimborsi.find_one({"_id": ObjectId(rimborso_id)})
    if not rimborso:
        raise HTTPException(status_code=404, detail="Rimborso non trovato")
    
    # Salva file
    content = await file.read()
    file_id = str(uuid.uuid4())
    ext = file.filename.split(".")[-1] if "." in file.filename else "pdf"
    filename = f"contabile_{file_id}.{ext}"
    filepath = UPLOAD_DIR / filename
    
    async with aiofiles.open(filepath, "wb") as f:
        await f.write(content)
    
    # Aggiorna rimborso
    await db.rimborsi.update_one(
        {"_id": ObjectId(rimborso_id)},
        {"$set": {
            "stato": "pagato",
            "contabile": {"filename": file.filename, "path": filename},
            "pagato_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # Notifica utente
    await db.notifiche.insert_one({
        "user_id": rimborso["user_id"],
        "sede_id": rimborso.get("sede_id"),
        "tipo": "rimborso",
        "titolo": "Rimborso pagato",
        "messaggio": f"Il rimborso del {rimborso['data']} è stato pagato. Contabile disponibile.",
        "letto": False,
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    return {"message": "Contabile caricata e rimborso chiuso"}

# ==============================================
# ROUTE: ANNUNCI (BACHECA)
# ==============================================

@api_router.get("/annunci", tags=["Bacheca"])
async def get_annunci(request: Request):
    """Lista annunci in bacheca"""
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

@api_router.post("/annunci", tags=["Bacheca"])
async def create_annuncio(annuncio_data: AnnuncioCreate, request: Request):
    """Pubblica nuovo annuncio (Segreteria+)"""
    user = await get_current_user(request)
    
    if user["ruolo"] not in ["segreteria", "segretario", "admin", "superadmin"]:
        raise HTTPException(status_code=403, detail="Permessi insufficienti")
    
    annuncio_doc = {
        "titolo": annuncio_data.titolo,
        "contenuto": annuncio_data.contenuto,
        "link_documento": annuncio_data.link_documento,
        "sede_id": user.get("sede_id") if user["ruolo"] != "superadmin" else None,
        "autore_id": user["id"],
        "autore_nome": f"{user['nome']} {user['cognome']}",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    result = await db.annunci.insert_one(annuncio_doc)
    annuncio_doc["id"] = str(result.inserted_id)
    annuncio_doc.pop("_id", None)
    return annuncio_doc

@api_router.delete("/annunci/{annuncio_id}", tags=["Bacheca"])
async def delete_annuncio(annuncio_id: str, request: Request):
    """Elimina annuncio"""
    user = await get_current_user(request)
    
    if user["ruolo"] not in ["segreteria", "segretario", "admin", "superadmin"]:
        raise HTTPException(status_code=403, detail="Permessi insufficienti")
    
    result = await db.annunci.delete_one({"_id": ObjectId(annuncio_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Annuncio non trovato")
    return {"message": "Annuncio eliminato"}

# ==============================================
# ROUTE: DOCUMENTI
# ==============================================

@api_router.get("/documenti", tags=["Documenti"])
async def get_documenti(request: Request, categoria: Optional[str] = None):
    """Lista documenti/modulistica"""
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

@api_router.post("/documenti", tags=["Documenti"])
async def upload_documento(
    request: Request,
    file: UploadFile = File(...),
    nome: str = Form(...),
    categoria: str = Form(...),
    descrizione: str = Form(None)
):
    """Carica nuovo documento (Segreteria+)"""
    user = await get_current_user(request)
    
    if user["ruolo"] not in ["segreteria", "segretario", "admin", "superadmin"]:
        raise HTTPException(status_code=403, detail="Permessi insufficienti")
    
    if file.content_type not in ["application/pdf", "image/jpeg", "image/png", "image/jpg"]:
        raise HTTPException(status_code=400, detail="Formato file non supportato")
    
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
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
    return doc_record

@api_router.get("/documenti/{doc_id}/download", tags=["Documenti"])
async def download_documento(doc_id: str, request: Request):
    """Scarica documento"""
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

@api_router.delete("/documenti/{doc_id}", tags=["Documenti"])
async def delete_documento(doc_id: str, request: Request):
    """Elimina documento"""
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

# ==============================================
# ROUTE: NOTIFICHE
# ==============================================

@api_router.get("/notifiche", tags=["Notifiche"])
async def get_notifiche(request: Request):
    """Lista notifiche utente"""
    user = await get_current_user(request)
    
    query = {"$or": [
        {"user_id": user["id"]},
        {"user_id": None, "sede_id": user.get("sede_id")}
    ]}
    
    if user["ruolo"] in ["admin", "superadmin"]:
        query = {"$or": [
            {"user_id": user["id"]},
            {"sede_id": user.get("sede_id")},
            {"sede_id": None}
        ]}
    
    notifiche = []
    async for notifica in db.notifiche.find(query).sort("created_at", -1).limit(50):
        notifica["id"] = str(notifica["_id"])
        notifica.pop("_id")
        notifiche.append(notifica)
    
    return notifiche

@api_router.put("/notifiche/{notifica_id}/letto", tags=["Notifiche"])
async def mark_notifica_letta(notifica_id: str, request: Request):
    """Segna notifica come letta"""
    await get_current_user(request)
    await db.notifiche.update_one({"_id": ObjectId(notifica_id)}, {"$set": {"letto": True}})
    return {"message": "Notifica segnata come letta"}

@api_router.put("/notifiche/letto-tutte", tags=["Notifiche"])
async def mark_all_notifiche_lette(request: Request):
    """Segna tutte le notifiche come lette"""
    user = await get_current_user(request)
    
    query = {"$or": [
        {"user_id": user["id"]},
        {"user_id": None, "sede_id": user.get("sede_id")}
    ]}
    
    await db.notifiche.update_many(query, {"$set": {"letto": True}})
    return {"message": "Tutte le notifiche segnate come lette"}

# ==============================================
# ROUTE: UTENTI
# ==============================================

@api_router.get("/users", tags=["Utenti"])
async def get_users(request: Request):
    """Lista utenti (Admin+)"""
    user = await get_current_user(request)
    
    if user["ruolo"] not in ["admin", "superadmin", "superuser", "segretario"]:
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

@api_router.put("/users/{user_id}", tags=["Utenti"])
async def update_user(user_id: str, user_data: UserUpdate, request: Request):
    """Aggiorna profilo utente"""
    current_user = await get_current_user(request)
    
    if user_id != current_user["id"] and current_user["ruolo"] not in ["admin", "superadmin"]:
        raise HTTPException(status_code=403, detail="Permessi insufficienti")
    
    update_data = {k: v for k, v in user_data.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="Nessun dato da aggiornare")
    
    await db.users.update_one({"_id": ObjectId(user_id)}, {"$set": update_data})
    return {"message": "Utente aggiornato"}

@api_router.put("/users/{user_id}/ruolo", tags=["Utenti"])
async def update_user_role(user_id: str, request: Request, ruolo: str = Form(...)):
    \"\"\"
    Modifica ruolo utente (Admin).
    
    Admin può assegnare: iscritto, delegato, segreteria, segretario, admin
    SuperAdmin può anche assegnare: superuser, superadmin
    \"\"\"
    current_user = await get_current_user(request)
    
    if current_user["ruolo"] not in ["admin", "superadmin"]:
        raise HTTPException(status_code=403, detail="Permessi insufficienti")
    
    valid_roles = ["iscritto", "delegato", "segreteria", "segretario", "admin"]
    if current_user["ruolo"] == "superadmin":
        valid_roles.extend(["superuser", "superadmin"])
    
    if ruolo not in valid_roles:
        raise HTTPException(status_code=400, detail="Ruolo non valido")
    
    await db.users.update_one({"_id": ObjectId(user_id)}, {"$set": {"ruolo": ruolo}})
    return {"message": "Ruolo aggiornato"}

# ==============================================
# ROUTE: REPORT
# ==============================================

@api_router.get("/reports/rimborsi-annuali", tags=["Report"])
async def get_report_rimborsi_annuali(request: Request, anno: int):
    """Report aggregato rimborsi per anno"""
    user = await get_current_user(request)
    
    if user["ruolo"] not in ["admin", "superadmin", "superuser"]:
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

@api_router.get("/reports/rimborsi-export", tags=["Report"])
async def export_rimborsi(request: Request, anno: int, formato: str = "csv"):
    """Export rimborsi in CSV"""
    user = await get_current_user(request)
    
    if user["ruolo"] not in ["admin", "superadmin", "superuser"]:
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

# ==============================================
# STARTUP - Inizializzazione database
# ==============================================

@app.on_event("startup")
async def startup():
    \"\"\"
    Inizializza database al primo avvio:
    - Crea indici
    - Crea superadmin se non esiste
    - Crea motivi rimborso default
    - Crea sede A22 se non esiste
    \"\"\"
    logger.info("Inizializzazione database...")
    
    # Indici
    await db.users.create_index("email", unique=True)
    await db.sedi.create_index("codice", unique=True)
    await db.login_attempts.create_index("identifier")
    
    # SuperAdmin
    admin_email = os.environ.get("ADMIN_EMAIL", "superadmin@sla.it")
    admin_password = os.environ.get("ADMIN_PASSWORD", "SlaAdmin2024!")
    
    existing = await db.users.find_one({"email": admin_email})
    if existing is None:
        await db.users.insert_one({
            "email": admin_email,
            "password_hash": hash_password(admin_password),
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
    
    # Motivi default
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
    
    # Rimuovi motivi vecchi
    await db.motivi_rimborso.delete_many({"nome": {"$nin": ["RSA", "Sede", "Altro"]}})
    
    # Mantieni solo A22
    await db.sedi.delete_many({"codice": {"$nin": ["A22"]}})
    
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
    
    # Test credentials file
    creds_path = Path("/app/memory/test_credentials.md")
    creds_path.parent.mkdir(exist_ok=True)
    creds_path.write_text(f\"\"\"# Test Credentials SLA Portale

## SuperAdmin
- **Email**: {admin_email}
- **Password**: {admin_password}
- **Ruolo**: superadmin

## Sedi Disponibili
- A22 - Autostrada del Brennero

## Motivi Rimborso
- RSA (note non obbligatorie)
- Sede (note non obbligatorie)
- Altro (note OBBLIGATORIE)

## Ruoli
- superadmin: Accesso totale
- superuser: Solo visualizzazione globale
- admin: Gestione propria sede
- segretario: Gestione sede
- segreteria: Carica documenti/annunci
- delegato: Richiede rimborsi
- iscritto: Solo bacheca/documenti
\"\"\")
    
    logger.info("Database inizializzato")

@app.on_event("shutdown")
async def shutdown():
    """Chiude connessione MongoDB"""
    client.close()

# ==============================================
# REGISTRA ROUTER E CORS
# ==============================================

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.environ.get("FRONTEND_URL", "http://localhost:3000")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
