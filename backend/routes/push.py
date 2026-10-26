"""Iscrizione dei dispositivi alle notifiche push."""
from datetime import datetime, timezone

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from core.auth import get_current_user
from core.db import db
from core.push import get_vapid

router = APIRouter()


class PushKeys(BaseModel):
    p256dh: str = Field(max_length=200)
    auth: str = Field(max_length=100)


class PushSubscription(BaseModel):
    endpoint: str = Field(max_length=1000, pattern=r"^https://")
    keys: PushKeys


class PushUnsubscribe(BaseModel):
    endpoint: str


@router.get("/push/public-key")
async def push_public_key():
    return {"public_key": (await get_vapid())["public"]}


@router.post("/push/subscribe")
async def push_subscribe(sub: PushSubscription, request: Request):
    user = await get_current_user(request)
    await db.push_subscriptions.update_one(
        {"endpoint": sub.endpoint},
        {"$set": {"user_id": user["id"], "keys": sub.keys.model_dump(), "updated_at": datetime.now(timezone.utc).isoformat()}},
        upsert=True,
    )
    return {"message": "Notifiche attivate su questo dispositivo"}


@router.post("/push/unsubscribe")
async def push_unsubscribe(data: PushUnsubscribe, request: Request):
    user = await get_current_user(request)
    await db.push_subscriptions.delete_many({"endpoint": data.endpoint, "user_id": user["id"]})
    return {"message": "Notifiche disattivate su questo dispositivo"}
