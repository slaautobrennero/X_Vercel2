from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

from fastapi import FastAPI, APIRouter, HTTPException, Request, Response, Depends, UploadFile, File, Form
from fastapi.responses import FileResponse
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
import os
import logging
import bcrypt
import jwt
import secrets
import aiofiles
from datetime import datetime, timezone, timedelta
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
import uuid
import shutil

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT Config
JWT_SECRET = os.environ['JWT_SECRET']
JWT_ALGORITHM = "HS256"

# Create the main app
app = FastAPI(title="SLA Sindacato - Portale Rimborsi")
api_router = APIRouter(prefix="/api")

# Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Upload directory
UPLOAD_DIR = ROOT_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

# ==================== MODELS ====================

class UserBase(BaseModel):
    email: EmailStr
    nome: str
    cognome: str
    telefono: Optional[str] = None
    indirizzo: Optional[str] = None
    citta: Optional[str] = None
    cap: Optional[str] = None
    iban: Optional[str] = None

class UserCreate(UserBase):
    password: str
    sede_id: Optional[str] = None
    ruolo: str = "iscritto"  # iscritto, delegato, segreteria, segretario, admin, superuser, superadmin

class UserUpdate(BaseModel):
    nome: Optional[str] = None
    cognome: Optional[str] = None
    telefono: Optional[str] = None
    indirizzo: Optional[str] = None
    citta: Optional[str] = None
    cap: Optional[str] = None
    iban: Optional[str] = None

class UserResponse(BaseModel):
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
    email: EmailStr
    password: str

class SedeCreate(BaseModel):
    nome: str
    codice: str
    indirizzo: Optional[str] = None
    tariffa_km: float = 0.35
    rimborso_pasti: float = 15.0
    rimborso_autostrada: bool = True

class SedeUpdate(BaseModel):
    nome: Optional[str] = None
    indirizzo: Optional[str] = None
    tariffa_km: Optional[float] = None
    rimborso_pasti: Optional[float] = None
    rimborso_autostrada: Optional[bool] = None

class MotivoRimborsoCreate(BaseModel):
    nome: str
    descrizione: Optional[str] = None

class RimborsoCreate(BaseModel):
    data: str
    motivo_id: str
    indirizzo_partenza: str
    indirizzo_partenza_tipo: str = "manuale"  # casa, manuale
    indirizzo_arrivo: str
    km_andata: float
    andata_ritorno: bool = True
    uso_autostrada: bool = False
    costo_autostrada: float = 0
    numero_pasti: int = 0
    note: Optional[str] = None

class RimborsoUpdate(BaseModel):
    stato: Optional[str] = None  # in_attesa, approvato, rifiutato, pagato
    note_admin: Optional[str] = None

class AnnuncioCreate(BaseModel):
    titolo: str
    contenuto: str
    link_documento: Optional[str] = None

class DocumentoCreate(BaseModel):
    nome: str
    categoria: str  # modulistica, documento, altro
    descrizione: Optional[str] = None

# ==================== AUTH HELPERS ====================

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))

