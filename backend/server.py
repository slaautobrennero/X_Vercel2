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
import os
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, FastAPI, Request
from starlette.middleware.cors import CORSMiddleware

# === Core moduli ===
from core.auth import hash_password, verify_password
from core.config import FRONTEND_ORIGIN_REGEX, logger
from core.db import client, db
from core.scheduler import _pending_reimbursements_scheduler

# === Route modules ===
from routes import (
    annunci as routes_annunci,
    audit as routes_audit,
    auth as routes_auth,
    contatti as routes_contatti,
    documenti as routes_documenti,
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

APP_VERSION = "0.10.1-beta"
APP_BUILD_DATE = "2026-02-15"
APP_RELEASE_NAME = "Refactor server.py modulare + dep security + cleanup ruolo"

app = FastAPI(
    title="SLA Sindacato - Portale Rimborsi",
    description="Gestione rimborsi e documenti per 30 concessionarie autostradali",
    version=APP_VERSION,
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
            "ruoli": ["superadmin"],
            "sede_id": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
        logger.info(f"SuperAdmin creato: {admin_email}")
    elif not verify_password(admin_password, existing["password_hash"]):
        await db.users.update_one(
            {"email": admin_email},
            {"$set": {"password_hash": hash_password(admin_password)}},
        )
        logger.info("Password SuperAdmin aggiornata")

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
            "created_at": datetime.now(timezone.utc).isoformat(),
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

    # === SCHEDULER PROMEMORIA RIMBORSI PENDENTI >7gg ===
    asyncio.create_task(_pending_reimbursements_scheduler())
    logger.info("Scheduler promemoria rimborsi avviato")


@app.on_event("shutdown")
async def shutdown():
    client.close()


# Mount il router /api SUL app PRIMA dei middleware
app.include_router(api_router)


# ==================== SECURITY HEADERS MIDDLEWARE ====================
# Aggiunge header HTTP standard per protezione contro XSS, clickjacking,
# MIME sniffing, downgrade HTTPS. Si applicano a TUTTE le risposte.

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
        "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://maps.googleapis.com; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com data:; "
        "img-src 'self' data: blob: https://*.googleapis.com https://*.gstatic.com; "
        "connect-src 'self' https://maps.googleapis.com; "
        "frame-ancestors 'none'; "
        "object-src 'none'; "
        "base-uri 'self'"
    )
    return response


app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=FRONTEND_ORIGIN_REGEX,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
