"""Archivio allegati: copia durevole in MongoDB GridFS + cache su disco locale."""
from pathlib import Path
from typing import Optional

import aiofiles
from fastapi import HTTPException
from gridfs.errors import NoFile
from motor.motor_asyncio import AsyncIOMotorGridFSBucket

from .config import UPLOAD_DIR, logger
from .db import db


class BlobStore:
    def __init__(self):
        self.bucket = AsyncIOMotorGridFSBucket(db, bucket_name="allegati")

    async def put_binary(self, key: str, data: bytes) -> None:
        await self.bucket.upload_from_stream(key, data)

    async def get_binary(self, key: str) -> Optional[bytes]:
        try:
            stream = await self.bucket.open_download_stream_by_name(key)
        except NoFile:
            return None
        return await stream.read()

    async def exists(self, key: str) -> bool:
        return await db["allegati.files"].find_one({"filename": key}, {"_id": 1}) is not None

    async def delete(self, key: str) -> None:
        async for f in self.bucket.find({"filename": key}):
            await self.bucket.delete(f._id)


blob_store = BlobStore()

_FIRME = ((b"%PDF-", "pdf"), (b"\x89PNG\r\n\x1a\n", "png"), (b"\xff\xd8\xff", "jpg"))


def detect_ext(content: bytes) -> Optional[str]:
    """Estensione dal contenuto reale del file (PDF/PNG/JPG), None se non ammesso."""
    for firma, ext in _FIRME:
        if content.startswith(firma):
            return ext
    return None


def require_ext(content: bytes) -> str:
    ext = detect_ext(content)
    if not ext:
        raise HTTPException(status_code=400, detail="Il contenuto del file non è un PDF, JPG o PNG valido")
    return ext


async def save_upload(filename: str, content: bytes) -> None:
    async with aiofiles.open(UPLOAD_DIR / filename, "wb") as f:
        await f.write(content)
    await blob_store.put_binary(filename, content)


async def get_local_path(filename: str) -> Optional[Path]:
    """Ritorna il path su disco; se manca lo ripristina da GridFS."""
    if not filename or Path(filename).name != filename:
        return None
    path = UPLOAD_DIR / filename
    if path.exists():
        return path
    blob = await blob_store.get_binary(filename)
    if blob is None:
        return None
    async with aiofiles.open(path, "wb") as f:
        await f.write(blob)
    return path


async def delete_upload(filename: str) -> None:
    path = UPLOAD_DIR / filename
    if path.exists():
        path.unlink()
    await blob_store.delete(filename)


async def sync_local_to_gridfs() -> None:
    """Copia in GridFS i file locali preesistenti (migrazione una tantum)."""
    copied = 0
    for path in UPLOAD_DIR.iterdir():
        if path.is_file() and not await blob_store.exists(path.name):
            async with aiofiles.open(path, "rb") as f:
                await blob_store.put_binary(path.name, await f.read())
            copied += 1
    if copied:
        logger.info(f"Storage: {copied} allegati locali copiati in GridFS")
