"""
routes/contatti.py
Link contatti sidebar (WhatsApp, Telegram, email, telefono, link generico).
"""
from datetime import datetime, timezone

from bson import ObjectId
from fastapi import APIRouter, HTTPException, Request

from core.auth import get_current_user
from core.db import db
from core.roles import user_has_any_role, user_has_role
from models_api import ContattoCreate, ContattoUpdate

router = APIRouter()

VALID_CONTATTO_TIPI = ["link", "whatsapp", "telegram", "email", "telefono"]
EDIT_CONTATTO_ROLES = ["admin", "segretario", "segreteria", "superadmin"]


@router.get("/contatti")
async def get_contatti(request: Request):
    """Restituisce i contatti della sede dell'utente. SuperAdmin/SuperUser vede tutti."""
    user = await get_current_user(request)

    query = {}
    if not user_has_any_role(user, ["superadmin", "superuser"]):
        query["sede_id"] = user.get("sede_id")

    contatti = []
    async for c in db.contatti.find(query).sort("ordine", 1):
        c["id"] = str(c["_id"])
        c.pop("_id")
        contatti.append(c)

    return contatti


@router.post("/contatti")
async def create_contatto(contatto_data: ContattoCreate, request: Request):
    user = await get_current_user(request)

    if not user_has_any_role(user, EDIT_CONTATTO_ROLES):
        raise HTTPException(status_code=403, detail="Permessi insufficienti")

    if contatto_data.tipo not in VALID_CONTATTO_TIPI:
        raise HTTPException(status_code=400, detail=f"Tipo non valido. Usa: {', '.join(VALID_CONTATTO_TIPI)}")

    contatto_doc = {
        "titolo": contatto_data.titolo,
        "descrizione": contatto_data.descrizione,
        "tipo": contatto_data.tipo,
        "valore": contatto_data.valore,
        "sede_id": user.get("sede_id"),
        "ordine": 0,
        "created_by": user["id"],
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    result = await db.contatti.insert_one(contatto_doc)
    contatto_doc["id"] = str(result.inserted_id)
    contatto_doc.pop("_id", None)

    return contatto_doc


@router.put("/contatti/{contatto_id}")
async def update_contatto(contatto_id: str, contatto_data: ContattoUpdate, request: Request):
    user = await get_current_user(request)

    if not user_has_any_role(user, EDIT_CONTATTO_ROLES):
        raise HTTPException(status_code=403, detail="Permessi insufficienti")

    contatto = await db.contatti.find_one({"_id": ObjectId(contatto_id)})
    if not contatto:
        raise HTTPException(status_code=404, detail="Contatto non trovato")

    if not user_has_role(user, "superadmin") and contatto.get("sede_id") != user.get("sede_id"):
        raise HTTPException(status_code=403, detail="Non autorizzato per questa sede")

    update_data = {k: v for k, v in contatto_data.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="Nessun dato da aggiornare")

    if "tipo" in update_data and update_data["tipo"] not in VALID_CONTATTO_TIPI:
        raise HTTPException(status_code=400, detail=f"Tipo non valido. Usa: {', '.join(VALID_CONTATTO_TIPI)}")

    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()

    await db.contatti.update_one({"_id": ObjectId(contatto_id)}, {"$set": update_data})

    return {"message": "Contatto aggiornato"}


@router.delete("/contatti/{contatto_id}")
async def delete_contatto(contatto_id: str, request: Request):
    user = await get_current_user(request)

    if not user_has_any_role(user, EDIT_CONTATTO_ROLES):
        raise HTTPException(status_code=403, detail="Permessi insufficienti")

    contatto = await db.contatti.find_one({"_id": ObjectId(contatto_id)})
    if not contatto:
        raise HTTPException(status_code=404, detail="Contatto non trovato")

    if not user_has_role(user, "superadmin") and contatto.get("sede_id") != user.get("sede_id"):
        raise HTTPException(status_code=403, detail="Non autorizzato per questa sede")

    await db.contatti.delete_one({"_id": ObjectId(contatto_id)})

    return {"message": "Contatto eliminato"}
