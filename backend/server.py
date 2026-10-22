"""
==============================================
SLA PORTALE - Server FastAPI (entry point)
==============================================

Entry point dell'applicazione backend.
La logica delle API è organizzata in moduli sotto `routes/`:

  routes/public.py     → /version
  routes/auth.py       → /auth/* (register, login, logout, me, 2fa, refresh, change-password)
  routes/users.py      → /users/* (lista, update, ruoli, reset, toggle, delete)
  routes/audit.py      → /audit-log
  routes/maps.py       → /calcola-km
  routes/sedi.py       → /sedi
  routes/motivi.py     → /motivi-rimborso
  routes/rimborsi.py   → /rimborsi (CRUD + ricevute + contabile)
  routes/annunci.py    → /annunci (bacheca + download)
  routes/contatti.py   → /contatti (sidebar)
  routes/documenti.py  → /documenti (modulistica)
  routes/notifiche.py  → /notifiche
  routes/system.py     → /system/* (manutenzione)
  routes/reports.py    → /reports/* (export PDF/Excel/CSV)

Per avviare in sviluppo:
    uvicorn server:app --reload --port 8001

Documentazione API automatica:
    http://localhost:8001/docs (Swagger)
    http://localhost:8001/redoc (ReDoc)

==============================================
"""
import asyncio
import re
from urllib.parse import urlparse
import os
from datetime import datetime, timezone

from fastapi import APIRouter, FastAPI, Request
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse

# === Core moduli ===
from core.auth import hash_password
from core.config import FRONTEND_ORIGIN_REGEX, logger
from core.db import client, db
from core.rate_limit import limiter
from core.storage import sync_local_to_gridfs
from bson.errors import InvalidId
from core.scheduler import _pending_reimbursements_scheduler

# === Route modules ===
from routes import (
    annunci as routes_annunci,
    audit as routes_audit,
    auth as routes_auth,
    contatti as routes_contatti,
    documenti as routes_documenti,
    gdpr as routes_gdpr,
    maps as routes_maps,
    motivi as routes_motivi,
    notifiche as routes_notifiche,
    public as routes_public,
    reports as routes_reports,
    rimborsi as routes_rimborsi,
    sedi as routes_sedi,
    system as routes_system,
    users as routes_users,
)

# ==================== CONFIGURAZIONE APP ====================

APP_VERSION = "0.14.3-beta"
APP_BUILD_DATE = "2026-02-15"
APP_RELEASE_NAME = "Sede Nazionale"

app = FastAPI(
    title="SLA Sindacato - Portale Rimborsi",
    description="Gestione rimborsi e documenti per 30 concessionarie autostradali",
    version=APP_VERSION,
)

# ==================== RATE LIMITING (slowapi) ====================
# Attivato per proteggere endpoint sensibili (auth, reset password, google maps).
# Vedi core/rate_limit.py per configurazione.
app.state.limiter = limiter


@app.exception_handler(InvalidId)
async def invalid_id_handler(request: Request, exc: InvalidId):
    return JSONResponse(status_code=400, content={"detail": "Identificativo non valido"})


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """Risposta uniforme e in italiano quando un client supera il rate limit."""
    return JSONResponse(
        status_code=429,
        content={
            "detail": "Troppe richieste in poco tempo. Attendi qualche secondo e riprova.",
            "retry_after": str(exc.detail),
        },
        headers={"Retry-After": "60"},
    )

# === Aggregazione di tutti i router sotto /api ===
api_router = APIRouter(prefix="/api")
api_router.include_router(routes_public.router)
api_router.include_router(routes_auth.router)
api_router.include_router(routes_users.router)
api_router.include_router(routes_audit.router)
api_router.include_router(routes_maps.router)
api_router.include_router(routes_sedi.router)
api_router.include_router(routes_motivi.router)
api_router.include_router(routes_rimborsi.router)
api_router.include_router(routes_annunci.router)
api_router.include_router(routes_contatti.router)
api_router.include_router(routes_documenti.router)
api_router.include_router(routes_notifiche.router)
api_router.include_router(routes_system.router)
api_router.include_router(routes_reports.router)
api_router.include_router(routes_gdpr.router)


# ==================== STARTUP / SHUTDOWN ====================

