"""
routes/maps.py
Integrazione Google Maps (Directions API) per calcolo km.
"""
import math

import httpx
from fastapi import APIRouter, HTTPException, Request

from core.auth import get_current_user
from core.config import GOOGLE_MAPS_API_KEY
from models_api import CalcoloKmRequest

router = APIRouter()


@router.post("/calcola-km")
async def calcola_km(data: CalcoloKmRequest, request: Request):
    await get_current_user(request)

    if not GOOGLE_MAPS_API_KEY:
        raise HTTPException(status_code=500, detail="Google Maps API non configurata")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://maps.googleapis.com/maps/api/directions/json",
                params={
                    "origin": data.origine,
                    "destination": data.destinazione,
                    "key": GOOGLE_MAPS_API_KEY,
                    "language": "it",
                },
            )
            result = response.json()

            if result.get("status") != "OK":
                raise HTTPException(status_code=400, detail=f"Impossibile calcolare il percorso: {result.get('status')}")

            distance_meters = result["routes"][0]["legs"][0]["distance"]["value"]
            distance_km = math.ceil(distance_meters / 1000)

            return {
                "km": distance_km,
                "origine": result["routes"][0]["legs"][0]["start_address"],
                "destinazione": result["routes"][0]["legs"][0]["end_address"],
                "durata": result["routes"][0]["legs"][0]["duration"]["text"],
            }
    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail=f"Errore di connessione: {str(e)}")
