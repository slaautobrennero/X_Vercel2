"""
routes/gdpr.py
Endpoint per compliance GDPR:
- Impostazioni Sindacato (dati titolare del trattamento)
- Documenti legali (privacy, cookie, termini) renderizzati da template + settings
- Diritti dell'interessato: accesso dati, esportazione, cancellazione con grace period
"""
from datetime import datetime, timezone, timedelta
from typing import Optional

from bson import ObjectId
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from core.audit import _log_audit
from core.auth import get_current_user
from core.db import db
from core.legal_templates import (
    PRIVACY_TEMPLATE, COOKIE_TEMPLATE, TERMINI_TEMPLATE,
    PRIVACY_VERSION, COOKIE_VERSION, TERMINI_VERSION,
    REGISTRO_TRATTAMENTI,
)
from core.roles import user_has_role

router = APIRouter()

# ==================== MODELS ====================

class ImpostazioniSindacatoIn(BaseModel):
    denominazione: str = "SLA - CISAL"
    sede_legale: str = "Via Arpinati 22/1 - 16035 Rapallo GE"
    codice_fiscale: str = "91027960102"
    partita_iva: Optional[str] = None
    pec: str = ""
    email_privacy: str = ""
    sito_web: str = ""
    dpo_nome: Optional[str] = None
    dpo_email: Optional[str] = None
    foro_competente: str = "Genova"


DEFAULT_SETTINGS = {
    "denominazione": "SLA - CISAL",
    "sede_legale": "Via Arpinati 22/1 - 16035 Rapallo GE",
    "codice_fiscale": "91027960102",
    "partita_iva": None,
    "pec": "sla-cisal@pec.example.it",  # placeholder, modificabile
    "email_privacy": "privacy@sla-cisal.example.it",  # placeholder
    "sito_web": "https://www.sla-cisal.example.it",  # placeholder
    "dpo_nome": None,
    "dpo_email": None,
    "foro_competente": "Genova",
}


# ==================== HELPERS ====================

async def get_settings() -> dict:
    """Restituisce le impostazioni sindacato correnti (o default se mancanti)."""
    doc = await db.impostazioni_sindacato.find_one({"_id": "singleton"})
    if not doc:
        # Prima chiamata: crea default
        doc = {"_id": "singleton", **DEFAULT_SETTINGS}
        await db.impostazioni_sindacato.insert_one(doc)
    return {k: v for k, v in doc.items() if k != "_id"}


def render_template(template: str, settings: dict) -> str:
    """Sostituisce i placeholder {{...}} nel template con i valori dai settings."""
    oggi = datetime.now().strftime("%d/%m/%Y")
    piva_riga = f"Partita IVA: {settings['partita_iva']}\n" if settings.get("partita_iva") else ""
    sito_web_riga = f"Sito web: {settings['sito_web']}\n" if settings.get("sito_web") else ""
    dpo_info = "Non è stato nominato un DPO obbligatorio ai sensi dell'art. 37 GDPR."
    if settings.get("dpo_nome"):
        dpo_email = settings.get("dpo_email", "-")
        dpo_info = f"**DPO nominato**: {settings['dpo_nome']} — email: {dpo_email}"

    replacements = {
        "{{denominazione}}": settings["denominazione"],
        "{{sede_legale}}": settings["sede_legale"],
        "{{codice_fiscale}}": settings["codice_fiscale"],
        "{{piva_riga}}": piva_riga,
        "{{pec}}": settings["pec"],
        "{{email_privacy}}": settings["email_privacy"],
        "{{sito_web_riga}}": sito_web_riga,
        "{{dpo_info}}": dpo_info,
        "{{foro_competente}}": settings["foro_competente"],
        "{{oggi}}": oggi,
        "{{privacy_version}}": PRIVACY_VERSION,
        "{{cookie_version}}": COOKIE_VERSION,
        "{{termini_version}}": TERMINI_VERSION,
    }
    out = template
    for k, v in replacements.items():
        out = out.replace(k, str(v))
    return out


# ==================== IMPOSTAZIONI SINDACATO ====================

@router.get("/impostazioni-sindacato")
async def get_impostazioni_sindacato():
    """Pubblico: dati titolare del trattamento (usati anche nell'informativa)."""
    return await get_settings()


@router.put("/impostazioni-sindacato")
async def update_impostazioni_sindacato(payload: ImpostazioniSindacatoIn, request: Request):
    """Solo SuperAdmin: aggiorna dati sindacato."""
    user = await get_current_user(request)
    if not user_has_role(user, "superadmin"):
        raise HTTPException(status_code=403, detail="Solo SuperAdmin")
    data = payload.model_dump()
    await db.impostazioni_sindacato.update_one(
        {"_id": "singleton"}, {"$set": data}, upsert=True
    )
    await _log_audit(user, "impostazioni.update", details=data)
    return {"ok": True, "settings": data}


# ==================== DOCUMENTI LEGALI (pubblici) ====================

@router.get("/privacy")
async def get_privacy():
    settings = await get_settings()
    return {
        "version": PRIVACY_VERSION,
        "contenuto": render_template(PRIVACY_TEMPLATE, settings),
    }


@router.get("/cookie-policy")
async def get_cookie_policy():
    settings = await get_settings()
    return {
        "version": COOKIE_VERSION,
        "contenuto": render_template(COOKIE_TEMPLATE, settings),
    }


@router.get("/termini")
async def get_termini():
    settings = await get_settings()
    return {
        "version": TERMINI_VERSION,
        "contenuto": render_template(TERMINI_TEMPLATE, settings),
    }


@router.get("/versioni-documenti")
async def get_versioni_documenti():
    """Versioni correnti dei documenti legali (utile per re-consenso)."""
    return {
        "privacy_version": PRIVACY_VERSION,
        "cookie_version": COOKIE_VERSION,
        "termini_version": TERMINI_VERSION,
    }


