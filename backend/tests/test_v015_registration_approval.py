# v0.15 - Approvazione registrazioni (register in_attesa, login 403, approva/rifiuta, permessi cross-sede)
# + get_current_user / refresh rifiutano utenti disabled / in_attesa
import os
import uuid
from datetime import datetime, timezone

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
A22 = str(db.sedi.find_one({"nome": {"$regex": "A22"}})["_id"])
HASH = bcrypt.hashpw(PWD.encode(), bcrypt.gensalt()).decode()
TAG = uuid.uuid4().hex[:6]


def _mk_user(email, ruoli, sede_id, stato=None):
    doc = {"email": email, "password_hash": HASH, "nome": "TEST", "cognome": email.split("@")[0],
           "ruoli": ruoli, "sede_id": sede_id, "disabled": False,
           "created_at": datetime.now(timezone.utc).isoformat()}
    if stato:
        doc["stato_approvazione"] = stato
    return str(db.users.insert_one(doc).inserted_id)


def _login(email, pwd=PWD):
    import time
    for _ in range(4):  # slowapi 10/minute su login: attendi e riprova
        s = requests.Session()
        r = s.post(f"{API}/auth/login", json={"email": email, "password": pwd})
        if r.status_code != 429:
            break
        time.sleep(20)
    return s, r


@pytest.fixture(scope="module")
def env():
    sede2 = str(db.sedi.insert_one({"nome": f"TEST_Sede2_{TAG}"}).inserted_id)
    u = {
        "seg_a22": f"test_seg_a22_{TAG}@test.it",
        "adm_a22": f"test_adm_a22_{TAG}@test.it",
        "adm_s2": f"test_adm_s2_{TAG}@test.it",
        "seg_s2": f"test_seg_s2_{TAG}@test.it",
        "isc": f"test_isc_{TAG}@test.it",
        "del": f"test_del_{TAG}@test.it",
        "cas": f"test_cas_{TAG}@test.it",
    }
    ids = {
        "seg_a22": _mk_user(u["seg_a22"], ["segretario"], A22),
        "adm_a22": _mk_user(u["adm_a22"], ["admin"], A22),
        "adm_s2": _mk_user(u["adm_s2"], ["admin"], sede2),
        "seg_s2": _mk_user(u["seg_s2"], ["segretario"], sede2),
        "isc": _mk_user(u["isc"], ["iscritto"], A22),
        "del": _mk_user(u["del"], ["delegato"], A22),
        "cas": _mk_user(u["cas"], ["cassiere"], A22),
    }
    yield {"sede2": sede2, "emails": u, "ids": ids}
    # cleanup
    rx = {"$regex": f"^test_.*_{TAG}@test.it$"}
    uids = [x["_id"] for x in db.users.find({"email": rx})]
    db.notifiche.delete_many({"user_id": {"$in": [str(i) for i in uids]}})
    db.consensi_privacy.delete_many({"user_id": {"$in": uids}})
    db.users.delete_many({"email": rx})
    db.notifiche.delete_many({"messaggio": {"$regex": TAG}})
    db.sedi.delete_one({"_id": ObjectId(sede2)})


# --- Register ---
class TestRegister:
    def test_register_pending_no_cookie_and_notifications(self, env):
        email = f"test_reg_{TAG}@test.it"
        r = requests.post(f"{API}/auth/register", json={
            "email": email, "password": PWD, "nome": "TEST", "cognome": "Reg", "ruolo": "iscritto",
            "sede_id": A22, "privacy_accepted": True, "termini_accepted": True, "privacy_version": "1.0"})
        if r.status_code == 429:
            pytest.skip("register rate-limited")
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["email"] == email and data["stato_approvazione"] == "in_attesa"
        assert isinstance(data["id"], str) and "message" in data
        assert "access_token" not in r.cookies and "refresh_token" not in r.cookies
        sc = r.headers.get("set-cookie", "")
        assert "access_token" not in sc and "refresh_token" not in sc, sc
        doc = db.users.find_one({"email": email})
        assert doc["stato_approvazione"] == "in_attesa"
        assert db.consensi_privacy.find_one({"user_id": doc["_id"]})
        sa_id = str(db.users.find_one({"email": SA_EMAIL})["_id"])
        q = {"titolo": "Nuova registrazione da approvare", "messaggio": {"$regex": email}}
        notified = {n["user_id"] for n in db.notifiche.find(q)}
        assert sa_id in notified
        assert env["ids"]["seg_a22"] in notified and env["ids"]["adm_a22"] in notified
        assert env["ids"]["adm_s2"] not in notified
        assert env["ids"]["isc"] not in notified
        # login pending -> 403
        _, lr = _login(email)
        assert lr.status_code == 403
        assert "attesa di approvazione" in lr.json()["detail"]


