"""
Notifications Service - Gestione notifiche

Crea notifiche in-app per:
- Nuove richieste rimborso (per admin)
- Approvazione/rifiuto rimborso (per utente)
- Pagamento completato (per utente)

Le notifiche possono essere:
- Personali (user_id specifico)
- Di sede (tutti gli admin della sede)
- Globali (sede_id = None)
"""

from datetime import datetime, timezone
from ..utils.database import db


async def create_notification(
    tipo: str,
    titolo: str,
    messaggio: str,
    user_id: str = None,
    sede_id: str = None,
    extra_data: dict = None
) -> str:
    """
    Crea nuova notifica nel database.
    
    Args:
        tipo: Categoria ("rimborso", "documento", "sistema")
        titolo: Titolo breve
        messaggio: Testo completo
        user_id: ID utente destinatario (None = per admin sede)
        sede_id: ID sede (None = globale)
        extra_data: Dati aggiuntivi (es. rimborso_id)
    
    Returns:
        ID della notifica creata
    """
    notifica_doc = {
        "user_id": user_id,
        "sede_id": sede_id,
        "tipo": tipo,
        "titolo": titolo,
        "messaggio": messaggio,
        "letto": False,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    # Aggiungi dati extra se presenti
    if extra_data:
        notifica_doc.update(extra_data)
    
    result = await db.notifiche.insert_one(notifica_doc)
    return str(result.inserted_id)


async def notify_rimborso_created(user: dict, importo: float, rimborso_id: str, km_modificati: bool = False):
    """
    Notifica admin di nuova richiesta rimborso.
    """
    titolo = "Nuova richiesta rimborso"
    if km_modificati:
        titolo += " ⚠️ KM MODIFICATI"
    
    messaggio = f"{user['nome']} {user['cognome']} ha inviato una richiesta di rimborso di €{importo:.2f}"
    if km_modificati:
        messaggio += " - ATTENZIONE: KM modificati manualmente!"
    
    await create_notification(
        tipo="rimborso",
        titolo=titolo,
        messaggio=messaggio,
        sede_id=user.get("sede_id"),
        extra_data={"rimborso_id": rimborso_id, "alert_km": km_modificati}
    )


async def notify_rimborso_status(user_id: str, sede_id: str, data_rimborso: str, stato: str):
    """
    Notifica utente di cambio stato rimborso.
    """
    stati_msg = {
        "approvato": "approvata",
        "rifiutato": "rifiutata",
        "pagato": "pagata"
    }
    
    if stato not in stati_msg:
        return
    
    await create_notification(
        tipo="rimborso",
        titolo=f"Richiesta rimborso {stati_msg[stato]}",
        messaggio=f"La tua richiesta di rimborso del {data_rimborso} è stata {stati_msg[stato]}",
        user_id=user_id,
        sede_id=sede_id
    )
