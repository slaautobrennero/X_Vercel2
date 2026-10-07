"""
Sistema MULTI-RUOLO.
Ogni utente ha un array `ruoli` (sorgente di verità).
Il campo legacy `ruolo` resta sincronizzato con ruoli[0] per retro-compat.
"""
from typing import List, Optional
from bson import ObjectId
from fastapi import HTTPException

from core.db import db

VALID_ROLES = ["superadmin", "superuser", "admin", "segretario", "segreteria", "cassiere", "delegato", "iscritto"]

# v0.14.0: cache in-memory della sede nazionale (id string). None se non ancora marcata.
_SEDE_NAZIONALE_CACHE: dict = {"id": None, "loaded": False}


async def get_sede_nazionale_id() -> Optional[str]:
    """
    Ritorna l'ID della sede marcata come nazionale (`is_nazionale=True`).
    Usa cache in-memory: prima chiamata legge dal DB, successive dalla cache.
    None se non c'è nessuna sede nazionale configurata.
    """
    if _SEDE_NAZIONALE_CACHE["loaded"]:
        return _SEDE_NAZIONALE_CACHE["id"]
    sede = await db.sedi.find_one({"is_nazionale": True}, {"_id": 1})
    _SEDE_NAZIONALE_CACHE["id"] = str(sede["_id"]) if sede else None
    _SEDE_NAZIONALE_CACHE["loaded"] = True
    return _SEDE_NAZIONALE_CACHE["id"]


def invalidate_sede_nazionale_cache() -> None:
    """Da chiamare dopo aver marcato/smarcato una sede come nazionale."""
    _SEDE_NAZIONALE_CACHE["id"] = None
    _SEDE_NAZIONALE_CACHE["loaded"] = False


async def is_sede_nazionale_member(user: Optional[dict], roles: Optional[List[str]] = None) -> bool:
    """
    True se l'utente appartiene alla sede nazionale e (opzionalmente)
    ha almeno uno dei ruoli indicati.
    - roles=None → verifica solo appartenenza sede nazionale
    - roles=[...] → verifica anche che possieda uno dei ruoli
    """
    if not user or not user.get("sede_id"):
        return False
    sede_naz = await get_sede_nazionale_id()
    if not sede_naz or str(user["sede_id"]) != sede_naz:
        return False
    if roles is None:
        return True
    return user_has_any_role(user, roles)


def _user_roles(user: Optional[dict]) -> List[str]:
    """Ritorna la lista dei ruoli di un utente, gestendo schema legacy."""
    if not user:
        return []
    ruoli = user.get("ruoli")
    if isinstance(ruoli, list) and ruoli:
        return ruoli
    ruolo_legacy = user.get("ruolo")
    return [ruolo_legacy] if ruolo_legacy else []


def user_has_role(user: Optional[dict], role: str) -> bool:
    """True se l'utente possiede il ruolo indicato."""
    return role in _user_roles(user)


def user_has_any_role(user: Optional[dict], roles: List[str]) -> bool:
    """True se l'utente possiede almeno uno dei ruoli indicati."""
    user_roles = _user_roles(user)
    return any(r in user_roles for r in roles)


def normalize_roles_input(ruoli: Optional[List[str]], ruolo_legacy: Optional[str]) -> List[str]:
    """
    Normalizza input ruoli da API: deduplica, valida, applica regole.
    Regola: se 'iscritto' è presente, deve essere l'unico ruolo.
    """
    raw: List[str] = []
    if ruoli:
        raw = list(ruoli)
    elif ruolo_legacy:
        raw = [ruolo_legacy]

    seen = set()
    cleaned: List[str] = []
    for r in raw:
        if r in VALID_ROLES and r not in seen:
            seen.add(r)
            cleaned.append(r)

    if not cleaned:
        raise HTTPException(status_code=400, detail="Nessun ruolo valido specificato")

    if "iscritto" in cleaned and len(cleaned) > 1:
        raise HTTPException(
            status_code=400,
            detail="Il ruolo 'iscritto' non può essere combinato con altri ruoli"
        )

    return cleaned
