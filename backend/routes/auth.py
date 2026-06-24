"""
routes/auth.py
Autenticazione: register, login, logout, me, refresh, change password, 2FA TOTP.
"""
from datetime import datetime, timezone, timedelta

from bson import ObjectId
from fastapi import APIRouter, HTTPException, Request, Response
import jwt

from core.audit import _log_audit
from core.auth import (
    create_access_token, create_refresh_token, get_current_user,
    hash_password, validate_password_strength, verify_password,
)
from core.config import JWT_ALGORITHM, JWT_SECRET
from core.db import db
from core.roles import user_has_any_role
from models_api import (
    ChangePasswordRequest, LoginRequest, TOTPDisableRequest, TOTPEnableRequest,
    UserCreate,
)

router = APIRouter()


@router.post("/auth/register")
async def register(user_data: UserCreate, response: Response):
    """
    POST /api/auth/register
    Registrazione nuovo utente.

    Regole:
    - Email univoca
    - Auto-registrazione solo per "iscritto" o "delegato"
    - "Iscritto": IBAN e indirizzo NON richiesti
    - "Delegato": IBAN e indirizzo OBBLIGATORI (per ricevere rimborsi)
    - Altri ruoli possono essere assegnati solo da admin
    """
    email = user_data.email.lower()
    validate_password_strength(user_data.password)

    existing = await db.users.find_one({"email": email})
    if existing:
        raise HTTPException(status_code=400, detail="Email già registrata")

    allowed_roles = ["iscritto", "delegato"]
    ruolo = user_data.ruolo if user_data.ruolo in allowed_roles else "iscritto"

    if user_data.sede_id:
        sede = await db.sedi.find_one({"_id": ObjectId(user_data.sede_id)})
        if not sede:
            raise HTTPException(status_code=400, detail="Sede non trovata")

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
        "ruoli": [ruolo],
        "sede_id": user_data.sede_id,
        "disabled": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    result = await db.users.insert_one(user_doc)
    user_id = str(result.inserted_id)

    access_token = create_access_token(user_id, email)
    refresh_token = create_refresh_token(user_id)

    response.set_cookie(key="access_token", value=access_token, httponly=True, secure=True, samesite="none", max_age=86400, path="/")
    response.set_cookie(key="refresh_token", value=refresh_token, httponly=True, secure=True, samesite="none", max_age=604800, path="/")

    user_doc["id"] = user_id
    user_doc.pop("password_hash")
    user_doc.pop("_id", None)
    return user_doc


@router.post("/auth/login")
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
            upsert=True,
        )
        raise HTTPException(status_code=401, detail="Credenziali non valide")

    if user.get("disabled", False):
        raise HTTPException(status_code=403, detail="Account disattivato. Contatta l'amministratore.")

    # 2FA TOTP
    if user.get("totp_enabled"):
        from core.totp import verify_code
        if not login_data.totp_code:
            raise HTTPException(status_code=401, detail="2FA_REQUIRED")
        if not verify_code(user.get("totp_secret", ""), login_data.totp_code):
            await db.login_attempts.update_one(
                {"identifier": identifier},
                {"$inc": {"count": 1}, "$set": {"last_attempt": datetime.now(timezone.utc).isoformat()}},
                upsert=True,
            )
            raise HTTPException(status_code=401, detail="Codice 2FA non valido")

    await db.login_attempts.delete_one({"identifier": identifier})

    user_id = str(user["_id"])
    access_token = create_access_token(user_id, email)
    refresh_token = create_refresh_token(user_id)

    response.set_cookie(key="access_token", value=access_token, httponly=True, secure=True, samesite="none", max_age=86400, path="/")
    response.set_cookie(key="refresh_token", value=refresh_token, httponly=True, secure=True, samesite="none", max_age=604800, path="/")

    user_ruoli = user.get("ruoli") or ([user["ruolo"]] if user.get("ruolo") else [])
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
        "ruoli": user_ruoli,
        "sede_id": user.get("sede_id"),
        "totp_enabled": bool(user.get("totp_enabled")),
        "created_at": user["created_at"],
    }

    if user.get("sede_id"):
        sede = await db.sedi.find_one({"_id": ObjectId(user["sede_id"])})
        if sede:
            user_response["sede_nome"] = sede["nome"]

    return user_response


@router.post("/auth/logout")
async def logout(response: Response):
    response.delete_cookie(key="access_token", path="/")
    response.delete_cookie(key="refresh_token", path="/")
    return {"message": "Logout effettuato"}


@router.get("/auth/me")
async def get_me(request: Request):
    user = await get_current_user(request)
    user["totp_enabled"] = bool(user.get("totp_enabled"))
    user.pop("totp_secret", None)
    return user


