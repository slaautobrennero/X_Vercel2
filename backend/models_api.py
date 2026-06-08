"""
Pydantic models per validazione I/O API.
"""
from typing import List, Optional
from pydantic import BaseModel, EmailStr


# --- USER ---

class UserBase(BaseModel):
    email: EmailStr
    nome: str
    cognome: str
    telefono: Optional[str] = None
    indirizzo: Optional[str] = None
    citta: Optional[str] = None
    cap: Optional[str] = None
    iban: Optional[str] = None


class UserCreate(UserBase):
    password: str
    sede_id: Optional[str] = None
    ruolo: str = "iscritto"
    ruoli: Optional[List[str]] = None


class UserUpdate(BaseModel):
    nome: Optional[str] = None
    cognome: Optional[str] = None
    telefono: Optional[str] = None
    indirizzo: Optional[str] = None
    citta: Optional[str] = None
    cap: Optional[str] = None
    iban: Optional[str] = None


class UserResponse(BaseModel):
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
    ruoli: List[str] = []
    sede_id: Optional[str] = None
    sede_nome: Optional[str] = None
    created_at: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class ToggleDisableRequest(BaseModel):
    disabled: bool


class UpdateRuoliRequest(BaseModel):
    ruoli: List[str]


# --- SEDE ---

class SedeCreate(BaseModel):
    nome: str
    codice: str
    indirizzo: Optional[str] = None
    tariffa_km: float = 0.35
    rimborso_pasti: float = 15.0
    rimborso_autostrada: bool = True


class SedeUpdate(BaseModel):
    nome: Optional[str] = None
    indirizzo: Optional[str] = None
    tariffa_km: Optional[float] = None
    rimborso_pasti: Optional[float] = None
    rimborso_autostrada: Optional[bool] = None


# --- MOTIVO RIMBORSO ---

class MotivoRimborsoCreate(BaseModel):
    nome: str
    descrizione: Optional[str] = None
    richiede_note: bool = False


class MotivoRimborsoUpdate(BaseModel):
    nome: Optional[str] = None
    descrizione: Optional[str] = None
    richiede_note: Optional[bool] = None


# --- RIMBORSO ---

class RimborsoCreate(BaseModel):
    data: str
    motivo_id: str
    indirizzo_partenza: str
    indirizzo_partenza_tipo: str = "manuale"
    indirizzo_arrivo: str
    km_andata: float
    km_calcolati: Optional[float] = None
    km_modificati_manualmente: bool = False
    andata_ritorno: bool = True
    uso_autostrada: bool = False
    costo_autostrada: float = 0
    importo_pasti: float = 0
    numero_partecipanti_pasto: int = 0
    note: Optional[str] = None


class RimborsoUpdate(BaseModel):
    stato: Optional[str] = None
    note_admin: Optional[str] = None
    km_approvati: Optional[bool] = None


# --- ANNUNCI / DOCUMENTI ---

class AnnuncioCreate(BaseModel):
    titolo: str
    contenuto: str
    link_documento: Optional[str] = None


class DocumentoCreate(BaseModel):
    nome: str
    categoria: str
    descrizione: Optional[str] = None


# --- MAPS ---

class CalcoloKmRequest(BaseModel):
    origine: str
    destinazione: str


# --- CONTATTI ---

class ContattoBase(BaseModel):
    titolo: str
    descrizione: Optional[str] = None
    tipo: str
    valore: str


class ContattoCreate(ContattoBase):
    pass


class ContattoUpdate(BaseModel):
    titolo: Optional[str] = None
    descrizione: Optional[str] = None
    tipo: Optional[str] = None
    valore: Optional[str] = None
