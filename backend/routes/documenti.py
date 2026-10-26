"""
routes/documenti.py
Modulistica/documenti condivisi: upload, list, download, delete.
"""
import uuid
from datetime import datetime, timezone
from typing import Optional

from bson import ObjectId
from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse

from core.auth import get_current_user
from core.db import db
from core.storage import delete_upload, get_local_path, require_ext, save_upload
from core.notifications import _notify_all_in_sede
from core.roles import (
    is_sede_nazionale_member,
    user_has_any_role,
)

from routes.cartelle import cartelle_nascoste_per, get_cartella, puo_caricare, puo_vedere

router = APIRouter()


@router.get("/documenti")
async def get_documenti(request: Request, categoria: Optional[str] = None, cartella_id: Optional[str] = None):
    user = await get_current_user(request)

    # v0.14.0: admin/segretario del Nazionale vedono TUTTI i documenti (di tutte le sedi)
    is_naz_reader = await is_sede_nazionale_member(user, roles=["admin", "segretario"])

    query = {}
    if not user_has_any_role(user, ["superadmin", "superuser"]) and not is_naz_reader:
        query["$or"] = [
            {"sede_id": user.get("sede_id")},
            {"sede_id": None},
        ]

    if categoria:
        query["categoria"] = categoria
    nascoste = await cartelle_nascoste_per(user)
    if cartella_id:
        if cartella_id in nascoste:
            raise HTTPException(status_code=403, detail="Cartella riservata")
        query["cartella_id"] = cartella_id
    elif nascoste:
        query["cartella_id"] = {"$nin": nascoste}

    documenti = []
    async for doc in db.documenti.find(query).sort("created_at", -1):
        doc["id"] = str(doc["_id"])
        doc.pop("_id")
        documenti.append(doc)

    return documenti


@router.post("/documenti")
async def upload_documento(
    request: Request,
    file: UploadFile = File(...),
    nome: str = Form(...),
    cartella_id: str = Form(...),
    descrizione: str = Form(None),
):
    user = await get_current_user(request)

    cartella = await get_cartella(cartella_id)
    if not await puo_caricare(user, cartella):
        raise HTTPException(status_code=403, detail="Non puoi caricare documenti in questa cartella")

    if file.content_type not in ["application/pdf", "image/jpeg", "image/png", "image/jpg"]:
        raise HTTPException(status_code=400, detail="Formato file non supportato")

    content = await file.read()
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File troppo grande. Max 5MB")

    file_id = str(uuid.uuid4())
    ext = require_ext(content)
    filename = f"doc_{file_id}.{ext}"
    await save_upload(filename, content)

    # Il documento eredita l'ambito della cartella (sede_id None = tutte le concessionarie)
    target_sede_id = cartella.get("sede_id")
    broadcast_nazionale = target_sede_id is None

    doc_record = {
        "nome": nome,
        "cartella_id": cartella_id,
        "categoria": cartella["nome"],
        "descrizione": descrizione,
        "filename": file.filename,
        "path": filename,
        "sede_id": target_sede_id,
        "broadcast_nazionale": broadcast_nazionale,
        "uploaded_by": user["id"],
        "autore_sede_id": user.get("sede_id"),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    result = await db.documenti.insert_one(doc_record)
    doc_record["id"] = str(result.inserted_id)
    doc_record.pop("_id", None)

    if cartella.get("visibile", True):
        await _notify_all_in_sede(
            sede_id=doc_record["sede_id"],
            notifica_data={
                "sede_id": doc_record["sede_id"],
                "tipo": "documento",
                "titolo": "Nuovo documento disponibile",
                "messaggio": f"{user['nome']} {user['cognome']} ha caricato: {nome}",
                "documento_id": doc_record["id"],
            },
            exclude_user_id=user["id"],
        )

    return doc_record


@router.get("/documenti/{doc_id}/download")
async def download_documento(doc_id: str, request: Request):
    user = await get_current_user(request)

    doc = await db.documenti.find_one({"_id": ObjectId(doc_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Documento non trovato")

    # v0.14.0: admin/segretario del Nazionale possono scaricare tutti i documenti
    is_naz_reader = await is_sede_nazionale_member(user, roles=["admin", "segretario"])
    if not user_has_any_role(user, ["superadmin", "superuser"]) and not is_naz_reader:
        if doc.get("sede_id") and doc["sede_id"] != user.get("sede_id"):
            raise HTTPException(status_code=403, detail="Non autorizzato")

    if doc.get("cartella_id") and not await puo_vedere(user, await get_cartella(doc["cartella_id"])):
        raise HTTPException(status_code=403, detail="Cartella riservata")

    filepath = await get_local_path(doc["path"])
    if not filepath:
        raise HTTPException(status_code=404, detail="File non trovato")

    return FileResponse(filepath, filename=doc["filename"])


@router.delete("/documenti/{doc_id}")
async def delete_documento(doc_id: str, request: Request):
    user = await get_current_user(request)

    doc = await db.documenti.find_one({"_id": ObjectId(doc_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Documento non trovato")
    cartella = await db.cartelle.find_one({"_id": ObjectId(doc["cartella_id"])}) if doc.get("cartella_id") else {"sede_id": doc.get("sede_id")}
    if not await puo_caricare(user, cartella or {"sede_id": doc.get("sede_id")}):
        raise HTTPException(status_code=403, detail="Non puoi eliminare questo documento")

    await delete_upload(doc["path"])

    await db.documenti.delete_one({"_id": ObjectId(doc_id)})

    return {"message": "Documento eliminato"}
