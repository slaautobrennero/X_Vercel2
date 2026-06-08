"""Audit log helper."""
from datetime import datetime, timezone
from typing import Optional
from .db import db


async def _log_audit(
    actor: dict,
    action: str,
    target_type: str,
    target_id: Optional[str] = None,
    target_label: Optional[str] = None,
    sede_id: Optional[str] = None,
    old_value: Optional[str] = None,
    new_value: Optional[str] = None,
    note: Optional[str] = None,
):
    """
    Registra un'azione nell'audit log.
    
    Args:
      actor: dict del current_user (id, nome, cognome, ruolo)
      action: codice azione (es: 'rimborso.approve', 'user.disable', ...)
      target_type: tipo entità (rimborso, user, annuncio, documento, sede, motivo)
      target_id: id entità coinvolta
      target_label: descrizione human-readable
      sede_id: sede di riferimento per filtri
      old_value / new_value: valori prima/dopo
      note: testo libero opzionale
    """
    entry = {
        "actor_id": actor.get("id"),
        "actor_nome": f"{actor.get('nome', '')} {actor.get('cognome', '')}".strip() or actor.get("email", "?"),
        "actor_ruolo": actor.get("ruolo"),
        "action": action,
        "target_type": target_type,
        "target_id": target_id,
        "target_label": target_label,
        "sede_id": sede_id,
        "old_value": old_value,
        "new_value": new_value,
        "note": note,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.audit_log.insert_one(entry)
