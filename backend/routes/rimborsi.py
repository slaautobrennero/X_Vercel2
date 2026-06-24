"""
routes/rimborsi.py
Gestione rimborsi: CRUD, ricevute, ricevute-spese, contabile.
"""
import uuid
from datetime import datetime, timezone
from typing import List, Optional

import aiofiles
from bson import ObjectId
from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse

from core.audit import _log_audit
from core.auth import get_current_user
from core.config import UPLOAD_DIR
from core.db import db
from core.notifications import _notify_user, _notify_users_by_role
from core.roles import user_has_any_role
from models_api import RimborsoCreate, RimborsoUpdate

router = APIRouter()


@router.get("/rimborsi")
async def get_rimborsi(
    request: Request,
    stato: Optional[str] = None,
    anno: Optional[int] = None,
    data_da: Optional[str] = None,
    data_a: Optional[str] = None,
    user_id: Optional[str] = None,
    sede_id: Optional[str] = None,
    motivo_id: Optional[str] = None,
    importo_min: Optional[float] = None,
    importo_max: Optional[float] = None,
):
    user = await get_current_user(request)

    query: dict = {}

    # Scope: superadmin/superuser → tutti; admin/cassiere → sede; altri → solo i propri
    if not user_has_any_role(user, ["superadmin", "superuser"]):
        if user_has_any_role(user, ["admin", "cassiere"]):
            query["sede_id"] = user.get("sede_id")
        else:
            query["user_id"] = user["id"]

    if stato:
        query["stato"] = stato

    if data_da or data_a:
        date_range: dict = {}
        if data_da:
            date_range["$gte"] = data_da
        if data_a:
            date_range["$lte"] = data_a
        query["data"] = date_range
    elif anno:
        query["data"] = {"$regex": f"^{anno}"}

    if user_id and user_has_any_role(user, ["admin", "cassiere", "superadmin", "superuser"]):
        query["user_id"] = user_id

    if sede_id and user_has_any_role(user, ["superadmin", "superuser"]):
        query["sede_id"] = sede_id

    if motivo_id:
        query["motivo_id"] = motivo_id

    if importo_min is not None or importo_max is not None:
        importo_range: dict = {}
        if importo_min is not None:
            importo_range["$gte"] = importo_min
        if importo_max is not None:
            importo_range["$lte"] = importo_max
        query["importo_totale"] = importo_range

    rimborsi = []
    async for rimborso in db.rimborsi.find(query).sort("created_at", -1):
        rimborso["id"] = str(rimborso["_id"])
        rimborso.pop("_id")

        rimborso_user = await db.users.find_one({"_id": ObjectId(rimborso["user_id"])})
        if rimborso_user:
            rimborso["user_nome"] = f"{rimborso_user['nome']} {rimborso_user['cognome']}"

        if rimborso.get("motivo_id"):
            motivo = await db.motivi_rimborso.find_one({"_id": ObjectId(rimborso["motivo_id"])})
            if motivo:
                rimborso["motivo_nome"] = motivo["nome"]

        rimborsi.append(rimborso)

    return rimborsi