# ==================== DIRITTI DELL'INTERESSATO ====================

@router.get("/gdpr/my-data")
async def get_my_data(request: Request):
    """Diritto di accesso (art. 15 GDPR): tutti i dati personali dell'utente."""
    user = await get_current_user(request)
    user_id = str(user["_id"])

    # Dati anagrafici
    anagrafica = {k: v for k, v in user.items() if k not in ("password_hash", "totp_secret")}
    anagrafica["_id"] = str(anagrafica["_id"])
    if "sede_id" in anagrafica and anagrafica["sede_id"]:
        anagrafica["sede_id"] = str(anagrafica["sede_id"])

    # Rimborsi
    rimborsi_cursor = db.rimborsi.find({"user_id": ObjectId(user_id)})
    rimborsi = []
    async for r in rimborsi_cursor:
        r["_id"] = str(r["_id"])
        r["user_id"] = str(r["user_id"])
        if r.get("sede_id"):
            r["sede_id"] = str(r["sede_id"])
        rimborsi.append(r)

    # Consensi
    consensi_cursor = db.consensi_privacy.find({"user_id": ObjectId(user_id)})
    consensi = []
    async for c in consensi_cursor:
        c["_id"] = str(c["_id"])
        c["user_id"] = str(c["user_id"])
        consensi.append(c)

    return {
        "anagrafica": anagrafica,
        "rimborsi": rimborsi,
        "consensi_privacy": consensi,
        "estratto_il": datetime.now(timezone.utc).isoformat(),
        "info": "Questo estratto include tutti i tuoi dati personali gestiti dal portale.",
    }


class RichiestaCancellazioneIn(BaseModel):
    motivo: Optional[str] = None


@router.post("/gdpr/richiedi-cancellazione")
async def richiedi_cancellazione(payload: RichiestaCancellazioneIn, request: Request):
    """Diritto all'oblio (art. 17 GDPR): richiesta cancellazione con grace period 30gg."""
    user = await get_current_user(request)
    user_id = ObjectId(user["_id"])

    # Verifica se esiste già una richiesta pending
    existing = await db.richieste_cancellazione.find_one({
        "user_id": user_id,
        "stato": "pending",
    })
    if existing:
        raise HTTPException(
            status_code=400,
            detail="Hai già una richiesta di cancellazione in corso. Puoi annullarla dalla stessa sezione.",
        )

    now = datetime.now(timezone.utc)
    data_esecuzione = now + timedelta(days=30)
    doc = {
        "user_id": user_id,
        "email": user["email"],
        "motivo": payload.motivo or "",
        "stato": "pending",
        "richiesta_il": now,
        "esecuzione_prevista": data_esecuzione,
        "ip": request.client.host if request.client else None,
    }
    result = await db.richieste_cancellazione.insert_one(doc)
    await _log_audit(user, "gdpr.richiesta_cancellazione", details={"motivo": payload.motivo})
    return {
        "ok": True,
        "id": str(result.inserted_id),
        "esecuzione_prevista": data_esecuzione.isoformat(),
        "messaggio": "Richiesta ricevuta. Hai 30 giorni per annullarla. Trascorsi i quali i tuoi dati saranno cancellati (eccetto quelli soggetti a obbligo fiscale).",
    }


@router.post("/gdpr/annulla-cancellazione")
async def annulla_cancellazione(request: Request):
    user = await get_current_user(request)
    user_id = ObjectId(user["_id"])
    result = await db.richieste_cancellazione.update_one(
        {"user_id": user_id, "stato": "pending"},
        {"$set": {"stato": "annullata", "annullata_il": datetime.now(timezone.utc)}},
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Nessuna richiesta in corso da annullare.")
    await _log_audit(user, "gdpr.annulla_cancellazione")
    return {"ok": True, "messaggio": "Richiesta annullata. Il tuo account resta attivo."}


@router.get("/gdpr/stato-cancellazione")
async def stato_cancellazione(request: Request):
    """Stato attuale della richiesta di cancellazione dell'utente loggato."""
    user = await get_current_user(request)
    doc = await db.richieste_cancellazione.find_one(
        {"user_id": ObjectId(user["_id"]), "stato": "pending"}
    )
    if not doc:
        return {"pending": False}
    return {
        "pending": True,
        "richiesta_il": doc["richiesta_il"].isoformat(),
        "esecuzione_prevista": doc["esecuzione_prevista"].isoformat(),
        "giorni_residui": (doc["esecuzione_prevista"] - datetime.now(timezone.utc)).days,
    }


# ==================== REGISTRO TRATTAMENTI (SuperAdmin) ====================

@router.get("/gdpr/registro-trattamenti")
async def get_registro_trattamenti(request: Request):
    """Solo SuperAdmin: registro trattamenti art. 30 GDPR."""
    user = await get_current_user(request)
    if not user_has_role(user, "superadmin"):
        raise HTTPException(status_code=403, detail="Solo SuperAdmin")
    return {"trattamenti": REGISTRO_TRATTAMENTI, "titolare": await get_settings()}


@router.get("/gdpr/richieste-cancellazione")
async def list_richieste_cancellazione(request: Request):
    """Solo SuperAdmin: lista richieste cancellazione pendenti."""
    user = await get_current_user(request)
    if not user_has_role(user, "superadmin"):
        raise HTTPException(status_code=403, detail="Solo SuperAdmin")
    cursor = db.richieste_cancellazione.find({"stato": "pending"}).sort("richiesta_il", -1)
    out = []
    async for r in cursor:
        r["_id"] = str(r["_id"])
        r["user_id"] = str(r["user_id"])
        out.append(r)
    return {"richieste": out, "totale": len(out)}
