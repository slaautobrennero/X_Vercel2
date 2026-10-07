"""
routes/sedi.py
Gestione concessionarie/sedi.
"""
from datetime import datetime, timezone

from bson import ObjectId
from fastapi import APIRouter, HTTPException, Request

from core.auth import get_current_user
from core.db import db
from core.roles import (
    get_sede_nazionale_id,
    invalidate_sede_nazionale_cache,
    user_has_any_role,
)
from models_api import SedeCreate, SedeUpdate

router = APIRouter()


@router.get("/sedi")
async def get_sedi(request: Request):  # noqa: ARG001
    # Accesso non autenticato consentito (serve in registrazione)
    sedi = []
    async for sede in db.sedi.find({}, {"_id": 1, "nome": 1, "codice": 1, "indirizzo": 1, "tariffa_km": 1, "rimborso_pasti": 1, "rimborso_autostrada": 1, "is_nazionale": 1}):
        sede["id"] = str(sede["_id"])
        sede.pop("_id")
        sede["is_nazionale"] = bool(sede.get("is_nazionale", False))
        sedi.append(sede)
    return sedi


@router.post("/sedi")
async def create_sede(sede_data: SedeCreate, request: Request):
    user = await get_current_user(request)
    if not user_has_any_role(user, ["superadmin"]):
        raise HTTPException(status_code=403, detail="Solo il SuperAdmin può creare sedi")

    existing = await db.sedi.find_one({"codice": sede_data.codice})
    if existing:
        raise HTTPException(status_code=400, detail="Codice sede già esistente")

    sede_doc = {
        "nome": sede_data.nome,
        "codice": sede_data.codice,
        "indirizzo": sede_data.indirizzo,
        "tariffa_km": sede_data.tariffa_km,
        "rimborso_pasti": sede_data.rimborso_pasti,
        "rimborso_autostrada": sede_data.rimborso_autostrada,
        "is_nazionale": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    result = await db.sedi.insert_one(sede_doc)
    sede_doc["id"] = str(result.inserted_id)
    sede_doc.pop("_id", None)
    return sede_doc


@router.put("/sedi/{sede_id}")
async def update_sede(sede_id: str, sede_data: SedeUpdate, request: Request):
    """
    Modifica dati anagrafici sede.
    - SuperAdmin: qualsiasi sede
    - Admin/Segretario appartenenti alla sede nazionale: possono modificare la nazionale
    - Admin: la propria sede (non-nazionale)
    """
    user = await get_current_user(request)

    if not user_has_any_role(user, ["superadmin", "admin", "segretario"]):
        raise HTTPException(status_code=403, detail="Permessi insufficienti")

    sede_naz_id = await get_sede_nazionale_id()

    if not user_has_any_role(user, ["superadmin"]):
        # Utente non superadmin: può modificare solo la propria sede
        if str(user.get("sede_id") or "") != sede_id:
            raise HTTPException(status_code=403, detail="Non autorizzato per questa sede")
        # Solo admin/segretario del nazionale può modificare la nazionale
        # (per sedi non-nazionali basta admin, segretario non modifica)
        is_nazionale_target = sede_naz_id == sede_id
        if is_nazionale_target and not user_has_any_role(user, ["admin", "segretario"]):
            raise HTTPException(status_code=403, detail="Serve ruolo admin o segretario del Nazionale")
        if not is_nazionale_target and not user_has_any_role(user, ["admin"]):
            raise HTTPException(status_code=403, detail="Serve ruolo admin per questa sede")

    update_data = {k: v for k, v in sede_data.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="Nessun dato da aggiornare")

    result = await db.sedi.update_one({"_id": ObjectId(sede_id)}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Sede non trovata")

    return {"message": "Sede aggiornata"}


@router.post("/sedi/{sede_id}/marca-nazionale")
async def marca_sede_nazionale(sede_id: str, request: Request):
    """
    SuperAdmin: marca una sede come nazionale (broadcast a tutte le sedi).
    Solo UNA sede alla volta può essere nazionale. Se ne esiste già una,
    verrà automaticamente smarcata.
    """
    user = await get_current_user(request)
    if not user_has_any_role(user, ["superadmin"]):
        raise HTTPException(status_code=403, detail="Solo il SuperAdmin")

    sede = await db.sedi.find_one({"_id": ObjectId(sede_id)})
    if not sede:
        raise HTTPException(status_code=404, detail="Sede non trovata")

    # Smarca eventuale sede nazionale esistente
    await db.sedi.update_many({"is_nazionale": True}, {"$set": {"is_nazionale": False}})
    # Marca questa
    await db.sedi.update_one({"_id": ObjectId(sede_id)}, {"$set": {"is_nazionale": True}})
    invalidate_sede_nazionale_cache()

    return {"message": f"Sede '{sede['nome']}' marcata come Nazionale"}


@router.delete("/sedi/{sede_id}")
async def delete_sede(sede_id: str, request: Request):
    user = await get_current_user(request)
    if not user_has_any_role(user, ["superadmin"]):
        raise HTTPException(status_code=403, detail="Solo il SuperAdmin può eliminare sedi")

    # Impedire cancellazione della sede nazionale
    sede_naz_id = await get_sede_nazionale_id()
    if sede_naz_id == sede_id:
        raise HTTPException(status_code=400, detail="Impossibile eliminare la sede Nazionale. Smarcala prima.")

    result = await db.sedi.delete_one({"_id": ObjectId(sede_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Sede non trovata")

    return {"message": "Sede eliminata"}
