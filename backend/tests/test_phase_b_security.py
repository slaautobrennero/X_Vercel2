"""
Backend tests for Portale SLA v0.11.0-beta — Fase B: Anti Brute-Force.

Covers:
- Version bump to 0.11.0-beta
- CSP header includes hCaptcha domains
- Non-regression on existing flows (auth/me, sedi, motivi, rimborsi CRUD, notifiche)
- hCaptcha "soft" (fail-open when HCAPTCHA_SECRET empty)
- hCaptcha ATTIVO (with test-secret 0x0000...): rejects missing token / accepts test token
- Rate limits: login (10/min), register (3/hour), reset-password (20/hour), calcola-km (60/hour)
- 429 response includes Retry-After header and italian detail

NOTE: slowapi uses get_remote_address; through ingress ALL requests share the same key.
      Tests are ordered so rate-limit-consuming tests run LAST.

Cleanup: DB is cleaned in module setup and after registration tests.
"""
import os
import time
import subprocess
from datetime import datetime, timezone

import pytest
import requests
from pymongo import MongoClient
from bson import ObjectId

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
if not BASE_URL:
    # frontend/.env holds the public URL; read it directly.
    with open("/app/frontend/.env") as f:
        for line in f:
            if line.startswith("REACT_APP_BACKEND_URL"):
                BASE_URL = line.split("=", 1)[1].strip().strip('"').rstrip("/")
                break

ADMIN_EMAIL = "superadmin@sla.it"
ADMIN_PASSWORD = "SlaAdmin2024!"
API = f"{BASE_URL}/api"

TEST_HCAPTCHA_SECRET = "0x0000000000000000000000000000000000000000"
TEST_HCAPTCHA_TOKEN = "10000000-aaaa-bbbb-cccc-000000000001"

DB_NAME = "sla_sindacato"


# ================== Helpers ==================


def _mongo():
    return MongoClient("mongodb://localhost:27017")[DB_NAME]


def _cleanup_test_data():
    db = _mongo()
    db.users.delete_many({"email": {"$regex": "^test_"}})
    db.login_attempts.delete_many({})


def _set_hcaptcha_secret(value: str):
    """Rewrite backend/.env HCAPTCHA_SECRET and restart backend to reload."""
    env_path = "/app/backend/.env"
    with open(env_path) as f:
        lines = f.readlines()
    new_lines = []
    found = False
    for line in lines:
        if line.startswith("HCAPTCHA_SECRET"):
            new_lines.append(f'HCAPTCHA_SECRET="{value}"\n')
            found = True
        else:
            new_lines.append(line)
    if not found:
        new_lines.append(f'HCAPTCHA_SECRET="{value}"\n')
    with open(env_path, "w") as f:
        f.writelines(new_lines)
    subprocess.run(["sudo", "supervisorctl", "restart", "backend"], check=True, capture_output=True)
    # Wait for backend to be ready
    for _ in range(30):
        try:
            r = requests.get(f"{API}/version", timeout=3)
            if r.status_code == 200:
                # Also, rate limiter is now reset (in-memory).
                # Clean login_attempts so no lockout inherits.
                _mongo().login_attempts.delete_many({})
                return
        except Exception:
            pass
        time.sleep(1)
    raise RuntimeError("Backend did not come back up")


# ================== Fixtures ==================


@pytest.fixture(scope="module")
def session():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


