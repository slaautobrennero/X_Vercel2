"""
Utils Package - Funzioni di utilità

Contiene:
- auth.py: Gestione JWT, password hashing, autenticazione
- database.py: Connessione MongoDB
- config.py: Configurazione da variabili ambiente
"""

from .config import settings
from .database import db, client
from .auth import (
    hash_password, verify_password,
    create_access_token, create_refresh_token,
    get_current_user
)

__all__ = [
    'settings', 'db', 'client',
    'hash_password', 'verify_password',
    'create_access_token', 'create_refresh_token',
    'get_current_user'
]
