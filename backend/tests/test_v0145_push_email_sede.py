# v0.14.5 - Web Push VAPID (public-key, subscribe/unsubscribe, invio in background su notifica)
# + Email per sede (GET/PUT email-config, test invio, cifratura Fernet, invia_email rispetta modalita)
import base64
import os
import random
import time
import uuid
from datetime import datetime, timezone

import bcrypt
import pytest
import requests
from bson import ObjectId
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from dotenv import dotenv_values
from pymongo import MongoClient

FE_ENV = dotenv_values("/app/frontend/.env")
BE_ENV = dotenv_values("/app/backend/.env")
BASE_URL = FE_ENV["REACT_APP_BACKEND_URL"].rstrip("/")
API = f"{BASE_URL}/api"
PWD = "Prova123!"
SA_EMAIL, SA_PWD = "superadmin@sla.it", "SlaAdmin2024!"
LOG = "/var/log/supervisor/backend.err.log"

mc = MongoClient(BE_ENV["MONGO_URL"])
db = mc[BE_ENV["DB_NAME"]]
HASH = bcrypt.hashpw(PWD.encode(), bcrypt.gensalt()).decode()
TAG = uuid.uuid4().hex[:6]


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
           "created_at": datetime.now(timezone.utc).isoformat(), **extra}
    return email, str(db.users.insert_one(doc).inserted_id)


def _b64(b):
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode()


def _fake_keys():
    k = ec.generate_private_key(ec.SECP256R1())
    pub = k.public_key().public_bytes(serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint)
    return {"p256dh": _b64(pub), "auth": _b64(os.urandom(16))}


def _log_size():
    return os.path.getsize(LOG)


def _log_since(pos):
    with open(LOG, "rb") as f:
        f.seek(pos)
        return f.read().decode(errors="ignore")


@pytest.fixture(scope="module")
def env():
    sa, r = _login(SA_EMAIL, SA_PWD)
    assert r.status_code == 200, r.text
    sA = str(db.sedi.insert_one({"nome": f"TEST_SedeA_{TAG}", "codice": f"TA{TAG}", "tariffa_km": 0.35,
                                 "rimborso_pasti": 15.0, "rimborso_autostrada": True}).inserted_id)
    sB = str(db.sedi.insert_one({"nome": f"TEST_SedeB_{TAG}", "codice": f"TB{TAG}", "tariffa_km": 0.35,
                                 "rimborso_pasti": 15.0, "rimborso_autostrada": True}).inserted_id)
    u = {}
    for key, ruoli, sede in [("admA", ["admin"], sA), ("segA", ["segretario"], sA), ("delA", ["delegato"], sA),
                             ("admB", ["admin"], sB), ("delA2", ["delegato"], sA)]:
        u[key] = _mk_user(key, ruoli, sede)
    sess = {k: _login(v[0])[0] for k, v in u.items()}
    yield {"sa": sa, "sA": sA, "sB": sB, "u": u, "s": sess}
    ids = [v[1] for v in u.values()]
    db.users.delete_many({"email": {"$regex": TAG}})
    db.sedi.delete_many({"_id": {"$in": [ObjectId(sA), ObjectId(sB)]}})
    db.notifiche.delete_many({"user_id": {"$in": ids}})
    db.push_subscriptions.delete_many({"endpoint": {"$regex": TAG}})
    db.audit_log.delete_many({"target_label": {"$regex": TAG}})
    db.audit_log.delete_many({"sede_id": {"$in": [sA, sB]}})
    db.login_attempts.delete_many({"identifier": {"$regex": TAG}})


