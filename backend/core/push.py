"""Notifiche push Web (gratuite, VAPID self-hosted)."""
import asyncio
import base64
import json
import os
from datetime import datetime, timezone

from cryptography.hazmat.primitives import serialization
from py_vapid import Vapid01
from pywebpush import WebPushException, webpush

from .config import FRONTEND_URL, logger
from .db import db

_TASKS: set = set()
_VAPID: dict = {}


def _b64(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode()


async def get_vapid() -> dict:
    """Chiavi VAPID da .env, altrimenti generate una volta e salvate nel database."""
    if _VAPID:
        return _VAPID
    if os.environ.get("VAPID_PUBLIC_KEY") and os.environ.get("VAPID_PRIVATE_KEY"):
        _VAPID.update(public=os.environ["VAPID_PUBLIC_KEY"], private=os.environ["VAPID_PRIVATE_KEY"])
        return _VAPID
    doc = await db.impostazioni.find_one({"_id": "vapid"})
    if not doc:
        v = Vapid01()
        v.generate_keys()
        pub = v.public_key.public_bytes(serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint)
        priv = v.private_key.private_numbers().private_value.to_bytes(32, "big")
        doc = {"_id": "vapid", "public": _b64(pub), "private": _b64(priv), "created_at": datetime.now(timezone.utc).isoformat()}
        await db.impostazioni.insert_one(doc)
        logger.info("Chiavi VAPID per le notifiche push generate")
    _VAPID.update(public=doc["public"], private=doc["private"])
    return _VAPID


def _send_one(sub: dict, payload: str, private_key: str) -> int:
    try:
        webpush(
            subscription_info={"endpoint": sub["endpoint"], "keys": sub["keys"]},
            data=payload,
            vapid_private_key=private_key,
            vapid_claims={"sub": f"mailto:noreply@{(FRONTEND_URL.split('//')[-1].split('/')[0] or 'localhost')}"},
            ttl=86400,
        )
        return 201
    except WebPushException as e:
        return e.response.status_code if e.response is not None else 0


async def _push_users(user_ids: list, titolo: str, messaggio: str, url: str) -> None:
    try:
        vapid = await get_vapid()
        payload = json.dumps({"title": titolo, "body": messaggio, "url": url})
        async for sub in db.push_subscriptions.find({"user_id": {"$in": user_ids}}):
            status = await asyncio.to_thread(_send_one, sub, payload, vapid["private"])
            if status in (404, 410):
                await db.push_subscriptions.delete_one({"_id": sub["_id"]})
    except Exception as e:
        logger.error(f"Errore invio push: {e}")


def invia_push(user_ids: list, notifica: dict) -> None:
    """Invio in background, non blocca la richiesta."""
    if not user_ids:
        return
    url = notifica.get("link") or ("/rimborsi" if notifica.get("tipo") == "rimborso" else "/bacheca" if notifica.get("tipo") == "annuncio" else "/notifiche")
    task = asyncio.create_task(_push_users(user_ids, notifica.get("titolo", "Portale SLA"), notifica.get("messaggio", ""), url))
    _TASKS.add(task)
    task.add_done_callback(_TASKS.discard)