# === 2FA TOTP ===
# Disponibile solo per ruoli sensibili (admin, superadmin).

def _2fa_allowed(user: dict) -> bool:
    return user_has_any_role(user, ["admin", "superadmin"])


@router.post("/auth/2fa/setup")
async def setup_2fa(request: Request):
    """Inizia configurazione 2FA: genera segreto + QR code (pending)."""
    from core.totp import generate_qrcode_png, generate_secret
    user = await get_current_user(request)
    if not _2fa_allowed(user):
        raise HTTPException(status_code=403, detail="2FA disponibile solo per admin/superadmin")
    if user.get("totp_enabled"):
        raise HTTPException(status_code=400, detail="2FA già attivo. Disabilitalo prima di riconfigurarlo.")

    secret = generate_secret()
    qr = generate_qrcode_png(secret, user["email"])

    await db.users.update_one(
        {"_id": ObjectId(user["id"])},
        {"$set": {"totp_secret_pending": secret}},
    )

    return {
        "secret": secret,
        "qrcode": qr,
        "issuer": "Portale SLA",
        "account": user["email"],
    }


@router.post("/auth/2fa/enable")
async def enable_2fa(payload: TOTPEnableRequest, request: Request):
    """Verifica il primo codice e attiva definitivamente il 2FA."""
    from core.totp import verify_code
    user = await get_current_user(request)
    if not _2fa_allowed(user):
        raise HTTPException(status_code=403, detail="2FA disponibile solo per admin/superadmin")

    user_doc = await db.users.find_one({"_id": ObjectId(user["id"])})
    pending = user_doc.get("totp_secret_pending")
    if not pending:
        raise HTTPException(status_code=400, detail="Nessuna configurazione 2FA in corso. Riavvia da Setup.")

    if not verify_code(pending, payload.code):
        raise HTTPException(status_code=400, detail="Codice non valido")

    await db.users.update_one(
        {"_id": ObjectId(user["id"])},
        {
            "$set": {"totp_secret": pending, "totp_enabled": True},
            "$unset": {"totp_secret_pending": ""},
        },
    )
    await _log_audit(
        actor=user,
        action="user.enable_2fa",
        target_type="user",
        target_id=user["id"],
        target_label=user["email"],
    )
    return {"message": "2FA attivato con successo", "totp_enabled": True}


@router.post("/auth/2fa/disable")
async def disable_2fa(payload: TOTPDisableRequest, request: Request):
    """Disabilita 2FA. Richiede la password per evitare disabilitazioni accidentali."""
    user = await get_current_user(request)
    user_doc = await db.users.find_one({"_id": ObjectId(user["id"])})

    if not verify_password(payload.password, user_doc["password_hash"]):
        raise HTTPException(status_code=401, detail="Password non valida")

    if not user_doc.get("totp_enabled"):
        raise HTTPException(status_code=400, detail="2FA non è attivo")

    await db.users.update_one(
        {"_id": ObjectId(user["id"])},
        {"$unset": {"totp_secret": "", "totp_enabled": "", "totp_secret_pending": ""}},
    )
    await _log_audit(
        actor=user,
        action="user.disable_2fa",
        target_type="user",
        target_id=user["id"],
        target_label=user["email"],
    )
    return {"message": "2FA disattivato", "totp_enabled": False}


@router.post("/auth/refresh")
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
        response.set_cookie(key="access_token", value=access_token, httponly=True, secure=True, samesite="none", max_age=86400, path="/")
        return {"message": "Token aggiornato"}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token scaduto")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token non valido")


@router.post("/auth/change-password")
async def change_password(data: ChangePasswordRequest, request: Request, response: Response):
    """Utente loggato cambia la propria password. Forza re-login dopo il cambio."""
    user = await get_current_user(request)

    user_doc = await db.users.find_one({"_id": ObjectId(user["id"])})
    if not user_doc:
        raise HTTPException(status_code=404, detail="Utente non trovato")

    if not verify_password(data.current_password, user_doc["password_hash"]):
        raise HTTPException(status_code=400, detail="Password attuale non corretta")

    if data.current_password == data.new_password:
        raise HTTPException(status_code=400, detail="La nuova password deve essere diversa da quella attuale")

    validate_password_strength(data.new_password)

    await db.users.update_one(
        {"_id": ObjectId(user["id"])},
        {"$set": {
            "password_hash": hash_password(data.new_password),
            "password_changed_at": datetime.now(timezone.utc).isoformat(),
            "must_change_password": False,
        }},
    )

    response.delete_cookie("access_token", path="/")
    response.delete_cookie("refresh_token", path="/")

    return {"message": "Password aggiornata. Effettua nuovamente il login per sicurezza."}
