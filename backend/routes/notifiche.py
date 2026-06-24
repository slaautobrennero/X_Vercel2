"""
routes/notifiche.py
Notifiche utente: lista, mark-as-read singola e di gruppo.
"""
from bson import ObjectId
from fastapi import APIRouter, Request

from core.auth import get_current_user
from core.db import db

router = APIRouter()


@router.get("/notifiche")
async def get_notifiche(request: Request):
    user = await get_current_user(request)

    # Notifiche dirette all'utente + retrocompat con vecchie (user_id=None, sede_id specifica)
    query = {"$or": [
        {"user_id": user["id"]},
        {"user_id": None, "sede_id": user.get("sede_id")},
    ]}

    notifiche = []
    async for notifica in db.notifiche.find(query).sort("created_at", -1).limit(50):
        notifica["id"] = str(notifica["_id"])
        notifica.pop("_id")
        notifiche.append(notifica)

    return notifiche


@router.put("/notifiche/{notifica_id}/letto")
async def mark_notifica_letta(notifica_id: str, request: Request):
    await get_current_user(request)  # solo per autenticare

    await db.notifiche.update_one(
        {"_id": ObjectId(notifica_id)},
        {"$set": {"letto": True}},
    )

    return {"message": "Notifica segnata come letta"}


@router.put("/notifiche/letto-tutte")
async def mark_all_notifiche_lette(request: Request):
    user = await get_current_user(request)

    query = {"$or": [
        {"user_id": user["id"]},
        {"user_id": None, "sede_id": user.get("sede_id")},
    ]}

    await db.notifiche.update_many(query, {"$set": {"letto": True}})

    return {"message": "Tutte le notifiche segnate come lette"}
