"""
routes/documenti.py
Modulistica/documenti condivisi: upload, list, download, delete.
"""
import uuid
from datetime import datetime, timezone
from typing import Optional

import aiofiles
from bson import ObjectId
from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse

from core.auth import get_current_user
from core.config import UPLOAD_DIR
from core.db import db
from core.notifications import _notify_all_in_sede
from core.roles import user_has_any_role, user_has_role

router = APIRouter()


@router.get("/documenti")
async def get_documenti(request: Request, categoria: Optional[str] = None):
    user = await get_current_user(request)

    query = {}
    if not user_has_any_role(user, ["superadmin", "superuser"]):
        query["$or"] = [
            {"sede_id": user.get("sede_id")},
            {"sede_id": None},
        ]

    if categoria:
        query["categoria"] = categoria

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
    categoria: str = Form(...),
    descrizione: str = Form(None),
):
    user = await get_current_user(request)

    if not user_has_any_role(user, ["segreteria", "segretario", "admin", "superadmin"]):
        raise HTTPException(status_code=403, detail="Permessi insufficienti")

    if file.content_type not in ["application/pdf", "image/jpeg", "image/png", "image/jpg"]:
        raise HTTPException(status_code=400, detail="Formato file non supportato")

    content = await file.read()
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File troppo grande. Max 5MB")

    file_id = str(uuid.uuid4())
    ext = file.filename.split(".")[-1] if "." in file.filename else "pdf"
    filename = f"doc_{file_id}.{ext}"
    filepath = UPLOAD_DIR / filename

    async with aiofiles.open(filepath, "wb") as f:
        await f.write(content)

    doc_record = {
        "nome": nome,
        "categoria": categoria,
        "descrizione": descrizione,
        "filename": file.filename,
        "path": filename,
        "sede_id": user.get("sede_id") if not user_has_role(user, "superadmin") else None,
        "uploaded_by": user["id"],
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    result = await db.documenti.insert_one(doc_record)
    doc_record["id"] = str(result.inserted_id)
    doc_record.pop("_id", None)

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

    if not user_has_any_role(user, ["superadmin", "superuser"]):
        if doc.get("sede_id") and doc["sede_id"] != user.get("sede_id"):
            raise HTTPException(status_code=403, detail="Non autorizzato")

    filepath = UPLOAD_DIR / doc["path"]
    if not filepath.exists():
        raise HTTPException(status_code=404, detail="File non trovato")

    return FileResponse(filepath, filename=doc["filename"])


@router.delete("/documenti/{doc_id}")
async def delete_documento(doc_id: str, request: Request):
    user = await get_current_user(request)

    if not user_has_any_role(user, ["segreteria", "segretario", "admin", "superadmin"]):
        raise HTTPException(status_code=403, detail="Permessi insufficienti")

    doc = await db.documenti.find_one({"_id": ObjectId(doc_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Documento non trovato")

    filepath = UPLOAD_DIR / doc["path"]
    if filepath.exists():
        filepath.unlink()

    await db.documenti.delete_one({"_id": ObjectId(doc_id)})

    return {"message": "Documento eliminato"}