def create_access_token(user_id: str, email: str) -> str:
    payload = {
        "sub": user_id,
        "email": email,
        "exp": datetime.now(timezone.utc) + timedelta(hours=24),
        "type": "access"
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def create_refresh_token(user_id: str) -> str:
    payload = {
        "sub": user_id,
        "exp": datetime.now(timezone.utc) + timedelta(days=7),
        "type": "refresh"
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

async def get_current_user(request: Request) -> dict:
    token = request.cookies.get("access_token")
    if not token:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
    if not token:
        raise HTTPException(status_code=401, detail="Non autenticato")
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Token non valido")
        user = await db.users.find_one({"_id": ObjectId(payload["sub"])})
        if not user:
            raise HTTPException(status_code=401, detail="Utente non trovato")
        user["id"] = str(user["_id"])
        user.pop("_id", None)
        user.pop("password_hash", None)
        # Get sede name
        if user.get("sede_id"):
            sede = await db.sedi.find_one({"_id": ObjectId(user["sede_id"])})
            if sede:
                user["sede_nome"] = sede["nome"]
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token scaduto")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token non valido")

def require_roles(*roles):
    async def role_checker(request: Request):
        user = await get_current_user(request)
        if user["ruolo"] not in roles and user["ruolo"] not in ["superadmin", "admin"]:
            raise HTTPException(status_code=403, detail="Permessi insufficienti")
        return user
    return role_checker

# ==================== AUTH ROUTES ====================

@api_router.post("/auth/register")
async def register(user_data: UserCreate, response: Response):
    email = user_data.email.lower()
    existing = await db.users.find_one({"email": email})
    if existing:
        raise HTTPException(status_code=400, detail="Email già registrata")
    
    # Validate sede exists if provided
    if user_data.sede_id:
        sede = await db.sedi.find_one({"_id": ObjectId(user_data.sede_id)})
        if not sede:
            raise HTTPException(status_code=400, detail="Sede non trovata")
    
    user_doc = {
        "email": email,
        "password_hash": hash_password(user_data.password),
        "nome": user_data.nome,
        "cognome": user_data.cognome,
        "telefono": user_data.telefono,
        "indirizzo": user_data.indirizzo,
        "citta": user_data.citta,
        "cap": user_data.cap,
        "iban": user_data.iban,
        "ruolo": user_data.ruolo if user_data.ruolo in ["iscritto", "delegato"] else "iscritto",
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
    
    # Check brute force
    attempts = await db.login_attempts.find_one({"identifier": identifier})
    if attempts and attempts.get("count", 0) >= 5:
        lockout_time = attempts.get("last_attempt")
        if lockout_time:
            lockout_dt = datetime.fromisoformat(lockout_time) if isinstance(lockout_time, str) else lockout_time
            if datetime.now(timezone.utc) - lockout_dt < timedelta(minutes=15):
                raise HTTPException(status_code=429, detail="Troppi tentativi. Riprova tra 15 minuti.")
    
    user = await db.users.find_one({"email": email})
    if not user or not verify_password(login_data.password, user["password_hash"]):
        # Increment failed attempts
        await db.login_attempts.update_one(
            {"identifier": identifier},
            {"$inc": {"count": 1}, "$set": {"last_attempt": datetime.now(timezone.utc).isoformat()}},
            upsert=True
        )
        raise HTTPException(status_code=401, detail="Credenziali non valide")
    
    # Clear failed attempts
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

# ==================== SEDI ROUTES ====================

@api_router.get("/sedi")
async def get_sedi(request: Request):
    user = await get_current_user(request)
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
    if user["ruolo"] not in ["superadmin", "admin"]:
        raise HTTPException(status_code=403, detail="Permessi insufficienti")
    
    motivo_doc = {
        "nome": motivo_data.nome,
        "descrizione": motivo_data.descrizione,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    result = await db.motivi_rimborso.insert_one(motivo_doc)
    motivo_doc["id"] = str(result.inserted_id)
    motivo_doc.pop("_id", None)
    return motivo_doc

@api_router.delete("/motivi-rimborso/{motivo_id}")
async def delete_motivo_rimborso(motivo_id: str, request: Request):
    user = await get_current_user(request)
    if user["ruolo"] not in ["superadmin", "admin"]:
        raise HTTPException(status_code=403, detail="Permessi insufficienti")
    
    result = await db.motivi_rimborso.delete_one({"_id": ObjectId(motivo_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Motivo non trovato")
    
    return {"message": "Motivo eliminato"}

# ==================== RIMBORSI ROUTES ====================

@api_router.get("/rimborsi")
async def get_rimborsi(request: Request, stato: Optional[str] = None, anno: Optional[int] = None):
    user = await get_current_user(request)
    
    query = {}
    
    # Filter by sede for non-superadmin/superuser
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
        
        # Get user info
        rimborso_user = await db.users.find_one({"_id": ObjectId(rimborso["user_id"])})
        if rimborso_user:
            rimborso["user_nome"] = f"{rimborso_user['nome']} {rimborso_user['cognome']}"
        
        # Get motivo info
        if rimborso.get("motivo_id"):
            motivo = await db.motivi_rimborso.find_one({"_id": ObjectId(rimborso["motivo_id"])})
            if motivo:
                rimborso["motivo_nome"] = motivo["nome"]
        
        rimborsi.append(rimborso)
    
    return rimborsi

@api_router.post("/rimborsi")
async def create_rimborso(rimborso_data: RimborsoCreate, request: Request):
    user = await get_current_user(request)
    
    if user["ruolo"] not in ["delegato", "segreteria", "segretario", "admin", "superadmin"]:
        raise HTTPException(status_code=403, detail="Gli iscritti non possono richiedere rimborsi")
    
    # Get sede tariffs
    sede = None
    if user.get("sede_id"):
        sede = await db.sedi.find_one({"_id": ObjectId(user["sede_id"])})
    
    tariffa_km = sede["tariffa_km"] if sede else 0.35
    rimborso_pasti = sede["rimborso_pasti"] if sede else 15.0
    
    # Calculate totals
    km_totali = rimborso_data.km_andata * (2 if rimborso_data.andata_ritorno else 1)
    importo_km = km_totali * tariffa_km
    importo_pasti = rimborso_data.numero_pasti * rimborso_pasti
    importo_autostrada = rimborso_data.costo_autostrada if rimborso_data.uso_autostrada else 0
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
        "andata_ritorno": rimborso_data.andata_ritorno,
        "km_totali": km_totali,
        "uso_autostrada": rimborso_data.uso_autostrada,
        "costo_autostrada": importo_autostrada,
        "numero_pasti": rimborso_data.numero_pasti,
        "tariffa_km": tariffa_km,
        "importo_km": importo_km,
        "importo_pasti": importo_pasti,
        "importo_totale": importo_totale,
        "note": rimborso_data.note,
        "stato": "in_attesa",
        "ricevute": [],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    result = await db.rimborsi.insert_one(rimborso_doc)
    rimborso_doc["id"] = str(result.inserted_id)
    rimborso_doc.pop("_id", None)
    
    # Create notification for admin
    await db.notifiche.insert_one({
        "user_id": None,
        "sede_id": user.get("sede_id"),
        "tipo": "rimborso",
        "titolo": "Nuova richiesta rimborso",
        "messaggio": f"{user['nome']} {user['cognome']} ha inviato una richiesta di rimborso di €{importo_totale:.2f}",
        "letto": False,
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    return rimborso_doc

@api_router.post("/rimborsi/{rimborso_id}/ricevute")
async def upload_ricevuta(rimborso_id: str, request: Request, file: UploadFile = File(...)):
    user = await get_current_user(request)
    
    rimborso = await db.rimborsi.find_one({"_id": ObjectId(rimborso_id)})
    if not rimborso:
        raise HTTPException(status_code=404, detail="Rimborso non trovato")
    
    if rimborso["user_id"] != user["id"] and user["ruolo"] not in ["admin", "superadmin"]:
        raise HTTPException(status_code=403, detail="Non autorizzato")
    
    # Validate file
    if file.content_type not in ["application/pdf", "image/jpeg", "image/png", "image/jpg"]:
        raise HTTPException(status_code=400, detail="Formato file non supportato. Usa PDF, JPG o PNG")
    
    # Check file size (5MB max)
    content = await file.read()
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File troppo grande. Max 5MB")
    
    # Save file
    file_id = str(uuid.uuid4())
    ext = file.filename.split(".")[-1] if "." in file.filename else "pdf"
    filename = f"{file_id}.{ext}"
    filepath = UPLOAD_DIR / filename
    
    async with aiofiles.open(filepath, "wb") as f:
        await f.write(content)
    
    # Update rimborso
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

@api_router.put("/rimborsi/{rimborso_id}")
async def update_rimborso(rimborso_id: str, rimborso_data: RimborsoUpdate, request: Request):
    user = await get_current_user(request)
    
    if user["ruolo"] not in ["admin", "superadmin"]:
        raise HTTPException(status_code=403, detail="Solo admin può gestire i rimborsi")
    
    rimborso = await db.rimborsi.find_one({"_id": ObjectId(rimborso_id)})
    if not rimborso:
        raise HTTPException(status_code=404, detail="Rimborso non trovato")
    
    # Check sede permission for admin
    if user["ruolo"] == "admin" and rimborso.get("sede_id") != user.get("sede_id"):
        raise HTTPException(status_code=403, detail="Non autorizzato per questa sede")
    
    update_data = {k: v for k, v in rimborso_data.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="Nessun dato da aggiornare")
    
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.rimborsi.update_one({"_id": ObjectId(rimborso_id)}, {"$set": update_data})
    
    # Notify user
    stato_msg = {
        "approvato": "approvata",
        "rifiutato": "rifiutata",
        "pagato": "pagata"
    }
    if rimborso_data.stato and rimborso_data.stato in stato_msg:
        await db.notifiche.insert_one({
            "user_id": rimborso["user_id"],
            "sede_id": rimborso.get("sede_id"),
            "tipo": "rimborso",
            "titolo": f"Richiesta rimborso {stato_msg[rimborso_data.stato]}",
            "messaggio": f"La tua richiesta di rimborso del {rimborso['data']} è stata {stato_msg[rimborso_data.stato]}",
            "letto": False,
            "created_at": datetime.now(timezone.utc).isoformat()
        })
    
    return {"message": "Rimborso aggiornato"}

@api_router.post("/rimborsi/{rimborso_id}/contabile")
async def upload_contabile(rimborso_id: str, request: Request, file: UploadFile = File(...)):
    user = await get_current_user(request)
    
    if user["ruolo"] not in ["admin", "superadmin"]:
        raise HTTPException(status_code=403, detail="Solo admin può caricare contabili")
    
    rimborso = await db.rimborsi.find_one({"_id": ObjectId(rimborso_id)})
    if not rimborso:
        raise HTTPException(status_code=404, detail="Rimborso non trovato")
    
    # Save file
    content = await file.read()
    file_id = str(uuid.uuid4())
    ext = file.filename.split(".")[-1] if "." in file.filename else "pdf"
    filename = f"contabile_{file_id}.{ext}"
    filepath = UPLOAD_DIR / filename
    
    async with aiofiles.open(filepath, "wb") as f:
        await f.write(content)
    
    # Update rimborso
    await db.rimborsi.update_one(
        {"_id": ObjectId(rimborso_id)},
        {"$set": {
            "stato": "pagato",
            "contabile": {"filename": file.filename, "path": filename},
            "pagato_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # Notify user
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

# ==================== ANNUNCI (BULLETIN BOARD) ROUTES ====================

@api_router.get("/annunci")
async def get_annunci(request: Request):
    user = await get_current_user(request)
    
    query = {}
    if user["ruolo"] not in ["superadmin", "superuser"]:
        query["$or"] = [
            {"sede_id": user.get("sede_id")},
            {"sede_id": None}  # Global announcements
        ]
    
    annunci = []
    async for annuncio in db.annunci.find(query).sort("created_at", -1).limit(50):
        annuncio["id"] = str(annuncio["_id"])
        annuncio.pop("_id")
        annunci.append(annuncio)
    
    return annunci

@api_router.post("/annunci")
async def create_annuncio(annuncio_data: AnnuncioCreate, request: Request):
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

@api_router.delete("/annunci/{annuncio_id}")
async def delete_annuncio(annuncio_id: str, request: Request):
    user = await get_current_user(request)
    
    if user["ruolo"] not in ["segreteria", "segretario", "admin", "superadmin"]:
        raise HTTPException(status_code=403, detail="Permessi insufficienti")
    
    result = await db.annunci.delete_one({"_id": ObjectId(annuncio_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Annuncio non trovato")
    
    return {"message": "Annuncio eliminato"}

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
    
    # Validate file
    if file.content_type not in ["application/pdf", "image/jpeg", "image/png", "image/jpg"]:
        raise HTTPException(status_code=400, detail="Formato file non supportato")
    
    content = await file.read()
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File troppo grande. Max 5MB")
    
    # Save file
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

@api_router.get("/documenti/{doc_id}/download")
async def download_documento(doc_id: str, request: Request):
    user = await get_current_user(request)
    
    doc = await db.documenti.find_one({"_id": ObjectId(doc_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Documento non trovato")
    
    # Check permission
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
    
    # Delete file
    filepath = UPLOAD_DIR / doc["path"]
    if filepath.exists():
        filepath.unlink()
    
    await db.documenti.delete_one({"_id": ObjectId(doc_id)})
    
    return {"message": "Documento eliminato"}

# ==================== NOTIFICHE ROUTES ====================

@api_router.get("/notifiche")
async def get_notifiche(request: Request):
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

@api_router.put("/users/{user_id}")
async def update_user(user_id: str, user_data: UserUpdate, request: Request):
    current_user = await get_current_user(request)
    
    # Users can update themselves, or admin can update others
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
    
    valid_roles = ["iscritto", "delegato", "segreteria", "segretario", "admin"]
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
        results.append(result)
    
    return results

# ==================== STARTUP ====================

@app.on_event("startup")
async def startup():
    # Create indexes
    await db.users.create_index("email", unique=True)
    await db.sedi.create_index("codice", unique=True)
    await db.login_attempts.create_index("identifier")
    
    # Seed superadmin
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
    
    # Seed default motivi rimborso
    motivi_default = ["RSA", "Sede", "Corso di Formazione", "Assemblea", "Riunione", "Altro"]
    for motivo in motivi_default:
        existing_motivo = await db.motivi_rimborso.find_one({"nome": motivo})
        if not existing_motivo:
            await db.motivi_rimborso.insert_one({
                "nome": motivo,
                "descrizione": None,
                "created_at": datetime.now(timezone.utc).isoformat()
            })
    
    # Seed sample sedi
    sedi_default = [
        {"nome": "Autostrada del Brennero A22", "codice": "A22", "tariffa_km": 0.35, "rimborso_pasti": 15.0},
        {"nome": "Concessioni Autostradali Venete CAV", "codice": "CAV", "tariffa_km": 0.30, "rimborso_pasti": 12.0},
        {"nome": "Autostrade per l'Italia", "codice": "ASPI", "tariffa_km": 0.40, "rimborso_pasti": 18.0},
    ]
    for sede in sedi_default:
        existing_sede = await db.sedi.find_one({"codice": sede["codice"]})
        if not existing_sede:
            sede["indirizzo"] = None
            sede["rimborso_autostrada"] = True
            sede["created_at"] = datetime.now(timezone.utc).isoformat()
            await db.sedi.insert_one(sede)
    
    # Write test credentials
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
""")
    
    logger.info("Database inizializzato con dati di esempio")

@app.on_event("shutdown")
async def shutdown():
    client.close()

# Include router
app.include_router(api_router)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.environ.get("FRONTEND_URL", "http://localhost:3000")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
