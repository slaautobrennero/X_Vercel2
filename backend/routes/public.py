"""
routes/public.py
Endpoint pubblici (no auth richiesta): versione, healthcheck.
"""
from fastapi import APIRouter

router = APIRouter()

APP_VERSION = "0.10.0-beta"
APP_BUILD_DATE = "2026-02-15"
APP_RELEASE_NAME = "Refactor server.py modulare + dep security + cleanup ruolo"


@router.get("/version")
async def get_version():
    """
    GET /api/version
    Restituisce versione applicazione (pubblico, no auth).
    Utile per verificare che frontend e backend siano allineati dopo deploy.
    """
    return {
        "version": APP_VERSION,
        "build_date": APP_BUILD_DATE,
        "release_name": APP_RELEASE_NAME,
    }
