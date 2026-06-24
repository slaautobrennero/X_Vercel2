"""
routes/system.py
Endpoint operativi/manutenzione (es. trigger manuale scheduler).
"""
from fastapi import APIRouter, HTTPException, Request

from core.auth import get_current_user
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
