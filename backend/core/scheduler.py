"""
Scheduler: promemoria rimborsi pendenti >7 giorni.
Gira in background dal startup del backend.
Invia notifiche SOLO ai cassieri della sede del rimborso.
"""
import asyncio
from datetime import datetime, timezone

from .config import logger
from .db import db


async def _check_pending_reimbursements() -> dict:
    """
    Controlla rimborsi pendenti da >=7 giorni.
    Invia DUE notifiche distinte ai cassieri:
      - "in_attesa": rimborsi DA APPROVARE fermi >=7gg
      - "approvato": rimborsi DA PAGARE fermi >=7gg dall'approvazione
    
    Ricorrenza settimanale (gg 7, 14, 21, ...). Anti-spam tramite marcatori
    `reminder_last_week_attesa` e `reminder_last_week_pagamento` sul rimborso.
    """
    now = datetime.now(timezone.utc)
    soglia_giorni = 7
    risultato = {"in_attesa_inviate": 0, "approvato_inviate": 0, "cassieri_notificati": 0}

    pending = await db.rimborsi.find({
        "stato": {"$in": ["in_attesa", "approvato"]}
    }).to_list(length=None)

    if not pending:
        return risultato

    sedi_buckets: dict = {}
    for r in pending:
        sede_id = r.get("sede_id")
        if sede_id not in sedi_buckets:
            sedi_buckets[sede_id] = {"da_approvare": [], "da_pagare": []}

        if r.get("stato") == "in_attesa":
            created_str = r.get("created_at")
            if not created_str:
                continue
            try:
                created_dt = datetime.fromisoformat(created_str.replace("Z", "+00:00"))
            except Exception:
                continue
            giorni = (now - created_dt).days
            if giorni >= soglia_giorni:
                settimana = giorni // soglia_giorni
                last_week = r.get("reminder_last_week_attesa", 0)
                if settimana > last_week:
                    sedi_buckets[sede_id]["da_approvare"].append({"rimborso": r, "giorni": giorni, "settimana": settimana})

        elif r.get("stato") == "approvato":
            approvato_str = r.get("approvato_at") or r.get("created_at")
            if not approvato_str:
                continue
            try:
                approvato_dt = datetime.fromisoformat(approvato_str.replace("Z", "+00:00"))
            except Exception:
                continue
            giorni = (now - approvato_dt).days
            if giorni >= soglia_giorni:
                settimana = giorni // soglia_giorni
                last_week = r.get("reminder_last_week_pagamento", 0)
                if settimana > last_week:
                    sedi_buckets[sede_id]["da_pagare"].append({"rimborso": r, "giorni": giorni, "settimana": settimana})

    cassieri_notificati_ids = set()
    for sede_id, buckets in sedi_buckets.items():
        da_approvare = buckets["da_approvare"]
        da_pagare = buckets["da_pagare"]

        if not da_approvare and not da_pagare:
            continue

        role_match = {"$or": [{"ruolo": "cassiere"}, {"ruoli": "cassiere"}]}
        if sede_id:
            cassieri_query = {"$and": [role_match, {"sede_id": sede_id}, {"disabled": {"$ne": True}}]}
        else:
            cassieri_query = {"$and": [role_match, {"disabled": {"$ne": True}}]}

        cassieri = await db.users.find(cassieri_query, {"_id": 1}).to_list(length=None)
        if not cassieri:
            continue

        if da_approvare:
            count = len(da_approvare)
            messaggio = f"{count} rimborso/i in attesa di approvazione da almeno 7 giorni"
            notifiche = [{
                "user_id": str(c["_id"]),
                "tipo": "promemoria_rimborsi",
                "titolo": "Rimborsi da approvare",
                "messaggio": messaggio,
                "rimborsi_count": count,
                "stato_filtro": "in_attesa",
                "letto": False,
                "created_at": now.isoformat(),
            } for c in cassieri]
            await db.notifiche.insert_many(notifiche)
            risultato["in_attesa_inviate"] += len(notifiche)
            for item in da_approvare:
                await db.rimborsi.update_one(
                    {"_id": item["rimborso"]["_id"]},
                    {"$set": {"reminder_last_week_attesa": item["settimana"]}}
                )
            for c in cassieri:
                cassieri_notificati_ids.add(str(c["_id"]))

        if da_pagare:
            count = len(da_pagare)
            messaggio = f"{count} rimborso/i approvato/i in attesa di pagamento da almeno 7 giorni"
            notifiche = [{
                "user_id": str(c["_id"]),
                "tipo": "promemoria_rimborsi",
                "titolo": "Rimborsi da pagare",
                "messaggio": messaggio,
                "rimborsi_count": count,
                "stato_filtro": "approvato",
                "letto": False,
                "created_at": now.isoformat(),
            } for c in cassieri]
            await db.notifiche.insert_many(notifiche)
            risultato["approvato_inviate"] += len(notifiche)
            for item in da_pagare:
                await db.rimborsi.update_one(
                    {"_id": item["rimborso"]["_id"]},
                    {"$set": {"reminder_last_week_pagamento": item["settimana"]}}
                )
            for c in cassieri:
                cassieri_notificati_ids.add(str(c["_id"]))

    risultato["cassieri_notificati"] = len(cassieri_notificati_ids)
    return risultato


async def _pending_reimbursements_scheduler():
    """
    Loop infinito: ogni 60 minuti controlla se è ora di lanciare il check.
    Il check parte alle 07:00 UTC (≈ 08:00/09:00 ora italiana).
    Resiste a riavvii: lo stato è in DB (collection `system_jobs`).
    """
    while True:
        try:
            now = datetime.now(timezone.utc)
            if now.hour >= 7:
                job_doc = await db.system_jobs.find_one({"_id": "pending_reimbursements"})
                last_run_str = job_doc.get("last_run") if job_doc else None
                last_run_date = None
                if last_run_str:
                    try:
                        last_run_date = datetime.fromisoformat(last_run_str).date()
                    except Exception:
                        last_run_date = None

                if last_run_date != now.date():
                    logger.info("Scheduler: avvio check rimborsi pendenti >7gg")
                    try:
                        result = await _check_pending_reimbursements()
                        logger.info(f"Scheduler: completato - {result}")
                    except Exception as e:
                        logger.error(f"Scheduler errore: {e}")

                    await db.system_jobs.update_one(
                        {"_id": "pending_reimbursements"},
                        {"$set": {"last_run": now.isoformat()}},
                        upsert=True,
                    )
        except Exception as e:
            logger.error(f"Scheduler loop errore: {e}")

        await asyncio.sleep(3600)
