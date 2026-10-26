# v0.14.4 - Cartelle documenti (CRUD, visibilità riservata, upload/download/delete), forgot/reset password,
# email-contatto sede, email transazionali in background (non bloccanti)
import hashlib
import random
import uuid
from datetime import UTC, datetime, timedelta

import bcrypt
import pytest
import requests
from bson import ObjectId
from dotenv import dotenv_values
from pymongo import MongoClient

FE_ENV = dotenv_values("/app/frontend/.env")
BE_ENV = dotenv_values("/app/backend/.env")
BASE_URL = FE_ENV["REACT_APP_BACKEND_URL"].rstrip("/")
API = f"{BASE_URL}/api"
PWD = "Prova123!"
SA_EMAIL, SA_PWD = "superadmin@sla.it", "SlaAdmin2024!"

mc = MongoClient(BE_ENV["MONGO_URL"])
db = mc[BE_ENV["DB_NAME"]]
HASH = bcrypt.hashpw(PWD.encode(), bcrypt.gensalt()).decode()
TAG = uuid.uuid4().hex[:6]
PDF = b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF\n"


def _ip():
    return f"10.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}"


def _login(email, pwd=PWD):
    s = requests.Session()
    s.headers["X-Forwarded-For"] = _ip()
    r = s.post(f"{API}/auth/login", json={"email": email, "password": pwd})
    return s, r


def _mk_user(key, ruoli, sede_id, **extra):
    email = f"test_{key}_{TAG}@test.it".lower()
    doc = {"email": email, "password_hash": HASH, "nome": "TEST", "cognome": key, "ruoli": ruoli,
           "sede_id": sede_id, "disabled": False, "iban": "IT60X0542811101000000123456",
           "created_at": datetime.now(UTC).isoformat(), **extra}
    return email, str(db.users.insert_one(doc).inserted_id)


@pytest.fixture(scope="module")
def env():
    sa, r = _login(SA_EMAIL, SA_PWD)
    assert r.status_code == 200, r.text
    sA = str(db.sedi.insert_one({"nome": f"TEST_SedeA_{TAG}", "codice": f"TA{TAG}", "tariffa_km": 0.35,
                                 "rimborso_pasti": 15.0, "rimborso_autostrada": True}).inserted_id)
    sB = str(db.sedi.insert_one({"nome": f"TEST_SedeB_{TAG}", "codice": f"TB{TAG}", "tariffa_km": 0.35,
                                 "rimborso_pasti": 15.0, "rimborso_autostrada": True}).inserted_id)
    u = {}
    for key, ruoli, sede in [("admA", ["admin"], sA), ("segA", ["segretario"], sA), ("cassA", ["cassiere"], sA),
                             ("delA", ["delegato"], sA), ("admB", ["admin"], sB), ("segB", ["segretario"], sB),
                             ("pwd", ["delegato"], sA)]:
        u[key] = _mk_user(key, ruoli, sede)
    sess = {k: _login(v[0])[0] for k, v in u.items() if k != "pwd"}
    yield {"sa": sa, "sA": sA, "sB": sB, "u": u, "s": sess}
    ids = [v[1] for v in u.values()]
    db.users.delete_many({"_id": {"$in": [ObjectId(i) for i in ids]}})
    db.users.delete_many({"email": {"$regex": TAG}})
    db.sedi.delete_many({"_id": {"$in": [ObjectId(sA), ObjectId(sB)]}})
    db.cartelle.delete_many({"nome": {"$regex": f"^TEST_{TAG}"}})
    db.documenti.delete_many({"nome": {"$regex": f"^TEST_{TAG}"}})
    db.notifiche.delete_many({"user_id": {"$in": ids}})
    db.rimborsi.delete_many({"user_id": {"$in": ids}})
    db.password_resets.delete_many({"user_id": {"$in": ids}})
    db.audit_log.delete_many({"target_label": {"$regex": TAG}})
    db.login_attempts.delete_many({"identifier": {"$regex": TAG}})


def _upload(s, cid, nome="doc"):
    return s.post(f"{API}/documenti", files={"file": ("t.pdf", PDF, "application/pdf")},
                  data={"nome": f"TEST_{TAG}_{nome}", "cartella_id": cid, "descrizione": "d"})