@router.post("/rimborsi")
async def create_rimborso(rimborso_data: RimborsoCreate, request: Request):
    """
    Crea una nuova richiesta di rimborso.

    Regole speciali:
    - Iscritti NON possono richiedere rimborsi
    - Motivo "Altro" richiede note obbligatorie
    - Se km_modificati_manualmente=True, genera alert per admin
    - Calcolo: (KM totali * tariffa_km) + pasti + autostrada
    """
    user = await get_current_user(request)

    if not user_has_any_role(user, ["delegato", "segreteria", "segretario", "admin", "superadmin"]):
        raise HTTPException(status_code=403, detail="Gli iscritti non possono richiedere rimborsi")

    motivo = await db.motivi_rimborso.find_one({"_id": ObjectId(rimborso_data.motivo_id)})
    if motivo and motivo.get("richiede_note") and not rimborso_data.note:
        raise HTTPException(status_code=400, detail="Per questo motivo le note sono obbligatorie")

    sede = None
    if user.get("sede_id"):
        sede = await db.sedi.find_one({"_id": ObjectId(user["sede_id"])})

    tariffa_km = sede["tariffa_km"] if sede else 0.35

    km_totali = rimborso_data.km_andata * (2 if rimborso_data.andata_ritorno else 1)
    importo_km = km_totali * tariffa_km
    importo_autostrada = rimborso_data.costo_autostrada if rimborso_data.uso_autostrada else 0
    importo_pasti = rimborso_data.importo_pasti
    importo_totale = importo_km + importo_pasti + importo_autostrada

    rimborso_doc = {
        "user_id": user["id"],
        "sede_id": user.get("sede_id"),
        "data": rimborso_data.data,
        "motivo_id": rimborso_data.motivo_id,
        "indirizzo_partenza": rimborso_data.indirizzo_partenza,
        "indirizzo_partenza_tipo": rimborso_data.indirizzo_partenza_tipo,
        "indirizzo_arrivo": rimborso_data.indirizzo_arrivo,
        "km_andata": rimborso_data.km_andata,
        "km_calcolati": rimborso_data.km_calcolati,
        "km_modificati_manualmente": rimborso_data.km_modificati_manualmente,
        "andata_ritorno": rimborso_data.andata_ritorno,
        "km_totali": km_totali,
        "uso_autostrada": rimborso_data.uso_autostrada,
        "costo_autostrada": importo_autostrada,
        "importo_pasti": importo_pasti,
        "numero_partecipanti_pasto": rimborso_data.numero_partecipanti_pasto,
        "tariffa_km": tariffa_km,
        "importo_km": importo_km,
        "importo_totale": importo_totale,
        "note": rimborso_data.note,
        "stato": "in_attesa",
        "ricevute": [],
        "ricevute_spese": [],
        "km_approvati": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    result = await db.rimborsi.insert_one(rimborso_doc)
    rimborso_doc["id"] = str(result.inserted_id)
    rimborso_doc.pop("_id", None)

    notifica_msg = f"{user['nome']} {user['cognome']} ha inviato una richiesta di rimborso di €{importo_totale:.2f}"
    if rimborso_data.km_modificati_manualmente:
        notifica_msg += " - ATTENZIONE: KM modificati manualmente!"

    await _notify_users_by_role(
        roles=["admin", "cassiere"],
        sede_id=user.get("sede_id"),
        notifica_data={
            "tipo": "rimborso",
            "titolo": "Nuova richiesta rimborso" + (" ⚠️ KM MODIFICATI" if rimborso_data.km_modificati_manualmente else ""),
            "messaggio": notifica_msg,
            "rimborso_id": str(result.inserted_id),
            "alert_km": rimborso_data.km_modificati_manualmente,
        },
        include_global=False,
    )

    return rimborso_doc


@router.post("/rimborsi/{rimborso_id}/ricevute")
async def upload_ricevuta(rimborso_id: str, request: Request, file: UploadFile = File(...)):
    user = await get_current_user(request)

    rimborso = await db.rimborsi.find_one({"_id": ObjectId(rimborso_id)})
    if not rimborso:
        raise HTTPException(status_code=404, detail="Rimborso non trovato")

    if rimborso["user_id"] != user["id"] and not user_has_any_role(user, ["admin", "superadmin"]):
        raise HTTPException(status_code=403, detail="Non autorizzato")

    if file.content_type not in ["application/pdf", "image/jpeg", "image/png", "image/jpg"]:
        raise HTTPException(status_code=400, detail="Formato file non supportato. Usa PDF, JPG o PNG")

    content = await file.read()
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File troppo grande. Max 5MB")

    file_id = str(uuid.uuid4())
    ext = file.filename.split(".")[-1] if "." in file.filename else "pdf"
    filename = f"{file_id}.{ext}"
    filepath = UPLOAD_DIR / filename

    async with aiofiles.open(filepath, "wb") as f:
        await f.write(content)

    ricevuta = {
        "id": file_id,
        "filename": file.filename,
        "path": filename,
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
    }

    await db.rimborsi.update_one(
        {"_id": ObjectId(rimborso_id)},
        {"$push": {"ricevute": ricevuta}},
    )

    return ricevuta


@router.post("/rimborsi/{rimborso_id}/ricevute-multi")
async def upload_ricevute_multi(rimborso_id: str, request: Request, files: List[UploadFile] = File(...)):
    """Upload multiplo di ricevute generiche al rimborso."""
    user = await get_current_user(request)

    rimborso = await db.rimborsi.find_one({"_id": ObjectId(rimborso_id)})
    if not rimborso:
        raise HTTPException(status_code=404, detail="Rimborso non trovato")

    if rimborso["user_id"] != user["id"] and not user_has_any_role(user, ["admin", "cassiere", "superadmin"]):
        raise HTTPException(status_code=403, detail="Non autorizzato")

    uploaded = []
    for f in files:
        if f.content_type not in ["application/pdf", "image/jpeg", "image/png", "image/jpg"]:
            continue

        content = await f.read()
        if len(content) > 5 * 1024 * 1024:
            continue

        file_id = str(uuid.uuid4())
        ext = f.filename.split(".")[-1] if "." in f.filename else "pdf"
        filename = f"{file_id}.{ext}"
        filepath = UPLOAD_DIR / filename

        async with aiofiles.open(filepath, "wb") as fout:
            await fout.write(content)

        ricevuta = {
            "id": file_id,
            "filename": f.filename,
            "path": filename,
            "content_type": f.content_type,
            "uploaded_at": datetime.now(timezone.utc).isoformat(),
        }
        uploaded.append(ricevuta)

    if uploaded:
        await db.rimborsi.update_one(
            {"_id": ObjectId(rimborso_id)},
            {"$push": {"ricevute": {"$each": uploaded}}},
        )

    return {"uploaded": uploaded, "count": len(uploaded), "skipped": len(files) - len(uploaded)}


@router.get("/rimborsi/{rimborso_id}/ricevute/{file_id}")
async def download_ricevuta(rimborso_id: str, file_id: str, request: Request):
    """Download di una ricevuta specifica (anche per anteprima inline)."""
    user = await get_current_user(request)

    rimborso = await db.rimborsi.find_one({"_id": ObjectId(rimborso_id)})
    if not rimborso:
        raise HTTPException(status_code=404, detail="Rimborso non trovato")

    if rimborso["user_id"] != user["id"]:
        if not user_has_any_role(user, ["admin", "cassiere", "segretario", "superadmin", "superuser"]):
            raise HTTPException(status_code=403, detail="Non autorizzato")
        if not user_has_any_role(user, ["superadmin", "superuser"]) and rimborso.get("sede_id") != user.get("sede_id"):
            raise HTTPException(status_code=403, detail="Non autorizzato per questa sede")

    ricevuta = next(
        (r for r in (rimborso.get("ricevute") or []) + (rimborso.get("ricevute_spese") or []) if r.get("id") == file_id),
        None,
    )
    if not ricevuta:
        raise HTTPException(status_code=404, detail="Ricevuta non trovata")

    filepath = UPLOAD_DIR / ricevuta["path"]
    if not filepath.exists():
        raise HTTPException(status_code=404, detail="File non trovato sul server")

    return FileResponse(filepath, filename=ricevuta.get("filename", "ricevuta"))


@router.delete("/rimborsi/{rimborso_id}/ricevute/{file_id}")
async def delete_ricevuta(rimborso_id: str, file_id: str, request: Request):
    """Elimina una ricevuta. Possibile solo se rimborso ancora 'in_attesa'."""
    user = await get_current_user(request)

    rimborso = await db.rimborsi.find_one({"_id": ObjectId(rimborso_id)})
    if not rimborso:
        raise HTTPException(status_code=404, detail="Rimborso non trovato")

    if rimborso["user_id"] != user["id"] and not user_has_any_role(user, ["admin", "cassiere", "superadmin"]):
        raise HTTPException(status_code=403, detail="Non autorizzato")

    if rimborso.get("stato") not in ["in_attesa", None]:
        raise HTTPException(status_code=400, detail="Impossibile rimuovere ricevute da rimborsi già approvati/pagati")

    ricevuta = next(
        (r for r in (rimborso.get("ricevute") or []) + (rimborso.get("ricevute_spese") or []) if r.get("id") == file_id),
        None,
    )
    if not ricevuta:
        raise HTTPException(status_code=404, detail="Ricevuta non trovata")

    filepath = UPLOAD_DIR / ricevuta["path"]
    if filepath.exists():
        filepath.unlink()

    await db.rimborsi.update_one(
        {"_id": ObjectId(rimborso_id)},
        {"$pull": {
            "ricevute": {"id": file_id},
            "ricevute_spese": {"id": file_id},
        }},
    )

    return {"message": "Ricevuta eliminata"}


@router.post("/rimborsi/{rimborso_id}/ricevute-spese")
async def upload_ricevuta_spesa(rimborso_id: str, request: Request, file: UploadFile = File(...), tipo: str = Form(...), descrizione: str = Form(None)):
    """Upload ricevuta spesa (pasto, altro)."""
    user = await get_current_user(request)

    rimborso = await db.rimborsi.find_one({"_id": ObjectId(rimborso_id)})
    if not rimborso:
        raise HTTPException(status_code=404, detail="Rimborso non trovato")

    if rimborso["user_id"] != user["id"] and not user_has_any_role(user, ["admin", "superadmin"]):
        raise HTTPException(status_code=403, detail="Non autorizzato")

    if file.content_type not in ["application/pdf", "image/jpeg", "image/png", "image/jpg"]:
        raise HTTPException(status_code=400, detail="Formato file non supportato")

    content = await file.read()
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File troppo grande. Max 5MB")

    file_id = str(uuid.uuid4())
    ext = file.filename.split(".")[-1] if "." in file.filename else "pdf"
    filename = f"spesa_{file_id}.{ext}"
    filepath = UPLOAD_DIR / filename

    async with aiofiles.open(filepath, "wb") as f:
        await f.write(content)

    ricevuta_spesa = {
        "id": file_id,
        "filename": file.filename,
        "path": filename,
        "tipo": tipo,
        "descrizione": descrizione,
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
    }

    await db.rimborsi.update_one(
        {"_id": ObjectId(rimborso_id)},
        {"$push": {"ricevute_spese": ricevuta_spesa}},
    )

    return ricevuta_spesa


@router.put("/rimborsi/{rimborso_id}")
async def update_rimborso(rimborso_id: str, rimborso_data: RimborsoUpdate, request: Request):
    user = await get_current_user(request)

    if not user_has_any_role(user, ["admin", "cassiere", "superadmin"]):
        raise HTTPException(status_code=403, detail="Solo admin/cassiere può gestire i rimborsi")

    rimborso = await db.rimborsi.find_one({"_id": ObjectId(rimborso_id)})
    if not rimborso:
        raise HTTPException(status_code=404, detail="Rimborso non trovato")

    if user_has_any_role(user, ["admin", "cassiere"]) and rimborso.get("sede_id") != user.get("sede_id"):
        raise HTTPException(status_code=403, detail="Non autorizzato per questa sede")

    # Lo stato "pagato" può essere impostato SOLO via /contabile
    if rimborso_data.stato == "pagato":
        raise HTTPException(
            status_code=400,
            detail="Per pagare un rimborso devi caricare la contabile tramite l'apposito endpoint /contabile",
        )

    update_data = {k: v for k, v in rimborso_data.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="Nessun dato da aggiornare")

    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()

    await db.rimborsi.update_one({"_id": ObjectId(rimborso_id)}, {"$set": update_data})

    stato_msg = {"approvato": "approvata", "rifiutato": "rifiutata"}
    if rimborso_data.stato and rimborso_data.stato in stato_msg:
        await _notify_user(
            user_id=rimborso["user_id"],
            notifica_data={
                "sede_id": rimborso.get("sede_id"),
                "tipo": "rimborso",
                "titolo": f"Richiesta rimborso {stato_msg[rimborso_data.stato]}",
                "messaggio": f"La tua richiesta di rimborso del {rimborso['data']} è stata {stato_msg[rimborso_data.stato]}",
                "rimborso_id": rimborso_id,
            },
        )
        await _log_audit(
            actor=user,
            action=f"rimborso.{rimborso_data.stato}",
            target_type="rimborso",
            target_id=rimborso_id,
            target_label=f"Rimborso del {rimborso['data']} - €{rimborso.get('importo_totale', 0):.2f}",
            sede_id=rimborso.get("sede_id"),
            old_value=rimborso.get("stato"),
            new_value=rimborso_data.stato,
        )

    return {"message": "Rimborso aggiornato"}


@router.post("/rimborsi/{rimborso_id}/contabile")
async def upload_contabile(rimborso_id: str, request: Request, file: UploadFile = File(...)):
    user = await get_current_user(request)

    if not user_has_any_role(user, ["admin", "cassiere", "superadmin"]):
        raise HTTPException(status_code=403, detail="Solo admin/cassiere può caricare contabili")

    rimborso = await db.rimborsi.find_one({"_id": ObjectId(rimborso_id)})
    if not rimborso:
        raise HTTPException(status_code=404, detail="Rimborso non trovato")

    if user_has_any_role(user, ["admin", "cassiere"]) and rimborso.get("sede_id") != user.get("sede_id"):
        raise HTTPException(status_code=403, detail="Non autorizzato per questa sede")

    if rimborso.get("stato") == "rifiutato":
        raise HTTPException(status_code=400, detail="Impossibile pagare un rimborso rifiutato")

    if rimborso.get("stato") == "pagato":
        raise HTTPException(status_code=400, detail="Rimborso già pagato")

    if file.content_type not in ["application/pdf", "image/jpeg", "image/png", "image/jpg"]:
        raise HTTPException(status_code=400, detail="Formato file non supportato (solo PDF, JPG, PNG)")

    content = await file.read()
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File troppo grande. Max 5MB")

    file_id = str(uuid.uuid4())
    ext = file.filename.split(".")[-1] if "." in file.filename else "pdf"
    filename = f"contabile_{file_id}.{ext}"
    filepath = UPLOAD_DIR / filename

    async with aiofiles.open(filepath, "wb") as f:
        await f.write(content)

    pagamento_diretto = rimborso.get("stato") == "in_attesa"

    await db.rimborsi.update_one(
        {"_id": ObjectId(rimborso_id)},
        {"$set": {
            "stato": "pagato",
            "contabile": {"filename": file.filename, "path": filename},
            "pagato_at": datetime.now(timezone.utc).isoformat(),
            "pagato_by": user["id"],
            "pagato_by_nome": f"{user['nome']} {user['cognome']}",
        }},
    )

    if pagamento_diretto:
        msg_user = f"Il tuo rimborso del {rimborso['data']} è stato approvato e pagato. Contabile disponibile."
        titolo_user = "Rimborso approvato e pagato"
    else:
        msg_user = f"Il tuo rimborso del {rimborso['data']} è stato pagato. Contabile disponibile."
        titolo_user = "Rimborso pagato"

    await _notify_user(
        user_id=rimborso["user_id"],
        notifica_data={
            "sede_id": rimborso.get("sede_id"),
            "tipo": "rimborso",
            "titolo": titolo_user,
            "messaggio": msg_user,
            "rimborso_id": rimborso_id,
        },
    )

    # Notifica anche Admin + Cassiere della sede (escluso chi ha appena pagato)
    notifiche_admin = []
    async for u in db.users.find(
        {"ruoli": {"$in": ["admin", "cassiere"]}, "sede_id": rimborso.get("sede_id"), "_id": {"$ne": ObjectId(user["id"])}},
        {"_id": 1},
    ):
        notifiche_admin.append({
            "user_id": str(u["_id"]),
            "sede_id": rimborso.get("sede_id"),
            "tipo": "rimborso",
            "titolo": "Rimborso pagato",
            "messaggio": f"{user['nome']} {user['cognome']} ha pagato il rimborso del {rimborso['data']}",
            "rimborso_id": rimborso_id,
            "letto": False,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
    if notifiche_admin:
        await db.notifiche.insert_many(notifiche_admin)

    await _log_audit(
        actor=user,
        action="rimborso.pay_direct" if pagamento_diretto else "rimborso.pay",
        target_type="rimborso",
        target_id=rimborso_id,
        target_label=f"Rimborso del {rimborso['data']} - €{rimborso.get('importo_totale', 0):.2f}",
        sede_id=rimborso.get("sede_id"),
        old_value=rimborso.get("stato"),
        new_value="pagato",
        note=f"Contabile caricata: {file.filename}",
    )

    return {"message": "Contabile caricata e rimborso pagato"}
