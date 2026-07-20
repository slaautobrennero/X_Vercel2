"""
Backend tests for Portale SLA v0.11.4-beta.

Focus: verify the P0 fix for slowapi crash on POST /api/calcola-km and
POST /api/users/{id}/reset-password, plus the new /api/health endpoint.

RCA of the bug being fixed:
- @limiter.limit("60/hour") requires a `response: Response` parameter in the
  endpoint signature so slowapi can inject X-RateLimit-* headers.
- Missing parameter caused: `parameter response must be an instance of
  starlette.responses.Response` → HTTP 500 AFTER Google Maps had already
  returned 200 (=> requests silently consumed quota and users saw a crash).

We CANNOT rely on Google Maps returning OK in the sandbox (dummy key).
Instead we assert:
- No more 500 with the slowapi crash message
- Either 400 (REQUEST_DENIED from Google) or 500 (dummy key missing) or 429
  is the ONLY acceptable outcome — critically NOT the old slowapi crash text.
- X-RateLimit-* headers are present (proof slowapi injection worked).

Non-regression is also verified against login/me/sedi/rimborsi/notifiche.
"""
import os
from datetime import datetime, timezone

import pytest
import requests
from bson import ObjectId
from pymongo import MongoClient

# --- BASE URL from env (must be PROTECTED variable — no default) ---
BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
if not BASE_URL:
    with open("/app/frontend/.env") as f:
        for line in f:
            if line.startswith("REACT_APP_BACKEND_URL"):
                BASE_URL = line.split("=", 1)[1].strip().strip('"').rstrip("/")
                break
API = f"{BASE_URL}/api"

ADMIN_EMAIL = "superadmin@sla.it"
ADMIN_PASSWORD = "SlaAdmin2024!"

DB_NAME = "sla_sindacato"


# --- Helpers ---
def _mongo():
    return MongoClient("mongodb://localhost:27017")[DB_NAME]


# --- Fixtures ---
@pytest.fixture(scope="module")
def session():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


