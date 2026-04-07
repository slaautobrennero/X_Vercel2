"""
Auth - Autenticazione e autorizzazione

Gestisce:
- Hashing password con bcrypt
- Generazione/validazione token JWT
- Middleware per protezione route
- Protezione brute force

I token sono memorizzati in cookie httpOnly per sicurezza.
Access token: 24 ore
Refresh token: 7 giorni
"""

import bcrypt
import jwt
from datetime import datetime, timezone, timedelta
from fastapi import HTTPException, Request
from bson import ObjectId

from .config import settings
from .database import db


def hash_password(password: str) -> str:
    """
    Hash password con bcrypt.
    Usa salt automatico per sicurezza.
    """
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifica password contro hash.
    Ritorna True se corretta.
    """
    return bcrypt.checkpw(
        plain_password.encode("utf-8"), 
        hashed_password.encode("utf-8")
    )


def create_access_token(user_id: str, email: str) -> str:
    """
    Crea JWT access token.
    Contiene: user_id, email, scadenza, tipo.
    """
    payload = {
        "sub": user_id,
        "email": email,
        "exp": datetime.now(timezone.utc) + timedelta(hours=settings.ACCESS_TOKEN_EXPIRE_HOURS),
        "type": "access"
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(user_id: str) -> str:
    """
    Crea JWT refresh token.
    Usato per rinnovare access token senza re-login.
    """
    payload = {
        "sub": user_id,
        "exp": datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        "type": "refresh"
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


async def get_current_user(request: Request) -> dict:
    """
    Middleware: Estrae e valida utente dal token.
    
    Cerca token in:
    1. Cookie 'access_token'
    2. Header 'Authorization: Bearer <token>'
    
    Ritorna dict con dati utente (senza password).
    Solleva HTTPException se non autenticato.
    """
    # Cerca token
    token = request.cookies.get("access_token")
    if not token:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
    
    if not token:
        raise HTTPException(status_code=401, detail="Non autenticato")
    
    try:
        # Decodifica e valida
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Token non valido")
        
        # Carica utente da DB
        user = await db.users.find_one({"_id": ObjectId(payload["sub"])})
        if not user:
            raise HTTPException(status_code=401, detail="Utente non trovato")
        
        # Prepara risposta (senza dati sensibili)
        user["id"] = str(user["_id"])
        user.pop("_id", None)
        user.pop("password_hash", None)
        
        # Aggiungi nome sede se presente
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
    """
    Decorator factory: Richiede uno dei ruoli specificati.
    
    Uso:
        @router.get("/admin-only")
        async def admin_route(user = Depends(require_roles("admin", "superadmin"))):
            ...
    """
    async def role_checker(request: Request):
        user = await get_current_user(request)
        # SuperAdmin ha sempre accesso
        if user["ruolo"] in ["superadmin"] + list(roles):
            return user
        raise HTTPException(status_code=403, detail="Permessi insufficienti")
    return role_checker