# ---------- Cartelle ----------
class TestCartelle:
    def test_create_permissions_and_dup(self, env):
        s = env["s"]
        r = s["admA"].post(f"{API}/cartelle", json={"nome": f"TEST_{TAG}_A"})
        assert r.status_code == 200, r.text
        assert r.json()["sede_id"] == env["sA"]
        env["cA"] = r.json()["id"]
        r = s["admA"].post(f"{API}/cartelle", json={"nome": f"TEST_{TAG}_A"})
        assert r.status_code == 400
        for k in ("segA", "cassA", "delA"):
            assert s[k].post(f"{API}/cartelle", json={"nome": f"TEST_{TAG}_X"}).status_code == 403, k
        # admin non-nazionale che prova ambito 'tutte' -> 403
        assert s["admA"].post(f"{API}/cartelle", json={"nome": f"TEST_{TAG}_T", "ambito": "tutte"}).status_code == 403

    def test_superadmin_ambiti(self, env):
        r = env["sa"].post(f"{API}/cartelle", json={"nome": f"TEST_{TAG}_ALL", "ambito": "tutte"})
        assert r.status_code == 200, r.text
        assert r.json()["sede_id"] is None
        env["cAll"] = r.json()["id"]
        r = env["sa"].post(f"{API}/cartelle", json={"nome": f"TEST_{TAG}_B", "ambito": "sede", "sede_id": env["sB"]})
        assert r.status_code == 200 and r.json()["sede_id"] == env["sB"]
        env["cB"] = r.json()["id"]

    def test_list_flags(self, env):
        r = env["s"]["admA"].get(f"{API}/cartelle")
        assert r.status_code == 200
        by = {c["id"]: c for c in r.json()}
        assert env["cA"] in by and env["cAll"] in by and env["cB"] not in by
        assert by[env["cA"]]["gestibile"] is True and by[env["cA"]]["caricabile"] is True
        assert by[env["cAll"]]["gestibile"] is False
        assert by[env["cA"]]["num_documenti"] == 0
        seg = {c["id"]: c for c in env["s"]["segA"].get(f"{API}/cartelle").json()}
        assert seg[env["cA"]]["gestibile"] is False and seg[env["cA"]]["caricabile"] is True
        dl = {c["id"]: c for c in env["s"]["delA"].get(f"{API}/cartelle").json()}
        assert dl[env["cA"]]["caricabile"] is False

    def test_upload_permissions(self, env):
        s = env["s"]
        r = _upload(s["segA"], env["cA"], "seg")
        assert r.status_code == 200, r.text
        assert r.json()["sede_id"] == env["sA"] and r.json()["cartella_id"] == env["cA"]
        env["docA"] = r.json()["id"]
        assert _upload(s["admB"], env["cA"]).status_code == 403
        assert _upload(s["segB"], env["cA"]).status_code == 403
        assert _upload(s["delA"], env["cA"]).status_code == 403
        r = _upload(env["sa"], env["cAll"], "all")
        assert r.status_code == 200 and r.json()["sede_id"] is None
        env["docAll"] = r.json()["id"]
        # num_documenti aggiornato
        by = {c["id"]: c for c in s["admA"].get(f"{API}/cartelle").json()}
        assert by[env["cA"]]["num_documenti"] == 1

    def test_visibility_reserved(self, env):
        s = env["s"]
        assert s["segA"].put(f"{API}/cartelle/{env['cA']}/visibilita", json={"visibile": False}).status_code == 403
        assert s["admB"].put(f"{API}/cartelle/{env['cA']}/visibilita", json={"visibile": False}).status_code == 403
        r = s["admA"].put(f"{API}/cartelle/{env['cA']}/visibilita", json={"visibile": False})
        assert r.status_code == 200
        assert db.audit_log.find_one({"action": "cartella.visibility", "target_id": env["cA"]})
        for k in ("segA", "delA"):
            ids = [c["id"] for c in s[k].get(f"{API}/cartelle").json()]
            assert env["cA"] not in ids, k
        assert env["cA"] in [c["id"] for c in s["admA"].get(f"{API}/cartelle").json()]
        assert env["cA"] in [c["id"] for c in env["sa"].get(f"{API}/cartelle").json()]
        # documenti
        assert s["delA"].get(f"{API}/documenti", params={"cartella_id": env["cA"]}).status_code == 403
        docs = [d["id"] for d in s["delA"].get(f"{API}/documenti").json()]
        assert env["docA"] not in docs and env["docAll"] in docs
        assert s["delA"].get(f"{API}/documenti/{env['docA']}/download").status_code == 403
        assert _upload(s["segA"], env["cA"]).status_code == 403
        r = s["admA"].get(f"{API}/documenti/{env['docA']}/download")
        assert r.status_code == 200 and r.content.startswith(b"%PDF")
        assert s["admA"].put(f"{API}/cartelle/{env['cA']}/visibilita", json={"visibile": True}).status_code == 200
        assert env["cA"] in [c["id"] for c in s["delA"].get(f"{API}/cartelle").json()]

    def test_delete_flow(self, env):
        s = env["s"]
        r = s["admA"].delete(f"{API}/cartelle/{env['cA']}")
        assert r.status_code == 400 and "non è vuota" in r.json()["detail"]
        assert s["admB"].delete(f"{API}/documenti/{env['docA']}").status_code == 403
        assert s["delA"].delete(f"{API}/documenti/{env['docA']}").status_code == 403
        assert s["segA"].delete(f"{API}/documenti/{env['docA']}").status_code == 200
        assert s["segA"].delete(f"{API}/cartelle/{env['cA']}").status_code == 403
        assert s["admA"].delete(f"{API}/cartelle/{env['cA']}").status_code == 200
        assert db.audit_log.find_one({"action": "cartella.delete", "target_id": env["cA"]})
        assert env["sa"].delete(f"{API}/documenti/{env['docAll']}").status_code == 200
        assert env["sa"].delete(f"{API}/cartelle/{env['cAll']}").status_code == 200
        assert env["sa"].delete(f"{API}/cartelle/{env['cB']}").status_code == 200
        assert env["sa"].delete(f"{API}/cartelle/{env['cB']}").status_code == 404

    def test_upload_missing_cartella(self, env):
        r = env["s"]["admA"].post(f"{API}/documenti", files={"file": ("t.pdf", PDF, "application/pdf")},
                                  data={"nome": f"TEST_{TAG}_x"})
        assert r.status_code == 422


