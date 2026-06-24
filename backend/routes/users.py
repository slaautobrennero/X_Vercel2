"""
routes/users.py
Gestione utenti: lista, update, cambio ruoli, reset password, disabilita, cancella.
"""
from datetime import datetime, timezone

from bson import ObjectId
from fastapi import APIRouter, HTTPException, Request

from core.audit import _log_audit
from core.auth import (
    generate_temporary_password, get_current_user, hash_password,
)
from core.db import db
from core.roles import normalize_roles_input, user_has_any_role, user_has_role
from models_api import ToggleDisableRequest, UpdateRuoliRequest, UserUpdate

router = APIRouter()


@router.post("/users/{user_id}/reset-password")
async def admin_reset_password(user_id: str, request: Request):
    """Admin/Segretario/SuperAdmin genera password temporanea per un utente."""
    current_user = await get_current_user(request)

    if not user_has_any_role(current_user, ["admin", "segretario", "superadmin"]):
        raise HTTPException(status_code=403, detail="Permessi insufficienti")

    target_user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not target_user:
        raise HTTPException(status_code=404, detail="Utente non trovato")

    if not user_has_role(current_user, "superadmin"):
        if target_user.get("sede_id") != current_user.get("sede_id"):
            raise HTTPException(status_code=403, detail="Non autorizzato per questa sede")
        if user_has_any_role(target_user, ["superadmin", "superuser"]):
            raise HTTPException(status_code=403, detail="Non autorizzato a resettare questo ruolo")

    temp_password = generate_temporary_password(12)

    await db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {
            "password_hash": hash_password(temp_password),
            "password_reset_at": datetime.now(timezone.utc).isoformat(),
            "password_reset_by": current_user["id"],
            "must_change_password": True,
        }},
    )

    await db.notifiche.insert_one({
        "user_id": user_id,
        "sede_id": target_user.get("sede_id"),
        "tipo": "sicurezza",
        "titolo": "Password reimpostata",
        "messaggio": f"La tua password è stata reimpostata da {current_user['nome']} {current_user['cognome']}. Accedi con la nuova password ricevuta e cambiala al primo accesso.",
        "letto": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
    })

    await _log_audit(
        actor=current_user,
        action="user.reset_password",
        target_type="user",
        target_id=user_id,
        target_label=f"{target_user.get('nome', '')} {target_user.get('cognome', '')} ({target_user.get('email', '')})".strip(),
        sede_id=target_user.get("sede_id"),
    )

    return {
        "message": "Password reimpostata con successo",
        "temporary_password": temp_password,
        "user_email": target_user["email"],
    }


@router.put("/users/{user_id}/toggle-disabled")
async def toggle_user_disabled(user_id: str, data: ToggleDisableRequest, request: Request):
    """Admin/Segretario/SuperAdmin disattiva o riattiva un utente (soft)."""
    current_user = await get_current_user(request)

    if not user_has_any_role(current_user, ["admin", "segretario", "superadmin"]):
        raise HTTPException(status_code=403, detail="Permessi insufficienti")

    if user_id == current_user["id"]:
        raise HTTPException(status_code=400, detail="Non puoi disattivare il tuo stesso account")

    target_user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not target_user:
        raise HTTPException(status_code=404, detail="Utente non trovato")

    if not user_has_role(current_user, "superadmin"):
        if target_user.get("sede_id") != current_user.get("sede_id"):
            raise HTTPException(status_code=403, detail="Non autorizzato per questa sede")
        if user_has_any_role(target_user, ["superadmin", "superuser"]):
            raise HTTPException(status_code=403, detail="Non autorizzato a modificare questo ruolo")

    update_fields = {
        "disabled": data.disabled,
        "disabled_at": datetime.now(timezone.utc).isoformat() if data.disabled else None,
        "disabled_by": current_user["id"] if data.disabled else None,
    }

    await db.users.update_one({"_id": ObjectId(user_id)}, {"$set": update_fields})

    await _log_audit(
        actor=current_user,
        action="user.disable" if data.disabled else "user.enable",
        target_type="user",
        target_id=user_id,
        target_label=f"{target_user.get('nome', '')} {target_user.get('cognome', '')} ({target_user.get('email', '')})".strip(),
        sede_id=target_user.get("sede_id"),
        old_value="active" if not target_user.get("disabled") else "disabled",
        new_value="disabled" if data.disabled else "active",
    )

    return {
        "message": "Utente disattivato" if data.disabled else "Utente riattivato",
        "disabled": data.disabled,
    }


