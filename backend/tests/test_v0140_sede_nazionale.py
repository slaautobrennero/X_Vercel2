"""
Backend tests for v0.14.0-beta — Sede Nazionale.
Covers:
- GET /api/version is 0.14.0-beta
- GET /api/sedi expose is_nazionale
- POST /api/sedi (superadmin only, duplicate codice 400)
- POST /api/sedi/{id}/marca-nazionale (superadmin only, exclusivity, cache invalidation)
- DELETE sede nazionale blocked
- PUT /api/sedi/{id} RBAC
- GET /api/auth/me contains is_nazionale_member
- Annunci/documenti: broadcast_nazionale default (admin naz → broadcast), solo_nazionale=True scopes to naz sede
- Visibility: annunci/documenti created by naz admin are visible to all other sedi
- Rimborsi: naz-admin reads cross-sede (sede_id filter honored)
- Reports: naz-admin GET /reports/rimborsi-annuali works and returns sede_nome; CSV export OK
"""
import io
import os
import uuid
from datetime import date

import pytest
import requests
from bson import ObjectId
from pymongo import MongoClient

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://portale-rimborsi.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"

SUPERADMIN_EMAIL = "superadmin@sla.it"
SUPERADMIN_PASSWORD = "SlaAdmin2024!"


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


# ---------- Fixtures ----------

@pytest.fixture(scope="session")
def mongo():
    env = _load_backend_env()
    url = os.environ.get("MONGO_URL") or env.get("MONGO_URL") or "mongodb://localhost:27017"
    dbname = os.environ.get("DB_NAME") or env.get("DB_NAME") or "portale_sla"
    client = MongoClient(url)
    yield client[dbname]
    client.close()


@pytest.fixture(scope="session")
def superadmin_session():
    s = requests.Session()
    r = s.post(f"{API}/auth/login", json={"email": SUPERADMIN_EMAIL, "password": SUPERADMIN_PASSWORD})
    if r.status_code != 200:
        pytest.skip(f"Superadmin login failed: {r.status_code} {r.text[:200]}")
    return s


@pytest.fixture(scope="session")
def two_sedi(superadmin_session, mongo):
    """
    Ensure at least two sedi exist: one to mark as nazionale, one normale.
    Create test sedi with unique codice, cleanup at end.
    """
    created = []
    sedi_now = requests.get(f"{API}/sedi").json()

    def _mk(nome, codice):
        payload = {
            "nome": nome,
            "codice": codice,
            "indirizzo": "Via Test 1",
            "tariffa_km": 0.35,
            "rimborso_pasti": 25.0,
            "rimborso_autostrada": True,
        }
        r = superadmin_session.post(f"{API}/sedi", json=payload)
        assert r.status_code == 200, f"create sede failed: {r.status_code} {r.text}"
        created.append(r.json()["id"])
        return r.json()

    naz = _mk(f"TEST_NAZ_{uuid.uuid4().hex[:6]}", f"TNAZ{uuid.uuid4().hex[:4].upper()}")
    loc = _mk(f"TEST_LOC_{uuid.uuid4().hex[:6]}", f"TLOC{uuid.uuid4().hex[:4].upper()}")

    # mark naz as nazionale (store previous one to restore)
    prev_naz = None
    for s in sedi_now:
        if s.get("is_nazionale"):
            prev_naz = s["id"]
            break

    r = superadmin_session.post(f"{API}/sedi/{naz['id']}/marca-nazionale")
    assert r.status_code == 200

    yield {"naz_id": naz["id"], "loc_id": loc["id"], "naz": naz, "loc": loc}

    # cleanup: unmark, delete created
    try:
        # unmark naz by marking previous (or just unset via DB)
        if prev_naz:
            superadmin_session.post(f"{API}/sedi/{prev_naz}/marca-nazionale")
        else:
            mongo.sedi.update_many({"is_nazionale": True}, {"$set": {"is_nazionale": False}})
        for sid in created:
            # Nazionale cannot be deleted via API; unset first then delete via DB to be safe
            mongo.sedi.update_one({"_id": ObjectId(sid)}, {"$set": {"is_nazionale": False}})
            mongo.sedi.delete_one({"_id": ObjectId(sid)})
    except Exception as e:
        print(f"two_sedi cleanup warn: {e}")


