"""Cartelle documenti: create/eliminate da Admin (propria sede) e SuperAdmin, visibili o riservate."""
from datetime import datetime, timezone
from typing import Optional

from bson import ObjectId
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from core.auth import get_current_user
from core.db import db
from core.roles import get_sede_nazionale_id, is_sede_nazionale_member, user_has_any_role, user_has_role
from core.audit import _log_audit

router = APIRouter()

CATEGORIE_LEGACY = {"modulistica": "Modulistica", "documento": "Documenti", "altro": "Altro"}


class CartellaCreate(BaseModel):
    nome: str = Field(min_length=1, max_length=60)
    ambito: str = "sede"  # sede | tutte | nazionale
    sede_id: Optional[str] = None  # solo SuperAdmin con ambito=sede


class VisibilitaUpdate(BaseModel):
    visibile: bool


async def _sedi_amministrate(user: dict) -> set:
    """Ambiti (sede_id, None = tutte le sedi) che l'utente può amministrare."""
    ambiti = set()
    if user_has_role(user, "admin") and user.get("sede_id"):
        ambiti.add(user["sede_id"])
        if await is_sede_nazionale_member(user, roles=["admin"]):
            ambiti.add(None)
    return ambiti


async def puo_gestire(user: dict, cartella: dict) -> bool:
    if user_has_role(user, "superadmin"):
        return True
    return cartella.get("sede_id") in await _sedi_amministrate(user)


async def puo_vedere(user: dict, cartella: dict) -> bool:
    if not cartella.get("visibile", True):
        return await puo_gestire(user, cartella)
    if user_has_any_role(user, ["superadmin", "superuser"]):
        return True
    if await is_sede_nazionale_member(user, roles=["admin", "segretario"]):
        return True
    return cartella.get("sede_id") in (None, user.get("sede_id"))


async def puo_caricare(user: dict, cartella: dict) -> bool:
    if not user_has_any_role(user, ["segreteria", "segretario", "admin", "superadmin"]):
        return False
    if not await puo_vedere(user, cartella):
        return False
    if user_has_role(user, "superadmin"):
        return True
    sede = cartella.get("sede_id")
    if sede == user.get("sede_id"):
        return True
    return sede is None and await is_sede_nazionale_member(user, roles=["admin", "segretario", "segreteria"])


async def get_cartella(cartella_id: str) -> dict:
    cartella = await db.cartelle.find_one({"_id": ObjectId(cartella_id)})
    if not cartella:
        raise HTTPException(status_code=404, detail="Cartella non trovata")
    return cartella


async def cartelle_nascoste_per(user: dict) -> list:
    """ID (stringa) delle cartelle che l'utente NON può vedere."""
    nascoste = []
    async for c in db.cartelle.find({}):
        if not await puo_vedere(user, c):
            nascoste.append(str(c["_id"]))
    return nascoste


@router.get("/cartelle")
async def lista_cartelle(request: Request):
    user = await get_current_user(request)
    risultato = []
    async for c in db.cartelle.find({}).sort("nome", 1):
        if not await puo_vedere(user, c):
            continue
        cid = str(c["_id"])
        risultato.append({
            "id": cid,
            "nome": c["nome"],
            "sede_id": c.get("sede_id"),
            "visibile": c.get("visibile", True),
            "num_documenti": await db.documenti.count_documents({"cartella_id": cid}),
            "gestibile": await puo_gestire(user, c),
            "caricabile": await puo_caricare(user, c),
        })
    return risultato


@router.post("/cartelle")
async def crea_cartella(payload: CartellaCreate, request: Request):
    user = await get_current_user(request)
    if not user_has_any_role(user, ["admin", "superadmin"]):
        raise HTTPException(status_code=403, detail="Solo Admin e SuperAdmin possono creare cartelle")

    if payload.ambito == "tutte":
        sede_id = None
    elif payload.ambito == "nazionale":
        sede_id = await get_sede_nazionale_id()
        if not sede_id:
            raise HTTPException(status_code=400, detail="Nessuna Sede Nazionale configurata")
    elif user_has_role(user, "superadmin"):
        sede_id = payload.sede_id
    else:
        sede_id = user.get("sede_id")

    nuova = {"nome": payload.nome.strip(), "sede_id": sede_id}
    if not await puo_gestire(user, nuova):
        raise HTTPException(status_code=403, detail="Non puoi creare cartelle in questo ambito")
    if await db.cartelle.find_one({"nome": nuova["nome"], "sede_id": sede_id}):
        raise HTTPException(status_code=400, detail="Esiste già una cartella con questo nome")

    nuova.update({"visibile": True, "created_by": user["id"], "created_at": datetime.now(timezone.utc).isoformat()})
    result = await db.cartelle.insert_one(nuova)
    await _log_audit(actor=user, action="cartella.create", target_type="cartella", target_id=str(result.inserted_id),
                     target_label=nuova["nome"], sede_id=sede_id)
    return {"id": str(result.inserted_id), "nome": nuova["nome"], "sede_id": sede_id, "visibile": True}


@router.put("/cartelle/{cartella_id}/visibilita")
async def cambia_visibilita(cartella_id: str, payload: VisibilitaUpdate, request: Request):
    user = await get_current_user(request)
    cartella = await get_cartella(cartella_id)
    if not await puo_gestire(user, cartella):
        raise HTTPException(status_code=403, detail="Non autorizzato")
    await db.cartelle.update_one({"_id": cartella["_id"]}, {"$set": {"visibile": payload.visibile}})
    await _log_audit(actor=user, action="cartella.visibility", target_type="cartella", target_id=cartella_id,
                     target_label=cartella["nome"], sede_id=cartella.get("sede_id"),
                     old_value="visibile" if cartella.get("visibile", True) else "riservata",
                     new_value="visibile" if payload.visibile else "riservata")
    return {"message": "Visibilità aggiornata"}


@router.delete("/cartelle/{cartella_id}")
async def elimina_cartella(cartella_id: str, request: Request):
    user = await get_current_user(request)
    cartella = await get_cartella(cartella_id)
    if not await puo_gestire(user, cartella):
        raise HTTPException(status_code=403, detail="Non autorizzato")
    if await db.documenti.count_documents({"cartella_id": cartella_id}):
        raise HTTPException(status_code=400, detail="La cartella non è vuota: elimina prima i documenti al suo interno")
    await db.cartelle.delete_one({"_id": cartella["_id"]})
    await _log_audit(actor=user, action="cartella.delete", target_type="cartella", target_id=cartella_id,
                     target_label=cartella["nome"], sede_id=cartella.get("sede_id"))
    return {"message": "Cartella eliminata"}


async def migra_categorie_in_cartelle() -> None:
    """Una tantum: ogni categoria documenti (per sede) diventa una cartella."""
    async for doc in db.documenti.find({"cartella_id": {"$exists": False}}):
        nome = CATEGORIE_LEGACY.get(doc.get("categoria"), (doc.get("categoria") or "Generale").capitalize())
        sede_id = doc.get("sede_id")
        cartella = await db.cartelle.find_one({"nome": nome, "sede_id": sede_id})
        if not cartella:
            res = await db.cartelle.insert_one({"nome": nome, "sede_id": sede_id, "visibile": True,
                                                "created_at": datetime.now(timezone.utc).isoformat()})
            cid = str(res.inserted_id)
        else:
            cid = str(cartella["_id"])
        await db.documenti.update_one({"_id": doc["_id"]}, {"$set": {"cartella_id": cid}})
