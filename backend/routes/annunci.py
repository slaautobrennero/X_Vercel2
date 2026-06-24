"""
routes/annunci.py
Bacheca/comunicati: CRUD + download allegati.
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


@router.get("/annunci")
async def get_annunci(request: Request):
    user = await get_current_user(request)

    query = {}
    if not user_has_any_role(user, ["superadmin", "superuser"]):
        query["$or"] = [
            {"sede_id": user.get("sede_id")},
            {"sede_id": None},
        ]

    annunci = []
    async for annuncio in db.annunci.find(query).sort("created_at", -1).limit(50):
        annuncio["id"] = str(annuncio["_id"])
        annuncio.pop("_id")
        annunci.append(annuncio)

    return annunci


@router.post("/annunci")
async def create_annuncio(
    request: Request,
    titolo: str = Form(...),
    contenuto: str = Form(...),
    link_documento: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
):
    user = await get_current_user(request)

    if not user_has_any_role(user, ["segreteria", "segretario", "admin", "superadmin"]):
        raise HTTPException(status_code=403, detail="Permessi insufficienti")

    allegato_filename = None
    allegato_path = None

    if file and file.filename:
        if file.content_type not in ["application/pdf", "image/jpeg", "image/png", "image/jpg"]:
            raise HTTPException(status_code=400, detail="Formato file non supportato (solo PDF, JPG, PNG)")

        content = await file.read()
        if len(content) > 5 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File troppo grande. Max 5MB")

        file_id = str(uuid.uuid4())
        ext = file.filename.split(".")[-1] if "." in file.filename else "pdf"
        stored_name = f"annuncio_{file_id}.{ext}"
        filepath = UPLOAD_DIR / stored_name

        async with aiofiles.open(filepath, "wb") as f:
            await f.write(content)

        allegato_filename = file.filename
        allegato_path = stored_name

    annuncio_doc = {
        "titolo": titolo,
        "contenuto": contenuto,
        "link_documento": link_documento if link_documento else None,
        "allegato_filename": allegato_filename,
        "allegato_path": allegato_path,
        "sede_id": user.get("sede_id") if not user_has_role(user, "superadmin") else None,
        "autore_id": user["id"],
        "autore_nome": f"{user['nome']} {user['cognome']}",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    result = await db.annunci.insert_one(annuncio_doc)
    annuncio_doc["id"] = str(result.inserted_id)
    annuncio_doc.pop("_id", None)

    await _notify_all_in_sede(
        sede_id=annuncio_doc["sede_id"],
        notifica_data={
            "sede_id": annuncio_doc["sede_id"],
            "tipo": "annuncio",
            "titolo": "Nuovo comunicato in bacheca",
            "messaggio": f"{annuncio_doc['autore_nome']}: {titolo}",
            "annuncio_id": annuncio_doc["id"],
        },
        exclude_user_id=user["id"],
    )

    return annuncio_doc


@router.get("/annunci/{annuncio_id}/download")
async def download_allegato_annuncio(annuncio_id: str, request: Request):
    user = await get_current_user(request)

    annuncio = await db.annunci.find_one({"_id": ObjectId(annuncio_id)})
    if not annuncio:
        raise HTTPException(status_code=404, detail="Annuncio non trovato")

    if not annuncio.get("allegato_path"):
        raise HTTPException(status_code=404, detail="Nessun allegato per questo annuncio")

    if not user_has_any_role(user, ["superadmin", "superuser"]):
        if annuncio.get("sede_id") and annuncio["sede_id"] != user.get("sede_id"):
            raise HTTPException(status_code=403, detail="Non autorizzato")

    filepath = UPLOAD_DIR / annuncio["allegato_path"]
    if not filepath.exists():
        raise HTTPException(status_code=404, detail="File non trovato")

    return FileResponse(filepath, filename=annuncio.get("allegato_filename", "allegato"))


@router.delete("/annunci/{annuncio_id}")
async def delete_annuncio(annuncio_id: str, request: Request):
    user = await get_current_user(request)

    if not user_has_any_role(user, ["segreteria", "segretario", "admin", "superadmin"]):
        raise HTTPException(status_code=403, detail="Permessi insufficienti")

    annuncio = await db.annunci.find_one({"_id": ObjectId(annuncio_id)})
    if not annuncio:
        raise HTTPException(status_code=404, detail="Annuncio non trovato")

    if annuncio.get("allegato_path"):
        filepath = UPLOAD_DIR / annuncio["allegato_path"]
        if filepath.exists():
            filepath.unlink()

    await db.annunci.delete_one({"_id": ObjectId(annuncio_id)})

    return {"message": "Annuncio eliminato"}