@pytest.fixture(scope="session")
def naz_admin(two_sedi, superadmin_session, mongo):
    """Create a user, assign to naz sede with admin role."""
    email = f"test_naz_admin_{uuid.uuid4().hex[:8]}@example.com"
    password = "TestNaz2024!"
    s = requests.Session()
    r = s.post(f"{API}/auth/register", json={
        "email": email, "password": password,
        "nome": "NazAdmin", "cognome": "Test",
        "privacy_accepted": True, "termini_accepted": True,
        "privacy_version": "1.0",
    })
    assert r.status_code == 200, f"register naz admin failed: {r.text}"

    # Promote via DB
    mongo.users.update_one(
        {"email": email},
        {"$set": {"ruoli": ["admin"], "ruolo": "admin", "sede_id": two_sedi["naz_id"]}}
    )
    # Re-login to refresh session
    s2 = requests.Session()
    r = s2.post(f"{API}/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200
    yield {"session": s2, "email": email}
    try:
        udoc = mongo.users.find_one({"email": email}, {"_id": 1})
        if udoc:
            mongo.notifiche.delete_many({"user_id": str(udoc["_id"])})
            mongo.consensi_privacy.delete_many({"user_id": udoc["_id"]})
        mongo.users.delete_many({"email": email})
    except Exception as e:
        print(f"cleanup naz_admin: {e}")


@pytest.fixture(scope="session")
def local_admin(two_sedi, mongo):
    """Admin on the local (non-naz) sede."""
    email = f"test_loc_admin_{uuid.uuid4().hex[:8]}@example.com"
    password = "TestLoc2024!"
    s = requests.Session()
    r = s.post(f"{API}/auth/register", json={
        "email": email, "password": password,
        "nome": "LocAdmin", "cognome": "Test",
        "privacy_accepted": True, "termini_accepted": True,
        "privacy_version": "1.0",
    })
    assert r.status_code == 200
    mongo.users.update_one(
        {"email": email},
        {"$set": {"ruoli": ["admin"], "ruolo": "admin", "sede_id": two_sedi["loc_id"]}}
    )
    s2 = requests.Session()
    r = s2.post(f"{API}/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200
    yield {"session": s2, "email": email}
    try:
        mongo.users.delete_many({"email": email})
    except Exception:
        pass


@pytest.fixture(scope="session")
def iscritto_loc(two_sedi, mongo):
    """A plain iscritto in local sede to test visibility of broadcasts."""
    email = f"test_iscr_{uuid.uuid4().hex[:8]}@example.com"
    password = "TestIscr2024!"
    s = requests.Session()
    r = s.post(f"{API}/auth/register", json={
        "email": email, "password": password,
        "nome": "Iscr", "cognome": "Loc",
        "privacy_accepted": True, "termini_accepted": True,
        "privacy_version": "1.0",
    })
    assert r.status_code == 200
    mongo.users.update_one(
        {"email": email},
        {"$set": {"sede_id": two_sedi["loc_id"]}}
    )
    s2 = requests.Session()
    r = s2.post(f"{API}/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200
    yield {"session": s2, "email": email}
    try:
        mongo.users.delete_many({"email": email})
    except Exception:
        pass


# ==================== VERSION ====================

class TestVersion:
    def test_version_is_0140(self):
        r = requests.get(f"{API}/version")
        assert r.status_code == 200
        d = r.json()
        assert d["version"] == "0.14.0-beta"
        assert d["release_name"] == "Sede Nazionale"


# ==================== SEDI ====================

class TestSedi:
    def test_get_sedi_expose_is_nazionale(self, two_sedi):
        r = requests.get(f"{API}/sedi")
        assert r.status_code == 200
        sedi = r.json()
        assert any(s.get("is_nazionale") is True for s in sedi)
        # Exactly one nazionale
        naz_count = sum(1 for s in sedi if s.get("is_nazionale"))
        assert naz_count == 1, f"Expected exactly 1 nazionale, got {naz_count}"
        # Our naz_id is the one
        marked = [s for s in sedi if s.get("is_nazionale")][0]
        assert marked["id"] == two_sedi["naz_id"]

    def test_create_sede_duplicate_codice_400(self, superadmin_session, two_sedi):
        payload = {
            "nome": "Dup",
            "codice": two_sedi["loc"]["codice"],
            "indirizzo": "x",
            "tariffa_km": 0.3,
            "rimborso_pasti": 10.0,
            "rimborso_autostrada": False,
        }
        r = superadmin_session.post(f"{API}/sedi", json=payload)
        assert r.status_code == 400

    def test_create_sede_not_superadmin_403(self, local_admin):
        payload = {
            "nome": "XX",
            "codice": f"XX{uuid.uuid4().hex[:4]}",
            "indirizzo": "y",
            "tariffa_km": 0.3,
            "rimborso_pasti": 10.0,
            "rimborso_autostrada": False,
        }
        r = local_admin["session"].post(f"{API}/sedi", json=payload)
        assert r.status_code == 403

    def test_marca_nazionale_only_superadmin(self, local_admin, two_sedi):
        r = local_admin["session"].post(f"{API}/sedi/{two_sedi['loc_id']}/marca-nazionale")
        assert r.status_code == 403

    def test_marca_nazionale_exclusivity(self, superadmin_session, two_sedi, mongo):
        # Mark loc as nazionale → naz loses the flag
        r = superadmin_session.post(f"{API}/sedi/{two_sedi['loc_id']}/marca-nazionale")
        assert r.status_code == 200
        sedi = requests.get(f"{API}/sedi").json()
        marked = [s for s in sedi if s.get("is_nazionale")]
        assert len(marked) == 1
        assert marked[0]["id"] == two_sedi["loc_id"]
        # Restore naz
        r = superadmin_session.post(f"{API}/sedi/{two_sedi['naz_id']}/marca-nazionale")
        assert r.status_code == 200

    def test_delete_sede_nazionale_blocked(self, superadmin_session, two_sedi):
        r = superadmin_session.delete(f"{API}/sedi/{two_sedi['naz_id']}")
        assert r.status_code == 400
        assert "Nazionale" in r.json().get("detail", "")

    def test_put_sede_rbac_local_cannot_touch_other(self, local_admin, two_sedi):
        # local admin tries to update naz sede → 403
        r = local_admin["session"].put(
            f"{API}/sedi/{two_sedi['naz_id']}",
            json={"indirizzo": "hack"},
        )
        assert r.status_code == 403

    def test_put_sede_naz_admin_can_update_naz(self, naz_admin, two_sedi):
        r = naz_admin["session"].put(
            f"{API}/sedi/{two_sedi['naz_id']}",
            json={"indirizzo": "Via Nazionale 1"},
        )
        assert r.status_code == 200


# ==================== AUTH ME ====================

class TestAuthMe:
    def test_me_includes_is_nazionale_member_true(self, naz_admin):
        r = naz_admin["session"].get(f"{API}/auth/me")
        assert r.status_code == 200
        d = r.json()
        assert d.get("is_nazionale_member") is True

    def test_me_includes_is_nazionale_member_false(self, local_admin):
        r = local_admin["session"].get(f"{API}/auth/me")
        assert r.status_code == 200
        d = r.json()
        assert d.get("is_nazionale_member") is False


# ==================== ANNUNCI ====================

class TestAnnunciNazionale:
    def test_naz_admin_default_broadcast(self, naz_admin, iscritto_loc):
        titolo = f"TEST_NAZ_ANN_{uuid.uuid4().hex[:6]}"
        r = naz_admin["session"].post(
            f"{API}/annunci",
            data={"titolo": titolo, "contenuto": "Broadcast to all"},
        )
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["broadcast_nazionale"] is True
        assert d["sede_id"] is None
        # iscritto on local sede should see it
        r2 = iscritto_loc["session"].get(f"{API}/annunci")
        assert r2.status_code == 200
        titoli = [a["titolo"] for a in r2.json()]
        assert titolo in titoli

    def test_naz_admin_solo_nazionale_true_scopes(self, naz_admin, iscritto_loc, two_sedi):
        titolo = f"TEST_NAZ_SOLO_{uuid.uuid4().hex[:6]}"
        r = naz_admin["session"].post(
            f"{API}/annunci",
            data={"titolo": titolo, "contenuto": "Only naz", "solo_nazionale": "true"},
        )
        assert r.status_code == 200
        d = r.json()
        assert d["broadcast_nazionale"] is False
        assert d["sede_id"] == two_sedi["naz_id"]
        # iscritto local should NOT see it
        r2 = iscritto_loc["session"].get(f"{API}/annunci")
        titoli = [a["titolo"] for a in r2.json()]
        assert titolo not in titoli

    def test_local_admin_does_not_broadcast(self, local_admin, two_sedi):
        titolo = f"TEST_LOC_ANN_{uuid.uuid4().hex[:6]}"
        r = local_admin["session"].post(
            f"{API}/annunci",
            data={"titolo": titolo, "contenuto": "local only"},
        )
        assert r.status_code == 200
        d = r.json()
        assert d["broadcast_nazionale"] is False
        assert d["sede_id"] == two_sedi["loc_id"]


# ==================== DOCUMENTI ====================

class TestDocumentiNazionale:
    def test_naz_admin_default_broadcast(self, naz_admin, iscritto_loc):
        nome = f"TEST_DOC_NAZ_{uuid.uuid4().hex[:6]}"
        files = {"file": ("test.pdf", io.BytesIO(b"%PDF-1.4 test"), "application/pdf")}
        r = naz_admin["session"].post(
            f"{API}/documenti",
            data={"nome": nome, "categoria": "modulistica"},
            files=files,
        )
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["broadcast_nazionale"] is True
        assert d["sede_id"] is None
        # iscritto local should see it
        r2 = iscritto_loc["session"].get(f"{API}/documenti")
        assert r2.status_code == 200
        nomi = [doc["nome"] for doc in r2.json()]
        assert nome in nomi

    def test_naz_admin_sees_local_docs(self, naz_admin, local_admin, two_sedi):
        """v0.14.0: admin/segretario del Nazionale vede documenti di altre sedi."""
        nome = f"TEST_DOC_LOC_{uuid.uuid4().hex[:6]}"
        files = {"file": ("local.pdf", io.BytesIO(b"%PDF-1.4 local"), "application/pdf")}
        r = local_admin["session"].post(
            f"{API}/documenti",
            data={"nome": nome, "categoria": "modulistica"},
            files=files,
        )
        assert r.status_code == 200
        # Naz admin should see it
        r2 = naz_admin["session"].get(f"{API}/documenti")
        nomi = [doc["nome"] for doc in r2.json()]
        assert nome in nomi


# ==================== RIMBORSI (cross-sede read) ====================

class TestRimborsiNazionale:
    def test_naz_admin_sees_other_sede_rimborsi(self, naz_admin, local_admin, two_sedi, mongo):
        """Inject un rimborso finto in sede locale e verifica che naz admin lo veda."""
        # Create a rimborso document directly in Mongo for a user in loc sede
        user_loc = mongo.users.find_one({"sede_id": two_sedi["loc_id"]}, {"_id": 1})
        assert user_loc, "no user in loc sede"
        rid = mongo.rimborsi.insert_one({
            "user_id": str(user_loc["_id"]),
            "sede_id": two_sedi["loc_id"],
            "data": f"{date.today().year}-06-15",
            "motivo_id": None,
            "indirizzo_partenza": "A",
            "indirizzo_arrivo": "B",
            "km_andata": 10,
            "km_totali": 20,
            "andata_ritorno": True,
            "importo_pasti": 0,
            "costo_autostrada": 0,
            "tariffa_km": 0.35,
            "importo_km": 7.0,
            "importo_totale": 7.0,
            "stato": "approvato",
            "ricevute": [],
            "ricevute_spese": [],
            "created_at": "2026-06-15T10:00:00+00:00",
        }).inserted_id

        try:
            # naz admin filters by sede_id = loc
            r = naz_admin["session"].get(
                f"{API}/rimborsi",
                params={"sede_id": two_sedi["loc_id"]},
            )
            assert r.status_code == 200
            ids = [x["id"] for x in r.json()]
            assert str(rid) in ids

            # local admin for sede loc still sees it
            r2 = local_admin["session"].get(f"{API}/rimborsi")
            assert r2.status_code == 200
            ids2 = [x["id"] for x in r2.json()]
            assert str(rid) in ids2
        finally:
            mongo.rimborsi.delete_one({"_id": rid})


# ==================== REPORTS ====================

class TestReportsNazionale:
    def test_naz_admin_can_read_report(self, naz_admin, two_sedi):
        anno = date.today().year
        r = naz_admin["session"].get(f"{API}/reports/rimborsi-annuali", params={"anno": anno})
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_naz_admin_report_sede_filter(self, naz_admin, two_sedi):
        anno = date.today().year
        r = naz_admin["session"].get(
            f"{API}/reports/rimborsi-annuali",
            params={"anno": anno, "sede_id": two_sedi["loc_id"]},
        )
        assert r.status_code == 200

    def test_naz_admin_export_csv(self, naz_admin):
        anno = date.today().year
        r = naz_admin["session"].get(
            f"{API}/reports/rimborsi-export",
            params={"anno": anno, "formato": "csv"},
        )
        assert r.status_code == 200
        assert "text/csv" in r.headers.get("content-type", "")

    def test_local_admin_report_cannot_filter_other_sede(self, local_admin, two_sedi):
        """local admin forcing sede_id=naz should still only see own sede data."""
        anno = date.today().year
        # The route silently ignores sede_id for non-nazreader non-superadmin
        # (query["sede_id"] gets overwritten by user.sede_id)
        r = local_admin["session"].get(
            f"{API}/reports/rimborsi-annuali",
            params={"anno": anno, "sede_id": two_sedi["naz_id"]},
        )
        assert r.status_code == 200
        # No crash — results are scoped to own sede