@pytest.fixture(scope="module")
def admin_session(session):
    r = session.post(f"{API}/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    assert r.status_code == 200, f"Admin login failed: {r.status_code} {r.text}"
    return session


@pytest.fixture(scope="module", autouse=True)
def _pre_and_post_cleanup():
    _cleanup_test_data()
    yield
    _cleanup_test_data()
    # Ensure secret restored to empty at the very end
    _set_hcaptcha_secret("")


# ================== Basic sanity ==================


class TestVersionAndCSP:
    """Version endpoint + Security headers."""

    def test_version_endpoint(self, session):
        r = session.get(f"{API}/version")
        assert r.status_code == 200
        data = r.json()
        assert data["version"] == "0.11.0-beta"
        assert "release_name" in data

    def test_csp_includes_hcaptcha(self, session):
        r = session.get(f"{API}/version")
        assert r.status_code == 200
        csp = r.headers.get("content-security-policy", "")
        assert "hcaptcha.com" in csp, f"CSP missing hcaptcha.com: {csp}"
        # Verify hCaptcha domains present in critical directives
        for directive_marker in ["script-src", "style-src", "connect-src", "frame-src"]:
            # crude check: after directive we should see hcaptcha
            idx = csp.find(directive_marker)
            assert idx >= 0, f"CSP missing directive {directive_marker}"
            # take substring until next ';'
            end = csp.find(";", idx)
            segment = csp[idx : end if end > 0 else len(csp)]
            assert "hcaptcha.com" in segment, f"{directive_marker} missing hcaptcha.com: {segment}"

    def test_other_security_headers(self, session):
        r = session.get(f"{API}/version")
        assert r.headers.get("x-frame-options") == "DENY"
        assert r.headers.get("x-content-type-options") == "nosniff"
        assert "strict-transport-security" in {k.lower() for k in r.headers.keys()}


# ================== Non-regression on existing flows ==================


class TestNonRegression:
    """Verify existing flows still work after adding rate limiting."""

    def test_admin_login(self, admin_session):
        r = admin_session.get(f"{API}/auth/me")
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["email"] == ADMIN_EMAIL
        assert "superadmin" in (data.get("ruoli") or [])

    def test_sedi_list(self, admin_session):
        r = admin_session.get(f"{API}/sedi")
        assert r.status_code == 200
        sedi = r.json()
        assert isinstance(sedi, list)
        assert any(s.get("codice") == "A22" for s in sedi)

    def test_motivi_list(self, admin_session):
        r = admin_session.get(f"{API}/motivi-rimborso")
        assert r.status_code == 200
        motivi = r.json()
        names = {m["nome"] for m in motivi}
        assert {"RSA", "Sede", "Altro"}.issubset(names)

    def test_notifiche_list(self, admin_session):
        r = admin_session.get(f"{API}/notifiche")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_rimborsi_crud(self, admin_session):
        # Need motivo_id + sede for admin. Admin's sede_id may be None → RimborsoCreate does not require sede.
        motivi = admin_session.get(f"{API}/motivi-rimborso").json()
        motivo_id = next(m["id"] for m in motivi if m["nome"] == "RSA")

        payload = {
            "data": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "motivo_id": motivo_id,
            "indirizzo_partenza": "Via Roma 1, Milano",
            "indirizzo_partenza_tipo": "manuale",
            "indirizzo_arrivo": "Via Verdi 2, Milano",
            "km_andata": 12.5,
            "andata_ritorno": True,
            "uso_autostrada": False,
            "costo_autostrada": 0,
            "importo_pasti": 0,
            "numero_partecipanti_pasto": 0,
            "note": "TEST_regression",
        }
        r = admin_session.post(f"{API}/rimborsi", json=payload)
        assert r.status_code in (200, 201), f"Create rimborso failed: {r.status_code} {r.text}"
        created = r.json()
        rid = created.get("id")
        assert rid, f"Missing id in create response: {created}"

        # GET list
        r = admin_session.get(f"{API}/rimborsi")
        assert r.status_code == 200
        assert any(x.get("id") == rid for x in r.json())

        # PUT update (change stato) — endpoint uses PUT for updates
        r = admin_session.put(f"{API}/rimborsi/{rid}", json={"stato": "approvato"})
        assert r.status_code in (200, 204), f"Update rimborso failed: {r.status_code} {r.text}"

        # Cleanup directly in DB (no DELETE endpoint by design)
        _mongo().rimborsi.delete_one({"_id": ObjectId(rid)})


# ================== hCaptcha DISABLED (default: HCAPTCHA_SECRET empty) ==================


class TestHCaptchaDisabled:
    """When HCAPTCHA_SECRET is empty, registration works without token."""

    def test_register_without_captcha_when_disabled(self, session):
        # Should be enabled default state (empty secret)
        # Ensure secret is empty
        _set_hcaptcha_secret("")
        _cleanup_test_data()
        payload = {
            "email": "test_softdisabled@example.com",
            "password": "TestPass123!",
            "nome": "Soft",
            "cognome": "Disabled",
        }
        r = session.post(f"{API}/auth/register", json=payload)
        assert r.status_code == 200, f"Expected 200 with captcha disabled, got {r.status_code}: {r.text}"
        data = r.json()
        assert data["email"] == "test_softdisabled@example.com"


# ================== hCaptcha ATTIVO (with test secret) ==================


class TestHCaptchaEnabled:
    """When HCAPTCHA_SECRET set, requests without a valid token must fail."""

    @classmethod
    def setup_class(cls):
        _cleanup_test_data()
        _set_hcaptcha_secret(TEST_HCAPTCHA_SECRET)

    @classmethod
    def teardown_class(cls):
        _cleanup_test_data()
        _set_hcaptcha_secret("")

    def test_register_missing_token_rejected(self, session):
        payload = {
            "email": "test_captcha_missing@example.com",
            "password": "TestPass123!",
            "nome": "Missing",
            "cognome": "Token",
        }
        r = session.post(f"{API}/auth/register", json=payload)
        assert r.status_code == 400, f"Expected 400, got {r.status_code}: {r.text}"
        detail = r.json().get("detail", "")
        assert "captcha" in detail.lower(), f"Unexpected detail: {detail}"

    def test_register_with_test_token_succeeds(self, session):
        payload = {
            "email": "test_captcha_ok@example.com",
            "password": "TestPass123!",
            "nome": "Ok",
            "cognome": "Captcha",
            "hcaptcha_token": TEST_HCAPTCHA_TOKEN,
        }
        r = session.post(f"{API}/auth/register", json=payload)
        assert r.status_code == 200, f"Expected 200 with test token, got {r.status_code}: {r.text}"
        data = r.json()
        assert data["email"] == "test_captcha_ok@example.com"


# ================== Rate limits (RUN LAST — consume in-memory counters) ==================


class TestRateLimitLogin:
    """POST /api/auth/login → 10/minute per IP."""

    def test_login_rate_limit(self, session):
        # Fresh session; use a fake email/password (will 401 but limiter counts each request)
        # After 10 requests in a minute the 11th should be 429.
        # BUT this endpoint also has DB-based lockout 5/15min per (ip:email).
        # To disambiguate we use fake but VARYING email addresses so lockout won't kick in
        # (lockout is keyed on identifier = f"{ip}:{email}").
        # We need slowapi 429 (not DB lockout). But slowapi 429 comes from decorator @10/min per IP.
        _mongo().login_attempts.delete_many({})
        codes = []
        for i in range(12):
            r = session.post(
                f"{API}/auth/login",
                json={"email": f"test_rl_login_{i}@example.com", "password": "wrongpw"},
            )
            codes.append(r.status_code)
        # Expect at least one 429 in the last 2 requests
        assert 429 in codes[-3:], f"Expected 429 within last requests; got {codes}"
        # Verify 429 detail italian + Retry-After header
        # Find first 429
        idx = codes.index(429)
        # replay one more to inspect
        r = session.post(
            f"{API}/auth/login",
            json={"email": f"test_rl_login_last@example.com", "password": "wrongpw"},
        )
        if r.status_code == 429:
            assert "Retry-After" in r.headers or "retry-after" in r.headers
            detail = r.json().get("detail", "")
            assert "Troppe" in detail or "richieste" in detail, f"Missing italian detail: {detail}"


class TestRateLimitResetPassword:
    """POST /api/users/{id}/reset-password → 20/hour per IP for authenticated admin."""

    def test_reset_password_rate_limit(self, admin_session):
        # Create a target user to reset
        db = _mongo()
        target_id = str(
            db.users.insert_one(
                {
                    "email": "test_resettarget@example.com",
                    "password_hash": "$2b$12$abcdefghijklmnopqrstuv",  # invalid but present
                    "nome": "Reset",
                    "cognome": "Target",
                    "ruoli": ["iscritto"],
                    "sede_id": None,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                }
            ).inserted_id
        )

        codes = []
        for _ in range(22):
            r = admin_session.post(f"{API}/users/{target_id}/reset-password")
            codes.append(r.status_code)
        # First 20 should be 200; then 429
        successes = sum(1 for c in codes if c == 200)
        rate_limited = sum(1 for c in codes if c == 429)
        assert successes <= 20, f"Expected <=20 successes, got {successes} in codes {codes}"
        assert rate_limited >= 1, f"Expected >=1 429, got {codes}"


class TestRateLimitCalcolaKm:
    """POST /api/calcola-km → 60/hour per IP for authenticated user."""

    def test_calcola_km_rate_limit(self, admin_session):
        # We just verify the decorator kicks in around request 61. To avoid burning Google Maps
        # quota, we send obviously bad payloads that still count against the limit.
        # Google Maps returns non-OK for these → 400 from endpoint, but slowapi counts them.
        codes = []
        for _ in range(62):
            r = admin_session.post(
                f"{API}/calcola-km",
                json={"origine": "xxxxxxxxx_invalid", "destinazione": "yyyyyyyyy_invalid"},
            )
            codes.append(r.status_code)
            if r.status_code == 429:
                break
        assert 429 in codes, f"Expected 429 within 62 requests, got last codes {codes[-5:]}"


class TestRateLimitRegister:
    """POST /api/auth/register → 3/hour per IP."""

    def test_register_rate_limit(self, session):
        # Fresh state: reset backend to clear in-memory counters
        _set_hcaptcha_secret("")  # keep captcha off so we can test purely the rate limit
        _cleanup_test_data()
        codes = []
        for i in range(5):
            payload = {
                "email": f"test_rlreg_{i}@example.com",
                "password": "TestPass123!",
                "nome": "RL",
                "cognome": "Reg",
            }
            r = session.post(f"{API}/auth/register", json=payload)
            codes.append(r.status_code)
        # Expect at most 3 successes (200), remaining 429
        successes = sum(1 for c in codes if c == 200)
        rate_limited = sum(1 for c in codes if c == 429)
        assert successes <= 3, f"Expected <=3 successes, got {successes}. codes={codes}"
        assert rate_limited >= 1, f"Expected >=1 429, got codes={codes}"
