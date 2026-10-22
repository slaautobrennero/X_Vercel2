"""
routes/system.py
Endpoint operativi/manutenzione (es. trigger manuale scheduler).
"""
from fastapi import APIRouter, HTTPException, Request

import os

from bson import ObjectId

from core.auth import get_current_user, verify_password
from core.captcha import hcaptcha_enabled
from core.db import db
from core.roles import user_has_any_role
from core.scheduler import _check_pending_reimbursements

router = APIRouter()


@router.post("/system/check-pending-reimbursements")
async def trigger_pending_check(request: Request):
    """Lancia manualmente il check rimborsi pendenti >7gg (solo superadmin/admin).
    Utile per testing e debug. In produzione lo scheduler automatico gira ogni notte."""
    user = await get_current_user(request)
    if not user_has_any_role(user, ["superadmin", "admin"]):
        raise HTTPException(status_code=403, detail="Permessi insufficienti")
    result = await _check_pending_reimbursements()
    return result


@router.get("/system/avvisi-sicurezza")
async def avvisi_sicurezza(request: Request):
    """Avvisi di configurazione per il SuperAdmin."""
    user = await get_current_user(request)
    if not user_has_any_role(user, ["superadmin"]):
        raise HTTPException(status_code=403, detail="Solo SuperAdmin")
    avvisi = []
    if not hcaptcha_enabled():
        avvisi.append("Verifica anti-robot (hCaptcha) disattivata: imposta HCAPTCHA_SECRET in docker/.env.")
    doc = await db.users.find_one({"_id": ObjectId(user["id"])}, {"password_hash": 1})
    if os.environ.get("ADMIN_PASSWORD") and verify_password(os.environ["ADMIN_PASSWORD"], doc["password_hash"]):
        avvisi.append("Stai ancora usando la password iniziale del SuperAdmin: cambiala dal Profilo.")
    if not user.get("totp_enabled"):
        avvisi.append("La verifica in due passaggi (2FA) non è attiva sul tuo account: attivala dal Profilo.")
    return {"avvisi": avvisi}
