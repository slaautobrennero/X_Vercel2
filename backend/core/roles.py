"""
Sistema MULTI-RUOLO.
Ogni utente ha un array `ruoli` (sorgente di verità).
Il campo legacy `ruolo` resta sincronizzato con ruoli[0] per retro-compat.
"""
from typing import List, Optional
from fastapi import HTTPException

VALID_ROLES = ["superadmin", "superuser", "admin", "segretario", "segreteria", "cassiere", "delegato", "iscritto"]


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
