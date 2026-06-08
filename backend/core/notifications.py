"""Helper notifiche utenti."""
from datetime import datetime, timezone
from typing import Optional
from bson import ObjectId
from .db import db


async def _notify_users_by_role(roles: list, sede_id: Optional[str], notifica_data: dict, include_global: bool = False):
    """
    Crea una notifica per ogni utente che ha uno dei ruoli indicati nella sede.
    Supporta schema legacy (`ruolo`) e multi-ruolo (`ruoli` array).
    """
    role_match = {"$or": [{"ruolo": {"$in": roles}}, {"ruoli": {"$in": roles}}]}
    if sede_id and include_global:
        query = {
            "$and": [
                role_match,
                {"$or": [{"sede_id": sede_id}, {"sede_id": None}]}
            ]
        }
    elif sede_id:
        query = {"$and": [role_match, {"sede_id": sede_id}]}
    else:
        query = role_match

    notifiche_to_insert = []
    async for u in db.users.find(query, {"_id": 1}):
        notifiche_to_insert.append({
            **notifica_data,
            "user_id": str(u["_id"]),
            "letto": False,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
    if notifiche_to_insert:
        await db.notifiche.insert_many(notifiche_to_insert)


async def _notify_user(user_id: str, notifica_data: dict):
    """Crea una notifica per un singolo utente."""
    await db.notifiche.insert_one({
        **notifica_data,
        "user_id": user_id,
        "letto": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
    })


async def _notify_all_in_sede(sede_id: Optional[str], notifica_data: dict, exclude_user_id: Optional[str] = None):
    """
    Notifica tutti utenti della sede + globali (sede_id None).
    Esclude opzionalmente l'autore.
    """
    if sede_id:
        base_query = {"$or": [{"sede_id": sede_id}, {"sede_id": None}]}
    else:
        base_query = {}

    if exclude_user_id:
        try:
            query = {"$and": [base_query, {"_id": {"$ne": ObjectId(exclude_user_id)}}]} if base_query else {"_id": {"$ne": ObjectId(exclude_user_id)}}
        except Exception:
            query = base_query
    else:
        query = base_query

    notifiche_to_insert = []
    async for u in db.users.find(query, {"_id": 1}):
        notifiche_to_insert.append({
            **notifica_data,
            "user_id": str(u["_id"]),
            "letto": False,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
    if notifiche_to_insert:
        await db.notifiche.insert_many(notifiche_to_insert)
