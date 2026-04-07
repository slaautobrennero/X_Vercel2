"""
Documento Models - Modelli per documenti e annunci

Categorie documenti:
- modulistica: Moduli da compilare/scaricare
- documento: Documenti informativi
- altro: Altri file

Formati supportati: PDF, JPG, PNG (max 5MB)
"""

from pydantic import BaseModel
from typing import Optional


class AnnuncioCreate(BaseModel):
    """Crea nuovo annuncio in bacheca"""
    titolo: str
    contenuto: str  # Testo dell'annuncio
    link_documento: Optional[str] = None  # URL opzionale a documento


class DocumentoCreate(BaseModel):
    """Metadati per upload documento"""
    nome: str  # Nome visualizzato
    categoria: str  # modulistica, documento, altro
    descrizione: Optional[str] = None