# ---------- Email contatto sede ----------
class TestEmailContatto:
    def test_permissions(self, env):
        s = env["s"]
        assert s["admA"].put(f"{API}/sedi/{env['sA']}/email-contatto", json={"email_contatto": "segreteria@example.com"}).status_code == 200
        assert s["admB"].put(f"{API}/sedi/{env['sA']}/email-contatto", json={"email_contatto": "x@example.com"}).status_code == 403
        assert s["segA"].put(f"{API}/sedi/{env['sA']}/email-contatto", json={"email_contatto": "x@example.com"}).status_code == 403
        assert s["admA"].put(f"{API}/sedi/{env['sA']}/email-contatto", json={"email_contatto": "nonvalida"}).status_code == 422
        assert env["sa"].put(f"{API}/sedi/{env['sB']}/email-contatto", json={"email_contatto": "b@example.com"}).status_code == 200
        assert db.sedi.find_one({"_id": ObjectId(env["sA"])})["email_contatto"] == "segreteria@example.com"

    def test_get_sedi_exposes_email(self, env):
        sedi = {x["id"]: x for x in requests.get(f"{API}/sedi").json()}
        assert sedi[env["sA"]].get("email_contatto") == "segreteria@example.com", sedi[env["sA"]]


# ---------- Forgot / reset password ----------
class TestPasswordReset:
    def test_forgot_identical(self, env):
        email = env["u"]["pwd"][0]
        h = {"X-Forwarded-For": _ip()}
        r1 = requests.post(f"{API}/auth/forgot-password", json={"email": email}, headers=h)
        r2 = requests.post(f"{API}/auth/forgot-password", json={"email": f"nobody_{TAG}@example.com"}, headers=h)
        assert r1.status_code == 200 and r2.status_code == 200 and r1.json() == r2.json()
        rec = db.password_resets.find_one({"user_id": env["u"]["pwd"][1]})
        assert rec and len(rec["token_hash"]) == 64
        r3 = requests.post(f"{API}/auth/forgot-password", json={"email": email}, headers=h)
        assert r3.status_code == 200
        rec2 = db.password_resets.find_one({"user_id": env["u"]["pwd"][1]})
        assert rec2["_id"] == rec["_id"]  # cooldown: nessun nuovo token

    def test_reset_with_token(self, env):
        uid = env["u"]["pwd"][1]
        db.password_resets.delete_many({"user_id": uid})
        now = datetime.now(UTC)
        db.password_resets.insert_one({"user_id": uid, "token_hash": hashlib.sha256(b"testtoken123").hexdigest(),
                                       "created_at": now.isoformat(), "expires_at": (now + timedelta(minutes=30)).isoformat()})
        db.password_resets.insert_one({"user_id": uid, "token_hash": hashlib.sha256(b"expired123").hexdigest(),
                                       "created_at": now.isoformat(), "expires_at": (now - timedelta(minutes=1)).isoformat()})
        h = {"X-Forwarded-For": _ip()}
        assert requests.post(f"{API}/auth/reset-password", json={"token": "wrong", "new_password": "Nuova123!x"}, headers=h).status_code == 400
        assert requests.post(f"{API}/auth/reset-password", json={"token": "expired123", "new_password": "Nuova123!x"}, headers=h).status_code == 400
        assert requests.post(f"{API}/auth/reset-password", json={"token": "testtoken123", "new_password": "debole"}, headers=h).status_code == 400
        tv = db.users.find_one({"_id": ObjectId(uid)}).get("token_version", 0)
        r = requests.post(f"{API}/auth/reset-password", json={"token": "testtoken123", "new_password": "Nuova123!x"}, headers=h)
        assert r.status_code == 200, r.text
        u = db.users.find_one({"_id": ObjectId(uid)})
        assert u.get("token_version", 0) == tv + 1
        assert db.password_resets.count_documents({"user_id": uid}) == 0
        assert _login(env["u"]["pwd"][0], "Nuova123!x")[1].status_code == 200
        assert _login(env["u"]["pwd"][0], PWD)[1].status_code == 401
        # riuso token -> 400
        assert requests.post(f"{API}/auth/reset-password", json={"token": "testtoken123", "new_password": "Nuova123!y"}, headers=h).status_code == 400


