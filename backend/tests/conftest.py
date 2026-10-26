"""Configurazione comune dei test backend.

- Carica backend/.env e frontend/.env nelle variabili d'ambiente.
- Le chiamate all'URL pubblico vengono dirottate sul backend locale con un IP finto
  diverso per ogni test, così i limiti anti-abuso (es. 10 login/minuto) non si sommano tra file.
- I test che riscrivono backend/.env e riavviano il backend girano solo con RUN_ENV_TESTS=1.
"""
import http.cookiejar
import os
import random

import pytest
import requests
from dotenv import dotenv_values

for _f in ("/app/backend/.env", "/app/frontend/.env"):
    for _k, _v in dotenv_values(_f).items():
        os.environ.setdefault(_k, _v or "")

PUBLIC = os.environ["REACT_APP_BACKEND_URL"].rstrip("/")
LOCAL = "http://localhost:8001"

# I cookie di sessione sono "Secure": vanno inviati anche al backend locale in http
http.cookiejar.DefaultCookiePolicy.return_ok_secure = lambda self, cookie, request: True

_ip = {"value": "10.0.0.1"}
_orig_request = requests.Session.request


def _request(self, method, url, *args, **kwargs):
    if url.startswith(PUBLIC):
        url = LOCAL + url[len(PUBLIC):]
        kwargs["headers"] = {"X-Forwarded-Host": PUBLIC.split("://", 1)[1], **(kwargs.get("headers") or {})}
        hdrs = {k.lower() for k in {**self.headers, **(kwargs.get("headers") or {})}}
        if "cf-connecting-ip" not in hdrs and "x-forwarded-for" not in hdrs:
            kwargs["headers"] = {**(kwargs.get("headers") or {}), "CF-Connecting-IP": _ip["value"]}
    return _orig_request(self, method, url, *args, **kwargs)


requests.Session.request = _request


def mongo_db():
    from pymongo import MongoClient
    return MongoClient(os.environ["MONGO_URL"])[os.environ["DB_NAME"]]


def approva(email):
    """Le nuove registrazioni restano in attesa: nei test le approviamo direttamente."""
    mongo_db().users.update_one({"email": email}, {"$set": {"stato_approvazione": "approvato"}})


def cartella_test(sede_id=None):
    nome = f"TEST_cartella_{random.randint(0, 10**8)}"
    return str(mongo_db().cartelle.insert_one({"nome": nome, "sede_id": sede_id, "visibile": True}).inserted_id)


@pytest.fixture(scope="session", autouse=True)
def _pulizia_cartelle_test():
    yield
    db = mongo_db()
    ids = [str(c["_id"]) for c in db.cartelle.find({"nome": {"$regex": "^TEST_cartella_"}})]
    db.documenti.delete_many({"cartella_id": {"$in": ids}})
    db.cartelle.delete_many({"nome": {"$regex": "^TEST_cartella_"}})


@pytest.fixture(autouse=True)
def _ip_per_test():
    _ip["value"] = f"10.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}"
    yield


def pytest_collection_modifyitems(config, items):
    if os.environ.get("RUN_ENV_TESTS") == "1":
        return
    skip = pytest.mark.skip(reason="modifica backend/.env e riavvia il backend: lanciare con RUN_ENV_TESTS=1")
    for item in items:
        if item.get_closest_marker("modifica_env"):
            item.add_marker(skip)


def pytest_configure(config):
    config.addinivalue_line("markers", "modifica_env: test che riscrivono backend/.env e riavviano il backend")
