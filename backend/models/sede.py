"""
Sede Models - Modelli per gestione concessionarie autostradali

Ogni sede ha tariffe personalizzate per il calcolo rimborsi:
- tariffa_km: Euro per chilometro
- rimborso_pasti: Importo fisso per pasto (se applicabile)
- rimborso_autostrada: Se abilitato, rimborsa pedaggi
"""

from pydantic import BaseModel
from typing import Optional


class SedeCreate(BaseModel):
    """Dati per creare nuova sede (solo SuperAdmin)"""
    nome: str  # es. "Autostrada del Brennero"
    codice: str  # es. "A22" - deve essere unico
    indirizzo: Optional[str] = None
    tariffa_km: float = 0.35  # Default: 0.35 EUR/km
    rimborso_pasti: float = 15.0  # Default: 15 EUR/pasto
    rimborso_autostrada: bool = True  # Se rimborsare pedaggi


class SedeUpdate(BaseModel):
    """Campi aggiornabili per una sede"""
    nome: Optional[str] = None
    indirizzo: Optional[str] = None
    tariffa_km: Optional[float] = None
    rimborso_pasti: Optional[float] = None
    rimborso_autostrada: Optional[bool] = None
