"""
Database - Connessione MongoDB

Utilizza Motor per connessione asincrona.
La connessione viene condivisa tra tutte le route.

Collezioni:
- users: Utenti registrati
- sedi: Concessionarie autostradali
- rimborsi: Richieste di rimborso
- motivi_rimborso: Causali per rimborsi
- annunci: Annunci in bacheca
- documenti: Documenti/modulistica caricati
- notifiche: Notifiche per utenti
- login_attempts: Traccia tentativi login falliti (brute force protection)
"""

from motor.motor_asyncio import AsyncIOMotorClient
from .config import settings

# Connessione MongoDB (singleton)
client = AsyncIOMotorClient(settings.MONGO_URL)
db = client[settings.DB_NAME]

# Export collezioni per accesso diretto
users = db.users
sedi = db.sedi
rimborsi = db.rimborsi
motivi_rimborso = db.motivi_rimborso
annunci = db.annunci
documenti = db.documenti
notifiche = db.notifiche
login_attempts = db.login_attempts
