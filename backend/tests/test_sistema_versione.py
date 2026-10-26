import re

import requests

from tests.conftest import PUBLIC


def _v(path, pattern):
    return re.search(pattern, open(path).read()).group(1)


def test_versione_coerente_backend_frontend():
    be = _v("/app/backend/routes/public.py", r'APP_VERSION = "([^"]+)"')
    fe = _v("/app/frontend/src/version.js", r"APP_VERSION = '([^']+)'")
    assert be == fe
    r = requests.get(f"{PUBLIC}/api/version")
    assert r.status_code == 200
    assert r.json()["version"] == be