# --- Approva / Rifiuta ---
class TestApprovaRifiuta:
    def test_login_pending_403(self, env):
        e = f"test_pend0_{TAG}@test.it"
        _mk_user(e, ["iscritto"], A22, "in_attesa")
        _, r = _login(e)
        assert r.status_code == 403
        assert "Registrazione in attesa di approvazione" in r.json()["detail"]

    @pytest.mark.parametrize("who", ["adm_s2", "seg_s2", "isc", "del", "cas"])
    def test_forbidden_actors(self, env, who):
        pid = _mk_user(f"test_pend_{who}_{TAG}@test.it", ["iscritto"], A22, "in_attesa")
        s, lr = _login(env["emails"][who])
        assert lr.status_code == 200, lr.text
        for az in ("approva", "rifiuta"):
            r = s.post(f"{API}/users/{pid}/{az}")
            assert r.status_code == 403, f"{who} {az}: {r.status_code} {r.text}"
        assert db.users.find_one({"_id": ObjectId(pid)})["stato_approvazione"] == "in_attesa"

    def test_approve_by_segretario_same_sede(self, env):
        e = f"test_pendok_{TAG}@test.it"
        pid = _mk_user(e, ["iscritto"], A22, "in_attesa")
        s, _ = _login(env["emails"]["seg_a22"])
        r = s.post(f"{API}/users/{pid}/approva")
        assert r.status_code == 200, r.text
        doc = db.users.find_one({"_id": ObjectId(pid)})
        assert doc["stato_approvazione"] == "approvato"
        assert doc["approvato_da"] == env["ids"]["seg_a22"]
        assert db.notifiche.find_one({"user_id": pid, "titolo": "Benvenuto nel portale SLA"})
        assert db.audit_log.find_one({"action": "user.registration_approved", "target_id": pid})
        _, lr = _login(e)
        assert lr.status_code == 200
        assert "access_token" in lr.cookies
        # already approved -> 404
        r2 = s.post(f"{API}/users/{pid}/approva")
        assert r2.status_code == 404
        r3 = s.post(f"{API}/users/{pid}/rifiuta")
        assert r3.status_code == 404

    def test_approve_by_admin_same_sede(self, env):
        pid = _mk_user(f"test_pendadm_{TAG}@test.it", ["delegato"], A22, "in_attesa")
        s, _ = _login(env["emails"]["adm_a22"])
        assert s.post(f"{API}/users/{pid}/approva").status_code == 200

    def test_reject_by_superadmin(self, env):
        e = f"test_pendrej_{TAG}@test.it"
        pid = _mk_user(e, ["iscritto"], env["sede2"], "in_attesa")
        db.consensi_privacy.insert_one({"user_id": ObjectId(pid), "email": e})
        db.notifiche.insert_one({"user_id": pid, "titolo": "x"})
        s, lr = _login(SA_EMAIL, SA_PWD)
        assert lr.status_code == 200
        r = s.post(f"{API}/users/{pid}/rifiuta")
        assert r.status_code == 200, r.text
        assert db.users.find_one({"_id": ObjectId(pid)}) is None
        assert db.consensi_privacy.find_one({"user_id": ObjectId(pid)}) is None
        assert db.notifiche.find_one({"user_id": pid}) is None
        assert db.audit_log.find_one({"action": "user.registration_rejected", "target_id": pid})
        assert s.post(f"{API}/users/{pid}/rifiuta").status_code == 404

    def test_existing_user_without_field_not_pending(self, env):
        s, _ = _login(SA_EMAIL, SA_PWD)
        r = s.post(f"{API}/users/{env['ids']['isc']}/approva")
        assert r.status_code == 404

    def test_get_users_exposes_stato(self, env):
        pid = _mk_user(f"test_pendlist_{TAG}@test.it", ["iscritto"], A22, "in_attesa")
        s, _ = _login(SA_EMAIL, SA_PWD)
        users = s.get(f"{API}/users").json()
        found = [u for u in users if u["id"] == pid]
        assert found and found[0]["stato_approvazione"] == "in_attesa"
        assert all("password_hash" not in u for u in users)

    def test_invalid_object_id(self, env):
        s, _ = _login(SA_EMAIL, SA_PWD)
        r = s.post(f"{API}/users/not-an-id/approva")
        assert r.status_code in (400, 404, 422), f"got {r.status_code}"


# --- Sessione: disabled / in_attesa con cookie valido ---
class TestSessionGuards:
    def test_disabled_user_cookie_rejected(self, env):
        e = f"test_dis_{TAG}@test.it"
        uid = _mk_user(e, ["iscritto"], A22)
        s, lr = _login(e)
        assert lr.status_code == 200
        assert s.get(f"{API}/auth/me").status_code == 200
        db.users.update_one({"_id": ObjectId(uid)}, {"$set": {"disabled": True}})
        assert s.get(f"{API}/auth/me").status_code == 401
        assert s.post(f"{API}/auth/refresh").status_code == 401

    def test_pending_user_cookie_rejected(self, env):
        e = f"test_pendsess_{TAG}@test.it"
        uid = _mk_user(e, ["iscritto"], A22)
        s, lr = _login(e)
        assert lr.status_code == 200
        assert s.post(f"{API}/auth/refresh").status_code == 200
        db.users.update_one({"_id": ObjectId(uid)}, {"$set": {"stato_approvazione": "in_attesa"}})
        assert s.get(f"{API}/auth/me").status_code == 401
        assert s.post(f"{API}/auth/refresh").status_code == 401

    def test_bcrypt_and_cookie_flags(self, env):
        assert db.users.find_one({"email": SA_EMAIL})["password_hash"].startswith("$2b$")
        _, lr = _login(SA_EMAIL, SA_PWD)
        sc = lr.headers.get("set-cookie", "").lower()
        assert "httponly" in sc and "secure" in sc
