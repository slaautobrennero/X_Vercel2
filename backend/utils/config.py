"""
Config - Configurazione centralizzata

Tutte le variabili di ambiente sono caricate qui.
Modifica il file .env per configurare l'applicazione.

Variabili richieste:
- MONGO_URL: URL di connessione MongoDB
- DB_NAME: Nome del database
- JWT_SECRET: Chiave segreta per JWT (genera una casuale!)
- ADMIN_EMAIL: Email del superadmin iniziale
- ADMIN_PASSWORD: Password del superadmin iniziale
- GOOGLE_MAPS_API_KEY: (opzionale) Per calcolo KM automatico
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Carica variabili da .env
ROOT_DIR = Path(__file__).parent.parent
load_dotenv(ROOT_DIR / '.env')


class Settings:
    """Configurazione applicazione"""
    
    # Database
    MONGO_URL: str = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    DB_NAME: str = os.environ.get('DB_NAME', 'sla_sindacato')
    
    # JWT
    JWT_SECRET: str = os.environ.get('JWT_SECRET', 'CAMBIA-QUESTA-CHIAVE-IN-PRODUZIONE')
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_HOURS: int = 24
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Admin iniziale
    ADMIN_EMAIL: str = os.environ.get('ADMIN_EMAIL', 'superadmin@sla.it')
    ADMIN_PASSWORD: str = os.environ.get('ADMIN_PASSWORD', 'CambiaQuestaPassword!')
    
    # Google Maps (opzionale)
    GOOGLE_MAPS_API_KEY: str = os.environ.get('GOOGLE_MAPS_API_KEY', '')
    
    # Frontend URL (per CORS)
    FRONTEND_URL: str = os.environ.get('FRONTEND_URL', 'http://localhost:3000')
    
    # Upload
    UPLOAD_DIR: Path = ROOT_DIR / "uploads"
    MAX_FILE_SIZE: int = 5 * 1024 * 1024  # 5MB
    ALLOWED_EXTENSIONS: list = ['pdf', 'jpg', 'jpeg', 'png']


settings = Settings()

# Crea directory upload se non esiste
settings.UPLOAD_DIR.mkdir(exist_ok=True)
