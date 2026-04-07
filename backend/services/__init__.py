"""
Services Package - Logica di business

Contiene la logica separata dalle route:
- google_maps.py: Integrazione Google Maps API
- file_handler.py: Gestione upload/download file
- notifications.py: Creazione notifiche

I service sono funzioni pure che possono essere testate facilmente.
"""

from .google_maps import calcola_distanza_km
from .file_handler import save_upload_file, delete_file
from .notifications import create_notification

__all__ = [
    'calcola_distanza_km',
    'save_upload_file', 'delete_file',
    'create_notification'
]
