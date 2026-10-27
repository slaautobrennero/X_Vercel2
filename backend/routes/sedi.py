"""
routes/sedi.py
Gestione concessionarie/sedi.
"""
from datetime import datetime, timezone

from bson import ObjectId
from typing import Literal, Optional

from pydantic import BaseModel, EmailStr, Field
from fastapi import APIRouter, HTTPException, Request

from core.auth import get_current_user
from core.db import db
from core.roles import (
    get_sede_nazionale_id,
    invalidate_sede_nazionale_cache,
    user_has_any_role,
    user_has_role,
)
from core.audit import _log_audit
from core import email as mail
from models_api import SedeCreate, SedeEmailContatto, SedeUpdate

router = APIRouter()


@router.get("/sedi")
async def get_sedi(request: Request):  # noqa: ARG001
    # Accesso non autenticato consentito (serve in registrazione)
    sedi = []
    async for sede in db.sedi.find({}, {"_id": 1, "nome": 1, "codice": 1, "indirizzo": 1, "tariffa_km": 1, "rimborso_pasti": 1, "rimborso_autostrada": 1, "is_nazionale": 1, "email_contatto": 1}):
        sede["id"] = str(sede["_id"])
        sede.pop("_id")
        sede["is_nazionale"] = bool(sede.get("is_nazionale", False))
        sedi.append(sede)
    return sedi


@router.get("/sedi/riepilogo-impostazioni")
async def riepilogo_impostazioni(request: Request):
    """SuperAdmin: impostazioni di tutte le concessionarie, Nazionale in cima."""
    user = await get_current_user(request)
    if not user_has_role(user, "superadmin"):
        raise HTTPException(status_code=403, detail="Solo il SuperAdmin")
    righe = []
    async for s in db.sedi.find({}):
        sid = str(s["_id"])
        righe.append({
            "id": sid,
            "nome": s["nome"],
            "codice": s.get("codice"),
            "is_nazionale": bool(s.get("is_nazionale")),
            "tariffa_km": s.get("tariffa_km"),
            "rimborso_pasti": s.get("rimborso_pasti"),
            "rimborso_autostrada": s.get("rimborso_autostrada"),
            "email_modalita": (s.get("email_config") or {}).get("modalita", "nessuna"),
            "motivi_propri": await db.motivi_rimborso.count_documents({"sede_ids": sid}),
            "cartelle_con_invio": await db.cartelle.count_documents({"sede_id": sid, "invio_email": {"$in": ["si"]}}),
            "utenti": await db.users.count_documents({"sede_id": sid}),
        })
    righe.sort(key=lambda r: (not r["is_nazionale"], r["nome"].lower()))
    return righe


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


@router.put("/sedi/{sede_id}/email-contatto")
async def update_email_contatto(sede_id: str, payload: SedeEmailContatto, request: Request):
    """Email a cui arrivano le risposte alle email del portale (Admin della sede o SuperAdmin)."""
    user = await get_current_user(request)
    if not (user_has_role(user, "superadmin") or (user_has_role(user, "admin") and user.get("sede_id") == sede_id)):
        raise HTTPException(status_code=403, detail="Solo l'Admin della concessionaria o il SuperAdmin")
    sede = await db.sedi.find_one({"_id": ObjectId(sede_id)})
    if not sede:
        raise HTTPException(status_code=404, detail="Sede non trovata")
    nuova = str(payload.email_contatto) if payload.email_contatto else None
    await db.sedi.update_one({"_id": sede["_id"]}, {"$set": {"email_contatto": nuova}})
    await _log_audit(actor=user, action="sede.email_contatto", target_type="sede", target_id=sede_id,
                     target_label=sede.get("nome", ""), sede_id=sede_id,
                     old_value=sede.get("email_contatto"), new_value=nuova)
    return {"message": "Email della concessionaria aggiornata", "email_contatto": nuova}


class EmailConfigUpdate(BaseModel):
    modalita: Literal["nessuna", "smtp", "emergent"]
    smtp_host: Optional[str] = Field(None, max_length=200)
    smtp_port: Optional[int] = Field(None, ge=1, le=65535)
    smtp_tls: Literal["starttls", "ssl"] = "starttls"
    smtp_user: Optional[str] = Field(None, max_length=200)
    smtp_password: Optional[str] = Field(None, max_length=300)
    smtp_from: Optional[EmailStr] = None