@pytest.fixture(scope="module")
def admin_session(session):
    r = session.post(f"{API}/auth/login",
                     json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    assert r.status_code == 200, f"Admin login failed: {r.status_code} {r.text}"
    return session


@pytest.fixture(scope="module")
def target_user_id():
    """Create an ephemeral user used as target for admin reset-password."""
    db = _mongo()
    # Cleanup any pre-existing test user
    db.users.delete_many({"email": "test_v0114_target@example.com"})
    uid = db.users.insert_one({
        "email": "test_v0114_target@example.com",
        "password_hash": "$2b$12$placeholder_hash_only_for_test_needsxxxxx",
        "nome": "V0114",
        "cognome": "Target",
        "ruoli": ["iscritto"],
        "sede_id": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }).inserted_id
    yield str(uid)
    db.users.delete_one({"_id": uid})


# ==================== Public endpoints ====================


# --- Version & release name (fix release marker) ---
class TestVersion:
    def test_version_bumped_to_0_11_4(self, session):
        r = session.get(f"{API}/version")
        assert r.status_code == 200
        data = r.json()
        assert data["version"] == "0.11.4-beta", data
        assert "Fix rate limit su calcola-km" in data["release_name"], data


# --- New GET /api/health endpoint ---
class TestHealthEndpoint:
    def test_health_returns_ok_public(self, session):
        # Public: no auth cookie required
        s = requests.Session()
        r = s.get(f"{API}/health")
        assert r.status_code == 200, f"health: {r.status_code} {r.text}"
        data = r.json()
        assert data == {"status": "ok"}, data

    def test_health_is_lightweight(self, session):
        # Response body must be minimal (no DB call → no _id leakage)
        r = session.get(f"{API}/health")
        assert r.status_code == 200
        body = r.text
        assert len(body) < 100, f"health body too big: {body!r}"


# ==================== P0 FIX: /calcola-km slowapi crash ====================


class TestCalcolaKmSlowapiFix:
    """Verifies no HTTP 500 slowapi crash after adding response: Response param."""

    OLD_CRASH_MARKER = "parameter response must be an instance of starlette.responses.Response"

    def test_calcola_km_no_slowapi_crash(self, admin_session):
        r = admin_session.post(
            f"{API}/calcola-km",
            json={"origine": "Roma, IT", "destinazione": "Milano, IT"},
        )
        # Accept: 400 (Google REQUEST_DENIED with dummy key),
        #         500 with 'Google Maps API non configurata' (empty key),
        #         429 (rate-limited from prior tests)
        # REJECT: 500 with slowapi crash marker (the actual P0 bug).
        assert r.status_code in (200, 400, 429, 500), (
            f"Unexpected status: {r.status_code} {r.text}"
        )
        assert self.OLD_CRASH_MARKER not in r.text, (
            f"P0 REGRESSION: slowapi crash still present: {r.text}"
        )
        # If 500, the detail MUST be the configured error, not the slowapi crash
        if r.status_code == 500:
            data = r.json()
            detail = data.get("detail", "")
            assert "Google Maps API non configurata" in detail or "Errore di connessione" in detail, (
                f"Unexpected 500 detail (possible slowapi crash?): {detail}"
            )

    def test_calcola_km_rate_limit_headers_present(self, admin_session):
        """slowapi should inject X-RateLimit-* headers on the RESPONSE.

        NOTE: slowapi only injects headers on non-exception responses (200).
        With the sandbox's dummy Google Maps key, the endpoint returns 400,
        so headers are NOT expected in that case. We validate the FIX by
        checking that the endpoint DOESN'T crash with the old slowapi
        error message. Header injection is proven by the reset-password
        test (which returns 200).

        We still assert that if we happen to get a 200 back, headers are
        injected (best-effort verification).
        """
        r = admin_session.post(
            f"{API}/calcola-km",
            json={"origine": "A", "destinazione": "B"},
        )
        assert self.OLD_CRASH_MARKER not in r.text, (
            f"P0 REGRESSION: slowapi crash still present: {r.text}"
        )
        header_keys_lower = {k.lower() for k in r.headers.keys()}
        if r.status_code == 200:
            has_rl = any(k.startswith("x-ratelimit") for k in header_keys_lower)
            assert has_rl, (
                f"200 OK but missing X-RateLimit-* headers; got: "
                f"{sorted(header_keys_lower)}"
            )


# ==================== P0 FIX: /users/{id}/reset-password slowapi crash ====================


class TestResetPasswordSlowapiFix:
    OLD_CRASH_MARKER = "parameter response must be an instance of starlette.responses.Response"

    def test_reset_password_success(self, admin_session, target_user_id):
        r = admin_session.post(f"{API}/users/{target_user_id}/reset-password")
        assert r.status_code == 200, f"reset-password: {r.status_code} {r.text}"
        assert self.OLD_CRASH_MARKER not in r.text
        data = r.json()
        assert "temporary_password" in data
        assert isinstance(data["temporary_password"], str) and len(data["temporary_password"]) >= 8
        assert data["user_email"] == "test_v0114_target@example.com"
        # Verify DB persisted: must_change_password = True
        db = _mongo()
        u = db.users.find_one({"_id": ObjectId(target_user_id)})
        assert u["must_change_password"] is True
        assert u.get("password_reset_at")
        assert u.get("password_reset_by")

    def test_reset_password_rate_limit_headers_present(self, admin_session, target_user_id):
        r = admin_session.post(f"{API}/users/{target_user_id}/reset-password")
        assert r.status_code in (200, 429), f"{r.status_code} {r.text}"
        assert self.OLD_CRASH_MARKER not in r.text
        header_keys_lower = {k.lower() for k in r.headers.keys()}
        has_rl = any(k.startswith("x-ratelimit") for k in header_keys_lower)
        assert has_rl, (
            f"Expected X-RateLimit-* headers on reset-password response; got: "
            f"{sorted(header_keys_lower)}"
        )


# ==================== Non-regression on core flows ====================


class TestNonRegression:
    def test_auth_me(self, admin_session):
        r = admin_session.get(f"{API}/auth/me")
        assert r.status_code == 200
        data = r.json()
        assert data["email"] == ADMIN_EMAIL
        assert "superadmin" in (data.get("ruoli") or [])

    def test_sedi_list(self, admin_session):
        r = admin_session.get(f"{API}/sedi")
        assert r.status_code == 200
        sedi = r.json()
        assert isinstance(sedi, list)
        assert any(s.get("codice") == "A22" for s in sedi)

    def test_rimborsi_list(self, admin_session):
        r = admin_session.get(f"{API}/rimborsi")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_notifiche_list(self, admin_session):
        r = admin_session.get(f"{API}/notifiche")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_motivi_list(self, admin_session):
        r = admin_session.get(f"{API}/motivi-rimborso")
        assert r.status_code == 200
        motivi = r.json()
        names = {m["nome"] for m in motivi}
        assert {"RSA", "Sede", "Altro"}.issubset(names)

    def test_rimborsi_crud_still_works(self, admin_session):
        """Create → list → update → cleanup."""
        motivi = admin_session.get(f"{API}/motivi-rimborso").json()
        motivo_id = next(m["id"] for m in motivi if m["nome"] == "RSA")
        payload = {
            "data": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "motivo_id": motivo_id,
            "indirizzo_partenza": "TEST_via Roma 1, Milano",
            "indirizzo_partenza_tipo": "manuale",
            "indirizzo_arrivo": "TEST_via Verdi 2, Milano",
            "km_andata": 10.0,
            "andata_ritorno": False,
            "uso_autostrada": False,
            "costo_autostrada": 0,
            "importo_pasti": 0,
            "numero_partecipanti_pasto": 0,
            "note": "TEST_v0114_nonreg",
        }
        r = admin_session.post(f"{API}/rimborsi", json=payload)
        assert r.status_code in (200, 201), f"create rimborso: {r.status_code} {r.text}"
        rid = r.json().get("id")
        assert rid

        r = admin_session.put(f"{API}/rimborsi/{rid}", json={"stato": "approvato"})
        assert r.status_code in (200, 204), f"update rimborso: {r.status_code} {r.text}"

        _mongo().rimborsi.delete_one({"_id": ObjectId(rid)})
