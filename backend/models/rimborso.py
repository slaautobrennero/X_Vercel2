"""
Rimborso Models - Modelli per gestione richieste rimborso

Flusso rimborso:
1. Delegato crea richiesta (stato: in_attesa)
2. Admin approva/rifiuta
3. Se approvato, admin carica contabile bonifico
4. Rimborso passa a stato "pagato"

Stati possibili:
- in_attesa: Richiesta inviata, in attesa di approvazione
- approvato: Approvato, in attesa di pagamento
- rifiutato: Rifiutato dall'admin
- pagato: Bonifico effettuato, contabile caricata
"""

from pydantic import BaseModel
from typing import Optional


class MotivoRimborsoCreate(BaseModel):
    """Crea nuovo motivo/causale rimborso (solo SuperAdmin)"""
    nome: str  # es. "RSA", "Sede", "Altro"
    descrizione: Optional[str] = None
    richiede_note: bool = False  # Se True, note obbligatorie


class MotivoRimborsoUpdate(BaseModel):
    """Aggiorna motivo esistente"""
    nome: Optional[str] = None
    descrizione: Optional[str] = None
    richiede_note: Optional[bool] = None


class RimborsoCreate(BaseModel):
    """Dati per nuova richiesta rimborso"""
    data: str  # Data del viaggio (YYYY-MM-DD)
    motivo_id: str  # ID del motivo (RSA, Sede, Altro...)
    
    # Percorso
    indirizzo_partenza: str
    indirizzo_partenza_tipo: str = "manuale"  # "casa" o "manuale"
    indirizzo_arrivo: str
    
    # Chilometri
    km_andata: float  # KM solo andata
    km_calcolati: Optional[float] = None  # KM da Google Maps (per confronto)
    km_modificati_manualmente: bool = False  # Alert se diversi da calcolati
    andata_ritorno: bool = True  # Se True, raddoppia KM
    
    # Autostrada
    uso_autostrada: bool = False
    costo_autostrada: float = 0  # Costo pedaggi
    
    # Pasti
    importo_pasti: float = 0  # Importo totale ricevuta pasti
    numero_partecipanti_pasto: int = 0  # Quante persone
    
    # Note
    note: Optional[str] = None  # Obbligatorio se motivo.richiede_note


class RimborsoUpdate(BaseModel):
    """Aggiornamento rimborso (solo Admin)"""
    stato: Optional[str] = None  # in_attesa, approvato, rifiutato, pagato
    note_admin: Optional[str] = None  # Note dell'admin
    km_approvati: Optional[bool] = None  # Se approvare KM manuali


class CalcoloKmRequest(BaseModel):
    """Richiesta calcolo KM con Google Maps"""
    origine: str  # Indirizzo completo partenza
    destinazione: str  # Indirizzo completo arrivo