async def _sede_gestibile(sede_id: str, request: Request):
    user = await get_current_user(request)
    if not (user_has_role(user, "superadmin") or (user_has_role(user, "admin") and user.get("sede_id") == sede_id)):
        raise HTTPException(status_code=403, detail="Solo l'Admin della concessionaria o il SuperAdmin")
    sede = await db.sedi.find_one({"_id": ObjectId(sede_id)})
    if not sede:
        raise HTTPException(status_code=404, detail="Sede non trovata")
    return user, sede


def _cfg_pubblica(cfg: dict) -> dict:
    out = {k: v for k, v in cfg.items() if k != "smtp_password_enc"}
    out["password_impostata"] = bool(cfg.get("smtp_password_enc"))
    out.setdefault("modalita", "nessuna")
    out["emergent_disponibile"] = bool(mail.EMAIL_KEY)
    return out


@router.get("/sedi/{sede_id}/email-config")
async def get_email_config(sede_id: str, request: Request):
    _, sede = await _sede_gestibile(sede_id, request)
    return _cfg_pubblica(sede.get("email_config") or {})


@router.put("/sedi/{sede_id}/email-config")
async def update_email_config(sede_id: str, payload: EmailConfigUpdate, request: Request):
    user, sede = await _sede_gestibile(sede_id, request)
    vecchia = sede.get("email_config") or {}
    cfg = {**vecchia, "modalita": payload.modalita}
    if payload.modalita == "smtp":
        if not payload.smtp_host or not payload.smtp_port or not payload.smtp_user:
            raise HTTPException(status_code=400, detail="Per la casella email servono server, porta e utente")
        cfg.update(smtp_host=payload.smtp_host.strip(), smtp_port=payload.smtp_port, smtp_tls=payload.smtp_tls,
                   smtp_user=payload.smtp_user.strip(), smtp_from=str(payload.smtp_from) if payload.smtp_from else None)
        if payload.smtp_password:
            cfg["smtp_password_enc"] = mail.cifra(payload.smtp_password)
        elif vecchia.get("smtp_password_enc"):
            cfg["smtp_password_enc"] = vecchia["smtp_password_enc"]
        else:
            raise HTTPException(status_code=400, detail="Inserisci la password della casella email")
    if payload.modalita == "emergent" and not mail.EMAIL_KEY:
        raise HTTPException(status_code=400, detail="Il servizio a pagamento non è attivo su questo portale")
    await db.sedi.update_one({"_id": sede["_id"]}, {"$set": {"email_config": cfg}})
    await _log_audit(actor=user, action="sede.email_config", target_type="sede", target_id=sede_id,
                     target_label=sede.get("nome", ""), sede_id=sede_id,
                     old_value=vecchia.get("modalita", "nessuna"), new_value=payload.modalita)
    return _cfg_pubblica(cfg)


def _spiega_errore_smtp(e: Exception) -> str:
    import smtplib
    import socket
    if isinstance(e, smtplib.SMTPAuthenticationError):
        return "utente o password errati (per Gmail, Yahoo e iCloud serve la password per le app)"
    if isinstance(e, (ConnectionRefusedError, socket.gaierror)):
        return "server non raggiungibile: controlla nome del server e porta"
    if isinstance(e, (TimeoutError, socket.timeout)):
        return "il server non risponde: controlla porta e sicurezza (587 STARTTLS o 465 SSL)"
    if isinstance(e, smtplib.SMTPRecipientsRefused):
        return "il destinatario è stato rifiutato dal server"
    return str(e)[:200]


@router.post("/sedi/{sede_id}/email-config/test")
async def test_email_config(sede_id: str, request: Request):
    user, sede = await _sede_gestibile(sede_id, request)
    cfg = sede.get("email_config") or {}
    if cfg.get("modalita", "nessuna") == "nessuna":
        raise HTTPException(status_code=400, detail="Le email sono disattivate per questa concessionaria")
    try:
        await mail.invia_con_config(cfg, user["email"], mail.tpl_prova(), sede.get("email_contatto"))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invio non riuscito: {_spiega_errore_smtp(e)}")
    return {"message": f"Email di prova inviata a {user['email']}"}