@app.on_event("startup")
async def startup():
    await db.users.create_index("email", unique=True)
    await db.sedi.create_index("codice", unique=True)
    await db.login_attempts.create_index("identifier")

    # === MIGRAZIONE MULTI-RUOLO ===
    # Per ogni utente senza il campo `ruoli`, lo crea a partire da `ruolo` legacy.
    # NOTA: il campo `ruolo` (string) NON viene più scritto dal codice dal 15/02/2026.
    # Pianificare la rimozione fisica del campo dal DB dopo 30 giorni di stabilità
    # tramite uno $unset: db.users.update_many({}, {"$unset": {"ruolo": ""}})
    migrated = 0
    async for u in db.users.find({"ruoli": {"$exists": False}}, {"_id": 1, "ruolo": 1}):
        if u.get("ruolo"):
            await db.users.update_one(
                {"_id": u["_id"]},
                {"$set": {"ruoli": [u["ruolo"]]}},
            )
            migrated += 1
    if migrated:
        logger.info(f"Migrazione multi-ruolo: {migrated} utenti aggiornati con campo 'ruoli'.")

    # SuperAdmin creato SOLO al primo avvio: la password non viene più sovrascritta ai riavvii
    admin_email = os.environ["ADMIN_EMAIL"]
    admin_password = os.environ["ADMIN_PASSWORD"]

    existing = await db.users.find_one({"email": admin_email})
    if existing is None:
        hashed = hash_password(admin_password)
        await db.users.insert_one({
            "email": admin_email,
            "password_hash": hashed,
            "nome": "Super",
            "cognome": "Admin",
            "ruoli": ["superadmin"],
            "sede_id": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
        logger.info(f"SuperAdmin creato: {admin_email}")

    # Seed default motivi rimborso with richiede_note flag
    motivi_default = [
        {"nome": "RSA", "richiede_note": False},
        {"nome": "Sede", "richiede_note": False},
        {"nome": "Altro", "richiede_note": True},
    ]
    for motivo in motivi_default:
        existing_motivo = await db.motivi_rimborso.find_one({"nome": motivo["nome"]})
        if not existing_motivo:
            await db.motivi_rimborso.insert_one({
                "nome": motivo["nome"],
                "descrizione": None,
                "richiede_note": motivo["richiede_note"],
                "created_at": datetime.now(timezone.utc).isoformat(),
            })

    # Sede iniziale solo se non esiste ancora nessuna sede
    if await db.sedi.count_documents({}) == 0:
        await db.sedi.insert_one({
            "nome": "Autostrada del Brennero",
            "codice": "A22",
            "indirizzo": None,
            "tariffa_km": 0.35,
            "rimborso_pasti": 15.0,
            "rimborso_autostrada": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })

    logger.info("Database inizializzato")

    # === SCHEDULER PROMEMORIA RIMBORSI PENDENTI >7gg ===
    asyncio.create_task(_pending_reimbursements_scheduler())
    asyncio.create_task(sync_local_to_gridfs())
    logger.info("Scheduler promemoria rimborsi avviato")


@app.on_event("shutdown")
async def shutdown():
    client.close()


# Mount il router /api SUL app PRIMA dei middleware
app.include_router(api_router)


# ==================== SECURITY HEADERS MIDDLEWARE ====================
# Aggiunge header HTTP standard per protezione contro XSS, clickjacking,
# MIME sniffing, downgrade HTTPS. Si applicano a TUTTE le risposte.

_ORIGIN_RE = re.compile(FRONTEND_ORIGIN_REGEX)


@app.middleware("http")
async def csrf_origin_middleware(request: Request, call_next):
    """Blocca richieste che modificano dati provenienti da siti esterni (CSRF)."""
    if request.method in ("POST", "PUT", "PATCH", "DELETE"):
        origin = request.headers.get("origin") or request.headers.get("referer")
        if origin:
            host = urlparse(origin).netloc
            req_host = request.headers.get("x-forwarded-host") or request.headers.get("host", "")
            if host != req_host and not _ORIGIN_RE.fullmatch(f"{urlparse(origin).scheme}://{host}"):
                return JSONResponse(status_code=403, content={"detail": "Origine della richiesta non consentita"})
    return await call_next(request)


@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    response = await call_next(request)
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = (
        "camera=(), microphone=(), geolocation=(), payment=(), usb=()"
    )
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://maps.googleapis.com "
        "https://hcaptcha.com https://*.hcaptcha.com; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com "
        "https://hcaptcha.com https://*.hcaptcha.com; "
        "font-src 'self' https://fonts.gstatic.com data:; "
        "img-src 'self' data: blob: https://*.googleapis.com https://*.gstatic.com; "
        "connect-src 'self' https://maps.googleapis.com "
        "https://hcaptcha.com https://*.hcaptcha.com; "
        "frame-src https://hcaptcha.com https://*.hcaptcha.com; "
        "frame-ancestors 'none'; "
        "object-src 'none'; "
        "base-uri 'self'"
    )
    return response


# ==================== RATE LIMIT MIDDLEWARE ====================
# Deve stare DOPO il router per non intercettare le risposte custom (es. Retry-After).
app.add_middleware(SlowAPIMiddleware)


app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=FRONTEND_ORIGIN_REGEX,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
