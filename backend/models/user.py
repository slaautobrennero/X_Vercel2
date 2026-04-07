"""
User Models - Modelli per gestione utenti

Ruoli disponibili:
- superadmin: Accesso completo a tutte le sedi
- superuser: Visualizzazione di tutte le sedi (sola lettura)
- admin: Gestione completa della propria sede
- segretario: Gestione sede + può coincidere con admin
- segreteria: Carica documenti, gestisce bacheca
- delegato: Richiede rimborsi, vede documenti
- iscritto: Solo bacheca e documenti (no rimborsi)
"""

from pydantic import BaseModel, EmailStr
from typing import Optional


class UserBase(BaseModel):
    """Campi base condivisi tra creazione e risposta"""
    email: EmailStr
    nome: str
    cognome: str
    telefono: Optional[str] = None
    indirizzo: Optional[str] = None  # Obbligatorio per delegato+
    citta: Optional[str] = None
    cap: Optional[str] = None
    iban: Optional[str] = None  # Obbligatorio per delegato+


class UserCreate(UserBase):
    """Dati richiesti per registrazione"""
    password: str
    sede_id: Optional[str] = None  # Riferimento alla concessionaria
    ruolo: str = "iscritto"  # Default: iscritto


class UserUpdate(BaseModel):
    """Campi aggiornabili dall'utente o admin"""
    nome: Optional[str] = None
    cognome: Optional[str] = None
    telefono: Optional[str] = None
    indirizzo: Optional[str] = None
    citta: Optional[str] = None
    cap: Optional[str] = None
    iban: Optional[str] = None


class UserResponse(BaseModel):
    """Risposta API con dati utente (senza password)"""
    id: str
    email: str
    nome: str
    cognome: str
    telefono: Optional[str] = None
    indirizzo: Optional[str] = None
    citta: Optional[str] = None
    cap: Optional[str] = None
    iban: Optional[str] = None
    ruolo: str
    sede_id: Optional[str] = None
    sede_nome: Optional[str] = None
    created_at: str


class LoginRequest(BaseModel):
    """Dati per login"""
    email: EmailStr
    password: str
