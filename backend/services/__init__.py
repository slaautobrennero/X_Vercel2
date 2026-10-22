"""
Services Package - Logica di business

Contiene la logica separata dalle route:
- google_maps.py: Integrazione Google Maps API
- notifications.py: Creazione notifiche

I service sono funzioni pure che possono essere testate facilmente.
"""

from .google_maps import calcola_distanza_km
from .notifications import create_notification

__all__ = [
    'calcola_distanza_km',
    'create_notification'
]
