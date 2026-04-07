"""
Google Maps Service - Calcolo distanze

Utilizza Google Directions API per calcolare:
- Distanza in KM tra due indirizzi
- Tempo di percorrenza stimato

Richiede GOOGLE_MAPS_API_KEY configurata.
Abilitare "Directions API" nella Google Cloud Console.

Costi: ~$5 per 1000 richieste (primi $200/mese gratis)
"""

import httpx
import math
from fastapi import HTTPException
from ..utils.config import settings


async def calcola_distanza_km(origine: str, destinazione: str) -> dict:
    """
    Calcola distanza tra due indirizzi usando Google Maps.
    
    Args:
        origine: Indirizzo completo di partenza
        destinazione: Indirizzo completo di arrivo
    
    Returns:
        dict con:
        - km: Distanza in KM (arrotondata per eccesso)
        - origine: Indirizzo normalizzato da Google
        - destinazione: Indirizzo normalizzato da Google  
        - durata: Tempo stimato (es. "2 ore 30 min")
    
    Raises:
        HTTPException: Se API non configurata o errore Google
    """
    if not settings.GOOGLE_MAPS_API_KEY:
        raise HTTPException(
            status_code=500, 
            detail="Google Maps API non configurata. Inserisci i KM manualmente."
        )
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://maps.googleapis.com/maps/api/directions/json",
                params={
                    "origin": origine,
                    "destination": destinazione,
                    "key": settings.GOOGLE_MAPS_API_KEY,
                    "language": "it"
                },
                timeout=10.0
            )
            result = response.json()
            
            # Controlla errori API
            if result.get("status") != "OK":
                error_msg = result.get("error_message", result.get("status"))
                raise HTTPException(
                    status_code=400, 
                    detail=f"Impossibile calcolare il percorso: {error_msg}"
                )
            
            # Estrai dati dal primo percorso
            leg = result["routes"][0]["legs"][0]
            
            # Converti metri in KM, arrotonda per eccesso
            distance_meters = leg["distance"]["value"]
            distance_km = math.ceil(distance_meters / 1000)
            
            return {
                "km": distance_km,
                "origine": leg["start_address"],
                "destinazione": leg["end_address"],
                "durata": leg["duration"]["text"]
            }
            
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Errore di connessione a Google Maps: {str(e)}"
        )
