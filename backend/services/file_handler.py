"""
File Handler Service - Gestione file

Gestisce upload e eliminazione file per:
- Documenti/modulistica
- Ricevute rimborso
- Contabili bonifico

Formati supportati: PDF, JPG, JPEG, PNG
Dimensione massima: 5MB

I file sono salvati in /uploads con UUID univoco.
"""

import uuid
import aiofiles
from pathlib import Path
from fastapi import UploadFile, HTTPException
from ..utils.config import settings


async def save_upload_file(
    file: UploadFile, 
    prefix: str = ""
) -> tuple[str, str]:
    """
    Salva file uploadato su disco.
    
    Args:
        file: File da UploadFile di FastAPI
        prefix: Prefisso per il nome file (es. "doc_", "ricevuta_")
    
    Returns:
        tuple: (file_id, filename)
        - file_id: UUID univoco
        - filename: Nome file salvato
    
    Raises:
        HTTPException: Se formato non supportato o file troppo grande
    """
    # Valida content type
    allowed_types = [
        "application/pdf", 
        "image/jpeg", 
        "image/png", 
        "image/jpg"
    ]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400, 
            detail="Formato file non supportato. Usa PDF, JPG o PNG."
        )
    
    # Leggi contenuto
    content = await file.read()
    
    # Valida dimensione
    if len(content) > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400, 
            detail=f"File troppo grande. Massimo {settings.MAX_FILE_SIZE // (1024*1024)}MB."
        )
    
    # Genera nome univoco
    file_id = str(uuid.uuid4())
    ext = file.filename.split(".")[-1] if "." in file.filename else "pdf"
    filename = f"{prefix}{file_id}.{ext}"
    filepath = settings.UPLOAD_DIR / filename
    
    # Salva su disco
    async with aiofiles.open(filepath, "wb") as f:
        await f.write(content)
    
    return file_id, filename


def delete_file(filename: str) -> bool:
    """
    Elimina file da disco.
    
    Args:
        filename: Nome del file da eliminare
    
    Returns:
        True se eliminato, False se non esisteva
    """
    filepath = settings.UPLOAD_DIR / filename
    if filepath.exists():
        filepath.unlink()
        return True
    return False
