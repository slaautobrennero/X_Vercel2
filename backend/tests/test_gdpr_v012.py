"""
Backend tests for v0.12.0-beta GDPR compliance MVP.
Covers: impostazioni-sindacato, privacy/cookie/termini, versioni-documenti,
register consent, gdpr/my-data, cancellazione lifecycle, registro-trattamenti, RBAC.
"""
import os
import time
import uuid
import pytest
import requests
from pymongo import MongoClient

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://portale-rimborsi.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"

SUPERADMIN_EMAIL = "superadmin@sla.it"
SUPERADMIN_PASSWORD = "SlaAdmin2024!"

MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "portale_sla")


# ---------- Fixtures ----------

def _load_backend_env():
    env = {}
    try:
        with open("/app/backend/.env") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip().strip('"').strip("'")
    except Exception:
        pass
    return env


@pytest.fixture(scope="session")
def mongo():
    env = _load_backend_env()
    url = os.environ.get("MONGO_URL") or env.get("MONGO_URL") or MONGO_URL
    dbname = os.environ.get("DB_NAME") or env.get("DB_NAME") or DB_NAME
    client = MongoClient(url)
    yield client[dbname]
    client.close()


@pytest.fixture(scope="session")
def cleanup(mongo):
    """Cleanup test_gdpr_* users and related data before + after."""
    def _clean():
        emails = [u["email"] for u in mongo.users.find({"email": {"$regex": "^test_gdpr_"}}, {"email": 1})]
        if emails:
            uids = [u["_id"] for u in mongo.users.find({"email": {"$in": emails}}, {"_id": 1})]
            mongo.consensi_privacy.delete_many({"email": {"$in": emails}})
            mongo.richieste_cancellazione.delete_many({"user_id": {"$in": uids}})
            mongo.users.delete_many({"email": {"$in": emails}})
    _clean()
    yield
    _clean()


@pytest.fixture(scope="session")
def superadmin_session():
    s = requests.Session()
    r = s.post(f"{API}/auth/login", json={"email": SUPERADMIN_EMAIL, "password": SUPERADMIN_PASSWORD})
    if r.status_code != 200:
        pytest.skip(f"Superadmin login failed: {r.status_code} {r.text[:200]}")
    return s


@pytest.fixture(scope="session")
def test_user(cleanup):
    """Create a fresh non-admin user via /auth/register and return (session, email, uid)."""
    email = f"test_gdpr_user_{uuid.uuid4().hex[:8]}@example.com"
    password = "TestPassGdpr2024!"
    s = requests.Session()
    r = s.post(f"{API}/auth/register", json={
        "email": email, "password": password,
        "nome": "Test", "cognome": "Gdpr",
        "privacy_accepted": True, "termini_accepted": True,
        "privacy_version": "1.0",
    })
    assert r.status_code == 200, f"Register failed: {r.status_code} {r.text}"
    # cookies set on session already, so subsequent requests will be authenticated
    return {"session": s, "email": email, "password": password}


# ---------- Public/Legal Endpoints ----------

class TestImpostazioniSindacato:
    def test_public_get_returns_correct_data(self):
        r = requests.get(f"{API}/impostazioni-sindacato")
        assert r.status_code == 200
        data = r.json()
        assert data["denominazione"] == "SLA - CISAL"
        assert "Via Arpinati 22/1" in data["sede_legale"]
        assert data["codice_fiscale"] == "91027960102"

    def test_put_requires_superadmin(self, test_user):
        r = test_user["session"].put(f"{API}/impostazioni-sindacato", json={
            "denominazione": "HACK", "sede_legale": "x", "codice_fiscale": "0",
            "pec": "", "email_privacy": "", "sito_web": "", "foro_competente": "Roma"
        })
        assert r.status_code == 403

    def test_put_superadmin_updates(self, superadmin_session):
        # Read current, modify, restore
        cur = requests.get(f"{API}/impostazioni-sindacato").json()
        payload = {
            "denominazione": cur["denominazione"],
            "sede_legale": cur["sede_legale"],
            "codice_fiscale": cur["codice_fiscale"],
            "partita_iva": cur.get("partita_iva"),
            "pec": cur.get("pec", ""),
            "email_privacy": cur.get("email_privacy", ""),
            "sito_web": cur.get("sito_web", ""),
            "dpo_nome": cur.get("dpo_nome"),
            "dpo_email": cur.get("dpo_email"),
            "foro_competente": cur.get("foro_competente", "Genova"),
        }
        r = superadmin_session.put(f"{API}/impostazioni-sindacato", json=payload)
        assert r.status_code == 200, r.text
        assert r.json().get("ok") is True


class TestLegalDocuments:
    def test_privacy(self):
        r = requests.get(f"{API}/privacy")
        assert r.status_code == 200
        d = r.json()
        assert d["version"] == "1.0"
        c = d["contenuto"]
        assert "SLA - CISAL" in c
        assert "Titolare del trattamento" in c
        assert "Diritti dell'interessato" in c

    def test_cookie_policy(self):
        r = requests.get(f"{API}/cookie-policy")
        assert r.status_code == 200
        assert r.json()["version"] == "1.0"

    def test_termini(self):
        r = requests.get(f"{API}/termini")
        assert r.status_code == 200
        assert r.json()["version"] == "1.0"

    def test_versioni_documenti(self):
        r = requests.get(f"{API}/versioni-documenti")
        assert r.status_code == 200
        d = r.json()
        assert d["privacy_version"] == "1.0"
        assert d["cookie_version"] == "1.0"
        assert d["termini_version"] == "1.0"