# ---------- Push ----------
class TestPush:
    def test_public_key_stable(self, env):
        r1 = requests.get(f"{API}/push/public-key")
        r2 = requests.get(f"{API}/push/public-key")
        assert r1.status_code == 200
        k = r1.json()["public_key"]
        assert k == r2.json()["public_key"]
        raw = base64.urlsafe_b64decode(k + "=" * (-len(k) % 4))
        assert len(raw) == 65 and raw[0] == 4
        if not (BE_ENV.get("VAPID_PUBLIC_KEY")):
            doc = db.impostazioni.find_one({"_id": "vapid"})
            assert doc and doc["public"] == k

    def test_subscribe_requires_login(self, env):
        r = requests.post(f"{API}/push/subscribe", json={"endpoint": f"https://x.test/{TAG}", "keys": _fake_keys()})
        assert r.status_code == 401

    def test_subscribe_non_https_422(self, env):
        r = env["s"]["delA"].post(f"{API}/push/subscribe", json={"endpoint": f"http://x.test/{TAG}", "keys": _fake_keys()})
        assert r.status_code == 422

    def test_subscribe_upsert_and_unsubscribe_own_only(self, env):
        ep = f"https://updates.push.services.mozilla.com/wpush/v2/fake{TAG}up"
        s = env["s"]["delA"]
        for _ in range(2):
            r = s.post(f"{API}/push/subscribe", json={"endpoint": ep, "keys": _fake_keys()})
            assert r.status_code == 200, r.text
        assert db.push_subscriptions.count_documents({"endpoint": ep}) == 1
        assert db.push_subscriptions.find_one({"endpoint": ep})["user_id"] == env["u"]["delA"][1]
        # another user cannot remove it
        r = env["s"]["delA2"].post(f"{API}/push/unsubscribe", json={"endpoint": ep})
        assert r.status_code == 200
        assert db.push_subscriptions.count_documents({"endpoint": ep}) == 1
        r = s.post(f"{API}/push/unsubscribe", json={"endpoint": ep})
        assert r.status_code == 200
        assert db.push_subscriptions.count_documents({"endpoint": ep}) == 0

    def test_push_on_approval_background_no_crash(self, env):
        ep = f"https://fcm.googleapis.com/fcm/send/fake{TAG}"
        # pending user with subscription inserted directly
        email, uid = _mk_user("pend", ["delegato"], env["sA"], stato_approvazione="in_attesa")
        db.push_subscriptions.insert_one({"endpoint": ep, "user_id": uid, "keys": _fake_keys()})
        pos = _log_size()
        t = time.time()
        r = env["s"]["admA"].post(f"{API}/users/{uid}/approva")
        dt = time.time() - t
        assert r.status_code == 200, r.text
        assert dt < 5, f"approve took {dt}s"
        # wait for background push
        for _ in range(15):
            time.sleep(1)
            if db.push_subscriptions.count_documents({"endpoint": ep}) == 0:
                break
        logs = _log_since(pos)
        assert "Traceback" not in logs, logs[-2000:]
        print("remaining subs:", db.push_subscriptions.count_documents({"endpoint": ep}))
        print("logs:", logs[-1500:])
        # sede in modalita nessuna -> no emergent call
        assert "integrations.emergentagent.com" not in logs
        assert db.push_subscriptions.count_documents({"endpoint": ep}) == 0, "404/410 subscription not deleted"


