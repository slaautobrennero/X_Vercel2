"""
Backend tests for Portale SLA v0.11.3-beta — Fix load .env: no override + secrets fuori dal repo.

Covers:
- load_dotenv(override=False) in core/config.py and utils/config.py
  - env var pre-set in os.environ takes precedence over .env file value
  - env var absent → .env file value is used
- /api/version returns 0.11.3-beta and release_name includes "Fix load .env"
- POST /api/calcola-km error handling:
  - empty key → 500 "Google Maps API non configurata"
  - invalid key → 400 with detail containing Google status (REQUEST_DENIED)
- Rate limit /api/calcola-km still 60/hour (smoke check after fresh restart)
- Non-regression: login, /auth/me, /sedi, /rimborsi, /notifiche

The .env file is restored to its original state in the module teardown.
"""
import os
import sys
import time
import shutil
import subprocess
import textwrap
from datetime import datetime, timezone

import pytest
import requests

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

BACKEND_ENV = "/app/backend/.env"
BACKEND_ENV_BACKUP = "/app/backend/.env.itest_backup"


# ---------------------- Helpers ----------------------


def _wait_backend_ready(timeout: int = 40):
    for _ in range(timeout):
        try:
            r = requests.get(f"{API}/version", timeout=3)
            if r.status_code == 200:
                return
        except Exception:
            pass
        time.sleep(1)
    raise RuntimeError("Backend did not come back up in time")


def _set_env_var(key: str, value: str):
    """Rewrite backend/.env <key>=<value> and restart backend to reload."""
    with open(BACKEND_ENV) as f:
        lines = f.readlines()
    new_lines = []
    found = False
    for line in lines:
        if line.startswith(f"{key}="):
            new_lines.append(f'{key}="{value}"\n')
            found = True
        else:
            new_lines.append(line)
    if not found:
        new_lines.append(f'{key}="{value}"\n')
    with open(BACKEND_ENV, "w") as f:
        f.writelines(new_lines)
    subprocess.run(
        ["sudo", "supervisorctl", "restart", "backend"],
        check=True, capture_output=True,
    )
    _wait_backend_ready()


@pytest.fixture(scope="module", autouse=True)
def _backup_and_restore_env():
    """Backup backend/.env before tests, restore + restart at the end."""
    shutil.copyfile(BACKEND_ENV, BACKEND_ENV_BACKUP)
    yield
    shutil.copyfile(BACKEND_ENV_BACKUP, BACKEND_ENV)
    os.remove(BACKEND_ENV_BACKUP)
    subprocess.run(
        ["sudo", "supervisorctl", "restart", "backend"],
        check=True, capture_output=True,
    )
    _wait_backend_ready()


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


# ================== load_dotenv(override=False) ==================


class TestLoadDotenvOverride:
    """Unit-level: launch a fresh Python subprocess and import config modules
    with a pre-set env var; verify that value wins over the one from .env file."""

    def _run_in_subprocess(self, module_import: str, env_var: str, env_var_value: str | None):
        """Run a small snippet in a subprocess importing a config module and
        printing GOOGLE_MAPS_API_KEY. Returns captured stdout."""
        env = os.environ.copy()
        # Isolate: remove any pre-existing test var to be explicit.
        env.pop(env_var, None)
        if env_var_value is not None:
            env[env_var] = env_var_value

        # PYTHONPATH so the subprocess can import from /app/backend
        env["PYTHONPATH"] = "/app/backend"

        snippet = textwrap.dedent(f"""
            import os
            import {module_import} as mod
            # Prefer module.GOOGLE_MAPS_API_KEY attribute if present,
            # otherwise fall back to os.environ.
            val = getattr(mod, "GOOGLE_MAPS_API_KEY", None)
            if val is None and hasattr(mod, "settings"):
                val = mod.settings.GOOGLE_MAPS_API_KEY
            print("VALUE=" + repr(val))
        """)
        proc = subprocess.run(
            [sys.executable, "-c", snippet],
            env=env,
            capture_output=True, text=True, timeout=30,
        )
        assert proc.returncode == 0, f"Subprocess failed: {proc.stderr}"
        # Extract VALUE line
        for line in proc.stdout.splitlines():
            if line.startswith("VALUE="):
                return line[len("VALUE="):].strip()
        pytest.fail(f"No VALUE printed. stdout={proc.stdout} stderr={proc.stderr}")

    def test_core_config_env_takes_precedence_over_file(self):
        """When GOOGLE_MAPS_API_KEY is pre-set in os.environ before import,
        core.config must NOT overwrite it with the value from .env file."""
        preset = "TEST_ENV_KEY_XYZ_core"
        value = self._run_in_subprocess("core.config", "GOOGLE_MAPS_API_KEY", preset)
        assert value == repr(preset), f"Expected pre-set env to win. Got: {value}"

    def test_utils_config_env_takes_precedence_over_file(self):
        """Same behavior for utils.config (Settings dataclass-like)."""
        preset = "TEST_ENV_KEY_XYZ_utils"
        value = self._run_in_subprocess("utils.config", "GOOGLE_MAPS_API_KEY", preset)
        assert value == repr(preset), f"Expected pre-set env to win. Got: {value}"

    def test_core_config_reads_file_when_env_not_set(self):
        """When GOOGLE_MAPS_API_KEY is NOT set in env, the value must come from
        the .env file (i.e., load_dotenv still populates missing vars)."""
        # Read the current file value first
        file_value = None
        with open(BACKEND_ENV) as f:
            for line in f:
                if line.startswith("GOOGLE_MAPS_API_KEY="):
                    file_value = line.split("=", 1)[1].strip().strip('"').strip("'")
                    break
        assert file_value is not None, "GOOGLE_MAPS_API_KEY line missing from .env"
        value = self._run_in_subprocess("core.config", "GOOGLE_MAPS_API_KEY", None)
        assert value == repr(file_value), (
            f"Expected .env file value when env unset. file_value={file_value!r}, got={value}"
        )

    def test_utils_config_reads_file_when_env_not_set(self):
        file_value = None
        with open(BACKEND_ENV) as f:
            for line in f:
                if line.startswith("GOOGLE_MAPS_API_KEY="):
                    file_value = line.split("=", 1)[1].strip().strip('"').strip("'")
                    break
        assert file_value is not None
        value = self._run_in_subprocess("utils.config", "GOOGLE_MAPS_API_KEY", None)
        assert value == repr(file_value)


