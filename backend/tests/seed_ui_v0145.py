# Seed/cleanup for v0.14.5 UI tests: python seed_ui_v0145.py [seed|clean]
import sys
from datetime import datetime, timezone
import bcrypt
from dotenv import dotenv_values
from pymongo import MongoClient

BE = dotenv_values("/app/backend/.env")
db = MongoClient(BE["MONGO_URL"])[BE["DB_NAME"]]
if sys.argv[1] == "seed":
    sid = str(db.sedi.insert_one({"nome": "TEST_UI_Sede145", "codice": "TUI145", "tariffa_km": 0.35,
                                  "rimborso_pasti": 15.0, "rimborso_autostrada": True}).inserted_id)
    h = bcrypt.hashpw(b"Prova123!", bcrypt.gensalt()).decode()
    for e, r in [("test_ui145_adm@test.it", ["admin"]), ("test_ui145_del@test.it", ["delegato"])]:
        db.users.insert_one({"email": e, "password_hash": h, "nome": "TEST", "cognome": "UI", "ruoli": r, "sede_id": sid,
                             "disabled": False, "iban": "IT60X0542811101000000123456",
                             "privacy_accettata": True, "created_at": datetime.now(timezone.utc).isoformat()})
    print(sid)
else:
    ids = [str(u["_id"]) for u in db.users.find({"email": {"$regex": "^test_ui145_"}})]
    db.users.delete_many({"email": {"$regex": "^test_ui145_"}})
    db.sedi.delete_many({"codice": "TUI145"})
    db.notifiche.delete_many({"user_id": {"$in": ids}})
    db.push_subscriptions.delete_many({"user_id": {"$in": ids}})
    db.audit_log.delete_many({"target_label": "TEST_UI_Sede145"})
    print("cleaned")