# ---------- Email config ----------
class TestEmailConfig:
    def test_get_permissions(self, env):
        sA = env["sA"]
        r = env["s"]["admA"].get(f"{API}/sedi/{sA}/email-config")
        assert r.status_code == 200
        d = r.json()
        assert d["modalita"] == "nessuna" and d["password_impostata"] is False
        assert "emergent_disponibile" in d and "smtp_password_enc" not in d
        assert env["sa"].get(f"{API}/sedi/{sA}/email-config").status_code == 200
        for k in ("admB", "segA", "delA"):
            assert env["s"][k].get(f"{API}/sedi/{sA}/email-config").status_code == 403, k

    def test_put_validation(self, env):
        s, sA = env["s"]["admA"], env["sA"]
        r = s.put(f"{API}/sedi/{sA}/email-config", json={"modalita": "smtp", "smtp_host": "smtp.x.it"})
        assert r.status_code == 400
        r = s.put(f"{API}/sedi/{sA}/email-config", json={"modalita": "smtp", "smtp_host": "smtp.x.it", "smtp_port": 587, "smtp_user": "u@x.it"})
        assert r.status_code == 400 and "password" in r.json()["detail"].lower()
        r = s.put(f"{API}/sedi/{sA}/email-config", json={"modalita": "boh"})
        assert r.status_code == 422
        assert env["s"]["admB"].put(f"{API}/sedi/{sA}/email-config", json={"modalita": "nessuna"}).status_code == 403

    def test_put_password_encrypted_and_kept(self, env):
        s, sA = env["s"]["admA"], env["sA"]
        body = {"modalita": "smtp", "smtp_host": f"smtp.nonexistent-{TAG}.invalid", "smtp_port": 587,
                "smtp_tls": "starttls", "smtp_user": "u@x.it", "smtp_password": "Segreta123", "smtp_from": "u@x.it"}
        r = s.put(f"{API}/sedi/{sA}/email-config", json=body)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["password_impostata"] is True and "smtp_password_enc" not in d and "smtp_password" not in d
        enc = db.sedi.find_one({"_id": ObjectId(sA)})["email_config"]["smtp_password_enc"]
        assert enc.startswith("gAAAA") and "Segreta123" not in enc
        body.pop("smtp_password")
        r = s.put(f"{API}/sedi/{sA}/email-config", json=body)
        assert r.status_code == 200
        assert db.sedi.find_one({"_id": ObjectId(sA)})["email_config"]["smtp_password_enc"] == enc
        g = s.get(f"{API}/sedi/{sA}/email-config").json()
        assert g["modalita"] == "smtp" and g["password_impostata"] is True and "smtp_password_enc" not in g

    def test_test_email_smtp_bad_host(self, env):
        r = env["s"]["admA"].post(f"{API}/sedi/{env['sA']}/email-config/test")
        assert r.status_code == 400
        assert "Invio non riuscito" in r.json()["detail"]
        print(r.json())

    def test_public_sedi_no_email_config(self, env):
        r = requests.get(f"{API}/sedi")
        assert r.status_code == 200
        for s in r.json():
            assert "email_config" not in s
            assert "smtp_password_enc" not in str(s)

    def test_test_email_nessuna_400(self, env):
        s, sA = env["s"]["admA"], env["sA"]
        assert s.put(f"{API}/sedi/{sA}/email-config", json={"modalita": "nessuna"}).status_code == 200
        r = s.post(f"{API}/sedi/{sA}/email-config/test")
        assert r.status_code == 400

    def test_emergent_mode(self, env):
        sB = env["sB"]
        g = env["sa"].get(f"{API}/sedi/{sB}/email-config").json()
        r = env["s"]["admB"].put(f"{API}/sedi/{sB}/email-config", json={"modalita": "emergent"})
        if not g["emergent_disponibile"]:
            assert r.status_code == 400
            return
        assert r.status_code == 200, r.text
        # admin B with delivered@resend.dev
        db.users.update_one({"_id": ObjectId(env["u"]["admB"][1])}, {"$set": {"email": f"delivered+{TAG}@resend.dev"}})
        r = env["s"]["admB"].post(f"{API}/sedi/{sB}/email-config/test")
        print("emergent test:", r.status_code, r.text)
        assert r.status_code == 200
        assert "Email di prova inviata" in r.json()["message"]
        env["s"]["admB"].put(f"{API}/sedi/{sB}/email-config", json={"modalita": "nessuna"})

    def test_forgot_password_message(self, env):
        r = requests.post(f"{API}/auth/forgot-password", json={"email": f"nobody_{TAG}@test.it"},
                          headers={"X-Forwarded-For": _ip()})
        assert r.status_code == 200
        assert "segreteria" in r.json()["message"]
