"""
routes/audit.py
Log eventi di sistema (audit log) — visualizzazione e filtri.
"""
from typing import Optional

from fastapi import APIRouter, HTTPException, Request

from core.auth import get_current_user
from core.db import db
from core.roles import user_has_any_role

router = APIRouter()


@router.get("/audit-log")
async def get_audit_log(
    request: Request,
    target_type: Optional[str] = None,
    target_id: Optional[str] = None,
    action: Optional[str] = None,
    limit: int = 100,
):
    """
    Restituisce gli eventi audit.
    - SuperAdmin/SuperUser: vede tutto
    - Admin/Cassiere/Segretario: vede solo la propria sede
    - Altri ruoli: forbidden

    Filtri opzionali: target_type, target_id, action
    """
    user = await get_current_user(request)

    if not user_has_any_role(user, ["superadmin", "superuser", "admin", "cassiere", "segretario"]):
        raise HTTPException(status_code=403, detail="Permessi insufficienti")

    query = {}
    if not user_has_any_role(user, ["superadmin", "superuser"]):
        query["sede_id"] = user.get("sede_id")

    if target_type:
        query["target_type"] = target_type
    if target_id:
        query["target_id"] = target_id
    if action:
        query["action"] = action

    limit = min(max(limit, 1), 500)

    entries = []
    async for entry in db.audit_log.find(query).sort("created_at", -1).limit(limit):
        entry["id"] = str(entry["_id"])
        entry.pop("_id")
        entries.append(entry)

    return entries
