"""
Autenticazione: hash password, JWT, get_current_user.
"""
import re
import secrets
import string
from datetime import datetime, timezone, timedelta

import bcrypt
import jwt
from fastapi import HTTPException, Request
from bson import ObjectId

from .config import JWT_SECRET, JWT_ALGORITHM
from .db import db


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def validate_password_strength(password: str) -> None:
    if len(password) < 8:
        raise HTTPException(status_code=400, detail="La password deve avere almeno 8 caratteri")
    if not re.search(r"[A-Za-z]", password):
        raise HTTPException(status_code=400, detail="La password deve contenere almeno una lettera")
    if not re.search(r"\d", password):
        raise HTTPException(status_code=400, detail="La password deve contenere almeno un numero")
    if not re.search(r"[^A-Za-z0-9]", password):
        raise HTTPException(status_code=400, detail="La password deve contenere almeno un carattere speciale")


def generate_temporary_password(length: int = 12) -> str:
    letters = string.ascii_letters
    digits = string.digits
    specials = "!@#$%&*"
    base = [secrets.choice(letters), secrets.choice(digits), secrets.choice(specials)]
    pool = letters + digits + specials
    base += [secrets.choice(pool) for _ in range(length - len(base))]
    secrets.SystemRandom().shuffle(base)
    return "".join(base)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def create_access_token(user_id: str, email: str) -> str:
    payload = {
        "sub": user_id,
        "email": email,
        "exp": datetime.now(timezone.utc) + timedelta(hours=24),
        "type": "access",
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def create_refresh_token(user_id: str) -> str:
    payload = {
        "sub": user_id,
        "exp": datetime.now(timezone.utc) + timedelta(days=7),
        "type": "refresh",
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


async def get_current_user(request: Request) -> dict:
    """
    Estrae e valida l'utente dal token JWT (cookie o header Authorization).
    Garantisce campo `ruoli` sempre presente (multi-ruolo).
    """
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

        # Multi-ruolo
        if not user.get("ruoli"):
            user["ruoli"] = [user["ruolo"]] if user.get("ruolo") else []
        if user.get("ruoli") and not user.get("ruolo"):
            user["ruolo"] = user["ruoli"][0]

        if user.get("sede_id"):
            sede = await db.sedi.find_one({"_id": ObjectId(user["sede_id"])})
            if sede:
                user["sede_nome"] = sede["nome"]
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token scaduto")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token non valido")