@router.delete("/users/{user_id}")
async def delete_user(user_id: str, request: Request):
    """Cancellazione definitiva utente. Solo SuperAdmin."""
    current_user = await get_current_user(request)

    if not user_has_role(current_user, "superadmin"):
        raise HTTPException(status_code=403, detail="Solo SuperAdmin può cancellare definitivamente gli utenti")

    if user_id == current_user["id"]:
        raise HTTPException(status_code=400, detail="Non puoi cancellare il tuo stesso account")

    target_user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not target_user:
        raise HTTPException(status_code=404, detail="Utente non trovato")

    user_label = "[utente eliminato]"

    await db.rimborsi.update_many(
        {"user_id": user_id},
        {"$set": {"user_nome": user_label, "user_eliminato": True}},
    )
    await db.annunci.update_many(
        {"autore_id": user_id},
        {"$set": {"autore_nome": user_label, "autore_eliminato": True}},
    )
    await db.notifiche.delete_many({"user_id": user_id})
    await db.users.delete_one({"_id": ObjectId(user_id)})

    await _log_audit(
        actor=current_user,
        action="user.delete",
        target_type="user",
        target_id=user_id,
        target_label=f"{target_user.get('nome', '')} {target_user.get('cognome', '')} ({target_user.get('email', '')})".strip(),
        sede_id=target_user.get("sede_id"),
        old_value=target_user.get("ruoli") or ([target_user["ruolo"]] if target_user.get("ruolo") else None),
        note="Cancellazione definitiva, dati anonimizzati nei record storici",
    )

    return {"message": "Utente cancellato definitivamente"}


@router.get("/users")
async def get_users(request: Request):
    user = await get_current_user(request)

    if not user_has_any_role(user, ["admin", "cassiere", "superadmin", "superuser", "segretario"]):
        raise HTTPException(status_code=403, detail="Permessi insufficienti")

    query = {}
    if not user_has_any_role(user, ["superadmin", "superuser"]):
        query["sede_id"] = user.get("sede_id")

    users = []
    async for u in db.users.find(query, {"password_hash": 0}):
        u["id"] = str(u["_id"])
        u.pop("_id")
        # Multi-ruolo: garantisci campo `ruoli` sempre presente
        if not u.get("ruoli"):
            u["ruoli"] = [u["ruolo"]] if u.get("ruolo") else []
        if u.get("sede_id"):
            sede = await db.sedi.find_one({"_id": ObjectId(u["sede_id"])})
            if sede:
                u["sede_nome"] = sede["nome"]
        users.append(u)

    return users


@router.put("/users/{user_id}")
async def update_user(user_id: str, user_data: UserUpdate, request: Request):
    current_user = await get_current_user(request)

    if user_id != current_user["id"] and not user_has_any_role(current_user, ["admin", "superadmin"]):
        raise HTTPException(status_code=403, detail="Permessi insufficienti")

    update_data = {k: v for k, v in user_data.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="Nessun dato da aggiornare")

    await db.users.update_one({"_id": ObjectId(user_id)}, {"$set": update_data})

    return {"message": "Utente aggiornato"}


@router.put("/users/{user_id}/ruolo")
async def update_user_role(user_id: str, request: Request, payload: UpdateRuoliRequest):
    """
    Aggiorna i ruoli di un utente.
    Vincoli:
    - 'iscritto' non combinabile con altri ruoli
    - Solo superadmin può assegnare/togliere superuser/superadmin
    """
    current_user = await get_current_user(request)

    if not user_has_any_role(current_user, ["admin", "superadmin"]):
        raise HTTPException(status_code=403, detail="Permessi insufficienti")

    valid_roles = ["iscritto", "delegato", "segreteria", "segretario", "cassiere", "admin"]
    if user_has_role(current_user, "superadmin"):
        valid_roles.extend(["superuser", "superadmin"])

    for r in payload.ruoli:
        if r not in valid_roles:
            raise HTTPException(status_code=400, detail=f"Ruolo '{r}' non assegnabile")

    nuovi_ruoli = normalize_roles_input(payload.ruoli, None)

    target_user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not target_user:
        raise HTTPException(status_code=404, detail="Utente non trovato")

    await db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"ruoli": nuovi_ruoli}},
    )

    old_ruoli = target_user.get("ruoli") or [target_user.get("ruolo")]
    if sorted(old_ruoli) != sorted(nuovi_ruoli):
        await _log_audit(
            actor=current_user,
            action="user.change_role",
            target_type="user",
            target_id=user_id,
            target_label=f"{target_user.get('nome', '')} {target_user.get('cognome', '')} ({target_user.get('email', '')})".strip(),
            sede_id=target_user.get("sede_id"),
            old_value=", ".join(old_ruoli),
            new_value=", ".join(nuovi_ruoli),
        )

    return {"message": "Ruoli aggiornati", "ruoli": nuovi_ruoli}
