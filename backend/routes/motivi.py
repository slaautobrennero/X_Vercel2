"""
routes/motivi.py
Gestione motivi-rimborso (RSA, Sede, Altro, ...).
"""
from datetime import datetime, timezone

from bson import ObjectId
from fastapi import APIRouter, HTTPException, Request

from core.auth import get_current_user
from core.db import db
from core.roles import user_has_any_role
from models_api import MotivoRimborsoCreate, MotivoRimborsoUpdate

router = APIRouter()


@router.get("/motivi-rimborso")
async def get_motivi_rimborso(request: Request):
    await get_current_user(request)
    motivi = []
    async for motivo in db.motivi_rimborso.find({}):
        motivo["id"] = str(motivo["_id"])
        motivo.pop("_id")
        motivi.append(motivo)
    return motivi


@router.post("/motivi-rimborso")
async def create_motivo_rimborso(motivo_data: MotivoRimborsoCreate, request: Request):
    user = await get_current_user(request)
    if not user_has_any_role(user, ["superadmin"]):
        raise HTTPException(status_code=403, detail="Solo il SuperAdmin può gestire i motivi")

    motivo_doc = {
        "nome": motivo_data.nome,
        "descrizione": motivo_data.descrizione,
        "richiede_note": motivo_data.richiede_note,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    result = await db.motivi_rimborso.insert_one(motivo_doc)
    motivo_doc["id"] = str(result.inserted_id)
    motivo_doc.pop("_id", None)
    return motivo_doc


@router.put("/motivi-rimborso/{motivo_id}")
async def update_motivo_rimborso(motivo_id: str, motivo_data: MotivoRimborsoUpdate, request: Request):
    user = await get_current_user(request)
    if not user_has_any_role(user, ["superadmin"]):
        raise HTTPException(status_code=403, detail="Solo il SuperAdmin può gestire i motivi")

    update_data = {k: v for k, v in motivo_data.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="Nessun dato da aggiornare")

    result = await db.motivi_rimborso.update_one({"_id": ObjectId(motivo_id)}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Motivo non trovato")

    return {"message": "Motivo aggiornato"}


@router.delete("/motivi-rimborso/{motivo_id}")
async def delete_motivo_rimborso(motivo_id: str, request: Request):
    user = await get_current_user(request)
    if not user_has_any_role(user, ["superadmin"]):
        raise HTTPException(status_code=403, detail="Solo il SuperAdmin può gestire i motivi")

    result = await db.motivi_rimborso.delete_one({"_id": ObjectId(motivo_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Motivo non trovato")

    return {"message": "Motivo eliminato"}