# ---------- Registration consent ----------

class TestRegisterConsent:
    def test_register_without_privacy_fails(self, cleanup):
        email = f"test_gdpr_noconsent_{uuid.uuid4().hex[:6]}@example.com"
        r = requests.post(f"{API}/auth/register", json={
            "email": email, "password": "TestPassGdpr2024!",
            "nome": "N", "cognome": "C",
            "privacy_accepted": False, "termini_accepted": True,
        })
        assert r.status_code == 400
        assert "Privacy" in r.json().get("detail", "") or "privacy" in r.json().get("detail", "").lower()

    def test_register_without_termini_fails(self, cleanup):
        email = f"test_gdpr_noterm_{uuid.uuid4().hex[:6]}@example.com"
        r = requests.post(f"{API}/auth/register", json={
            "email": email, "password": "TestPassGdpr2024!",
            "nome": "N", "cognome": "C",
            "privacy_accepted": True, "termini_accepted": False,
        })
        assert r.status_code == 400

    def test_register_with_both_creates_consenso(self, mongo, cleanup):
        email = f"test_gdpr_ok_{uuid.uuid4().hex[:6]}@example.com"
        r = requests.post(f"{API}/auth/register", json={
            "email": email, "password": "TestPassGdpr2024!",
            "nome": "N", "cognome": "C",
            "privacy_accepted": True, "termini_accepted": True,
            "privacy_version": "1.0",
        })
        assert r.status_code == 200, r.text
        # Verify consenso_privacy record
        rec = mongo.consensi_privacy.find_one({"email": email})
        assert rec is not None
        assert rec["privacy_accepted"] is True
        assert rec["termini_accepted"] is True
        assert rec["privacy_version"] == "1.0"


# ---------- GDPR interessato rights ----------

class TestGdprMyData:
    def test_my_data_returns_all(self, test_user):
        r = test_user["session"].get(f"{API}/gdpr/my-data")
        assert r.status_code == 200, r.text
        d = r.json()
        assert "anagrafica" in d
        assert "rimborsi" in d
        assert "consensi_privacy" in d
        assert d["anagrafica"]["email"] == test_user["email"]
        # user's consenso from register should be present
        assert len(d["consensi_privacy"]) >= 1

    def test_my_data_requires_auth(self):
        r = requests.get(f"{API}/gdpr/my-data")
        assert r.status_code in (401, 403)


class TestCancellazioneLifecycle:
    def test_full_lifecycle(self, test_user, mongo):
        s = test_user["session"]
        # Ensure clean state
        mongo.richieste_cancellazione.delete_many({"email": test_user["email"]})

        # Initial stato
        r = s.get(f"{API}/gdpr/stato-cancellazione")
        assert r.status_code == 200 and r.json()["pending"] is False

        # Richiedi
        r = s.post(f"{API}/gdpr/richiedi-cancellazione", json={"motivo": "test"})
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["ok"] is True
        assert "esecuzione_prevista" in d

        # Second time -> 400
        r2 = s.post(f"{API}/gdpr/richiedi-cancellazione", json={"motivo": "again"})
        assert r2.status_code == 400

        # Stato pending true
        r = s.get(f"{API}/gdpr/stato-cancellazione")
        assert r.status_code == 200
        st = r.json()
        assert st["pending"] is True
        assert 28 <= st["giorni_residui"] <= 30

        # Annulla
        r = s.post(f"{API}/gdpr/annulla-cancellazione")
        assert r.status_code == 200

        # Stato pending false
        r = s.get(f"{API}/gdpr/stato-cancellazione")
        assert r.status_code == 200 and r.json()["pending"] is False

        # Annulla again -> 404
        r = s.post(f"{API}/gdpr/annulla-cancellazione")
        assert r.status_code == 404


# ---------- Registro trattamenti (superadmin) ----------

class TestRegistroTrattamenti:
    def test_superadmin_ok(self, superadmin_session):
        r = superadmin_session.get(f"{API}/gdpr/registro-trattamenti")
        assert r.status_code == 200
        d = r.json()
        assert "trattamenti" in d
        assert len(d["trattamenti"]) == 4
        assert "titolare" in d

    def test_non_superadmin_forbidden(self, test_user):
        r = test_user["session"].get(f"{API}/gdpr/registro-trattamenti")
        assert r.status_code == 403


# ---------- Version ----------

class TestVersion:
    def test_version(self):
        r = requests.get(f"{API}/version")
        assert r.status_code == 200
        d = r.json()
        assert d["version"] == "0.12.0-beta"
        assert "GDPR" in d.get("release_name", "")


# ---------- Non regression ----------

class TestNonRegression:
    def test_login_me(self, superadmin_session):
        r = superadmin_session.get(f"{API}/auth/me")
        assert r.status_code == 200
        assert r.json()["email"] == SUPERADMIN_EMAIL

    def test_rimborsi_list(self, superadmin_session):
        r = superadmin_session.get(f"{API}/rimborsi")
        assert r.status_code == 200

    def test_sedi(self, superadmin_session):
        r = superadmin_session.get(f"{API}/sedi")
        assert r.status_code == 200

    def test_notifiche(self, superadmin_session):
        r = superadmin_session.get(f"{API}/notifiche")
        assert r.status_code == 200