# ================== Version endpoint ==================


class TestVersionEndpoint:
    def test_version_bumped_to_0_11_3_beta(self, session):
        r = session.get(f"{API}/version")
        assert r.status_code == 200
        data = r.json()
        assert data["version"] == "0.11.3-beta", f"Version mismatch: {data}"
        assert "release_name" in data
        assert "Fix load .env" in data["release_name"], f"Unexpected release_name: {data['release_name']}"


# ================== Non-regression on core flows ==================


class TestNonRegression:
    def test_login_and_me(self, admin_session):
        r = admin_session.get(f"{API}/auth/me")
        assert r.status_code == 200
        data = r.json()
        assert data["email"] == ADMIN_EMAIL
        assert "superadmin" in (data.get("ruoli") or [])

    def test_sedi_list(self, admin_session):
        r = admin_session.get(f"{API}/sedi")
        assert r.status_code == 200
        sedi = r.json()
        assert isinstance(sedi, list) and any(s.get("codice") == "A22" for s in sedi)

    def test_rimborsi_list(self, admin_session):
        r = admin_session.get(f"{API}/rimborsi")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_notifiche_list(self, admin_session):
        r = admin_session.get(f"{API}/notifiche")
        assert r.status_code == 200
        assert isinstance(r.json(), list)


# ================== calcola-km error handling ==================


class TestCalcolaKmErrorHandling:
    """Verify /api/calcola-km error handling:
       - empty key   → 500 "Google Maps API non configurata"
       - invalid key → 400 with detail containing Google status
    Restart backend after modifying .env to reload the config.
    """

    def test_empty_google_maps_key_returns_500(self, admin_session):
        _set_env_var("GOOGLE_MAPS_API_KEY", "")
        # After restart, need to re-login (cookie may still be valid but session
        # cookies survive restart — verify by refreshing me)
        r_me = admin_session.get(f"{API}/auth/me")
        if r_me.status_code != 200:
            admin_session.post(
                f"{API}/auth/login",
                json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            )
        r = admin_session.post(
            f"{API}/calcola-km",
            json={"origine": "Roma", "destinazione": "Milano"},
        )
        assert r.status_code == 500, f"Expected 500 with empty key, got {r.status_code}: {r.text}"
        detail = r.json().get("detail", "")
        assert "Google Maps API non configurata" in detail, f"Unexpected detail: {detail}"

    def test_invalid_google_maps_key_returns_400(self, admin_session):
        _set_env_var("GOOGLE_MAPS_API_KEY", "AIzaSy_INVALID_TEST_KEY_v0113beta_xxxxxxxx")
        r_me = admin_session.get(f"{API}/auth/me")
        if r_me.status_code != 200:
            admin_session.post(
                f"{API}/auth/login",
                json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            )
        r = admin_session.post(
            f"{API}/calcola-km",
            json={"origine": "Roma", "destinazione": "Milano"},
        )
        assert r.status_code == 400, f"Expected 400 with invalid key, got {r.status_code}: {r.text}"
        detail = r.json().get("detail", "")
        # Google returns REQUEST_DENIED for invalid keys; the backend surfaces the status
        assert "REQUEST_DENIED" in detail or "Impossibile calcolare il percorso" in detail, (
            f"Unexpected detail: {detail}"
        )


# ================== calcola-km rate limit (light smoke) ==================


class TestCalcolaKmRateLimit:
    """Smoke test: after restart (fresh counters), verify the 60/hour limiter
    kicks in on /api/calcola-km. Uses empty key so each request short-circuits
    with 500 (no Google API call), keeping the test fast."""

    def test_rate_limit_60_per_hour(self, admin_session):
        # backend restart → fresh in-memory counters
        _set_env_var("GOOGLE_MAPS_API_KEY", "")
        s = requests.Session()
        s.headers.update({"Content-Type": "application/json"})
        r_login = s.post(f"{API}/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
        assert r_login.status_code == 200

        # Public URL routes requests via Cloudflare + k8s ingress; the backend
        # can observe MORE than one client IP alternating across requests
        # (each IP gets its own 60/hour bucket). We therefore send ~140 requests
        # so that at least one IP's bucket is exhausted regardless of the split.
        codes = []
        first_429_at = None
        for i in range(140):
            r = s.post(f"{API}/calcola-km", json={"origine": "A", "destinazione": "B"})
            codes.append(r.status_code)
            if r.status_code == 429 and first_429_at is None:
                first_429_at = i + 1
        assert 429 in codes, (
            f"Expected 429 within 140 requests (60/hour). "
            f"Distribution: 500={codes.count(500)}, 429={codes.count(429)}, tail={codes[-5:]}"
        )
        # 429 detail italian check
        r = s.post(f"{API}/calcola-km", json={"origine": "A", "destinazione": "B"})
        if r.status_code == 429:
            body = r.json()
            assert "Troppe" in body.get("detail", "") or "richieste" in body.get("detail", "")