# ---------- Email in background non bloccanti ----------
class TestEmailNonBlocking:
    def test_approve_registration(self, env):
        email, uid = _mk_user("pend", ["delegato"], env["sA"], stato_approvazione="in_attesa")
        r = env["s"]["admA"].post(f"{API}/users/{uid}/approva")
        assert r.status_code == 200, r.text
        email2, uid2 = _mk_user("pend2", ["delegato"], env["sA"], stato_approvazione="in_attesa")
        assert env["s"]["admA"].post(f"{API}/users/{uid2}/rifiuta").status_code == 200

    def test_rimborso_stato(self, env):
        rid = str(db.rimborsi.insert_one({"user_id": env["u"]["delA"][1], "sede_id": env["sA"], "stato": "in_attesa",
                                          "data": "2026-01-10", "importo_totale": 12.5,
                                          "created_at": datetime.now(UTC).isoformat()}).inserted_id)
        r = env["s"]["admA"].put(f"{API}/rimborsi/{rid}", json={"stato": "approvato"})
        assert r.status_code == 200, r.text
        r = env["s"]["admA"].put(f"{API}/rimborsi/{rid}", json={"stato": "rifiutato"})
        assert r.status_code == 200, r.text

    def test_change_password(self, env):
        email, uid = _mk_user("chg", ["delegato"], env["sA"])
        s, r = _login(email)
        assert r.status_code == 200
        r = s.post(f"{API}/auth/change-password", json={"current_password": PWD, "new_password": "Cambio123!z"})
        assert r.status_code == 200, r.text
