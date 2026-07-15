"""
Configurazione globale del backend.
Carica variabili d'ambiente, imposta logger, costanti.
"""
from dotenv import load_dotenv
from pathlib import Path
import os
import logging

# Carica .env all'avvio SENZA sovrascrivere variabili già settate (docker-compose)
# In produzione: le env vars vengono da docker-compose environment; il .env locale
# è ignorato dal container (.dockerignore) ma resta utile in dev locale.
ROOT_DIR = Path(__file__).parent.parent
load_dotenv(ROOT_DIR / '.env', override=False)

# MongoDB
MONGO_URL = os.environ['MONGO_URL']
DB_NAME = os.environ['DB_NAME']

# JWT
JWT_SECRET = os.environ['JWT_SECRET']
JWT_ALGORITHM = "HS256"

# Google Maps API (opzionale)
GOOGLE_MAPS_API_KEY = os.environ.get('GOOGLE_MAPS_API_KEY', '')

# Upload directory (persistent volume nel container)
UPLOAD_DIR = Path(os.environ.get("UPLOAD_DIR", "/app/uploads"))
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Limite dimensione file upload
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

# CORS origin regex (configurabile via env)
FRONTEND_ORIGIN_REGEX = os.environ.get(
    "FRONTEND_ORIGIN_REGEX",
    r"https?://(www\.)?(portale-sla\.it|localhost(:\d+)?|192\.168\.\d+\.\d+(:\d+)?)"
)

# Logger condiviso
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("sla")
