"""
Models Package - Definizioni Pydantic per validazione dati

Questo package contiene tutti i modelli Pydantic usati per:
- Validazione input delle API
- Serializzazione response
- Documentazione automatica OpenAPI/Swagger
"""

from .user import (
    UserBase, UserCreate, UserUpdate, UserResponse, LoginRequest
)
from .sede import SedeCreate, SedeUpdate
from .rimborso import (
    RimborsoCreate, RimborsoUpdate, CalcoloKmRequest, 
    MotivoRimborsoCreate, MotivoRimborsoUpdate
)
from .documento import AnnuncioCreate, DocumentoCreate

__all__ = [
    'UserBase', 'UserCreate', 'UserUpdate', 'UserResponse', 'LoginRequest',
    'SedeCreate', 'SedeUpdate',
    'RimborsoCreate', 'RimborsoUpdate', 'CalcoloKmRequest',
    'MotivoRimborsoCreate', 'MotivoRimborsoUpdate',
    'AnnuncioCreate', 'DocumentoCreate'
]
