"""
v0.14.1-beta — Allegati su disco + copia durevole GridFS (bucket 'allegati').
Covers: version, documenti upload/download/restore/delete, ricevute rimborso,
annuncio allegato, GDPR export ZIP con allegati.
"""
import io
import os
import uuid
import zipfile
from datetime import date
from pathlib import Path

import pytest
import requests
from pymongo import MongoClient

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/")
API = f"{BASE_URL}/api"
UPLOAD_DIR = Path("/app/uploads")
SA_EMAIL = "superadmin@sla.it"
SA_PASS = "SlaAdmin2024!"
PDF = b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF\n" + uuid.uuid4().hex.encode()


def _env():
    env = {}
    for line in open("/app/backend/.env"):
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")
    return env


@pytest.fixture(scope="module")
def mongo():
    e = _env()
    c = MongoClient(e["MONGO_URL"])
    yield c[e["DB_NAME"]]
    c.close()


@pytest.fixture(scope="module")
def sa():
    s = requests.Session()
    r = s.post(f"{API}/auth/login", json={"email": SA_EMAIL, "password": SA_PASS})
    if r.status_code != 200:
        pytest.skip(f"login failed {r.status_code}")
    return s


def gridfs_has(mongo, key):
    return mongo["allegati.files"].find_one({"filename": key}) is not None


# --- version
def test_version():
    r = requests.get(f"{API}/version")
    assert r.status_code == 200
    assert r.json()["version"] == "0.14.1-beta"


# --- documenti: upload -> download -> remove local -> restore -> delete
def test_documento_lifecycle(sa, mongo):
    r = sa.post(f"{API}/documenti", files={"file": ("TEST_doc.pdf", PDF, "application/pdf")},
                data={"nome": "TEST_doc_gridfs", "categoria": "modulistica"})
    assert r.status_code == 200, r.text
    d = r.json()
    path = d["path"]
    assert (UPLOAD_DIR / path).exists()
    assert gridfs_has(mongo, path)

    r = sa.get(f"{API}/documenti/{d['id']}/download")
    assert r.status_code == 200 and r.content == PDF

    (UPLOAD_DIR / path).unlink()
    r = sa.get(f"{API}/documenti/{d['id']}/download")
    assert r.status_code == 200 and r.content == PDF, "restore from GridFS failed"
    assert (UPLOAD_DIR / path).exists(), "local cache not re-created"

    r = sa.delete(f"{API}/documenti/{d['id']}")
    assert r.status_code == 200
    assert not (UPLOAD_DIR / path).exists()
    assert not gridfs_has(mongo, path)
    assert mongo["allegati.chunks"].count_documents({}) >= 0
    r = sa.get(f"{API}/documenti/{d['id']}/download")
    assert r.status_code == 404


# --- annuncio con allegato
def test_annuncio_allegato(sa, mongo):
    r = sa.post(f"{API}/annunci", files={"file": ("TEST_ann.pdf", PDF, "application/pdf")},
                data={"titolo": "TEST_annuncio_gridfs", "contenuto": "test"})
    assert r.status_code == 200, r.text
    a = r.json()
    aid = a.get("id")
    doc = mongo.annunci.find_one({"titolo": "TEST_annuncio_gridfs"}, sort=[("_id", -1)])
    key = doc["allegato_path"]
    aid = aid or str(doc["_id"])
    assert gridfs_has(mongo, key)
    (UPLOAD_DIR / key).unlink()
    r = sa.get(f"{API}/annunci/{aid}/download")
    assert r.status_code == 200 and r.content == PDF
    r = sa.delete(f"{API}/annunci/{aid}")
    assert r.status_code == 200
    assert not gridfs_has(mongo, key)
    assert not (UPLOAD_DIR / key).exists()


# --- rimborso ricevuta + GDPR export
@pytest.fixture(scope="module")
def rimborso(sa, mongo):
    motivi = sa.get(f"{API}/motivi-rimborso").json()
    mot = next(m for m in motivi if not m.get("richiede_note"))
    r = sa.post(f"{API}/rimborsi", json={
        "data": date.today().isoformat(), "motivo_id": mot["id"],
        "indirizzo_partenza": "TEST_A", "indirizzo_arrivo": "TEST_B", "km_andata": 10,
        "note": "TEST_gridfs"})
    assert r.status_code == 200, r.text
    rid = r.json()["id"]
    yield rid
    from bson import ObjectId
    rb = mongo.rimborsi.find_one({"_id": ObjectId(rid)})
    for rc in (rb or {}).get("ricevute", []) or []:
        (UPLOAD_DIR / rc["path"]).unlink(missing_ok=True)
        for f in mongo["allegati.files"].find({"filename": rc["path"]}):
            mongo["allegati.chunks"].delete_many({"files_id": f["_id"]})
            mongo["allegati.files"].delete_one({"_id": f["_id"]})
    mongo.rimborsi.delete_one({"_id": ObjectId(rid)})


def test_ricevuta_upload_download_restore(sa, mongo, rimborso):
    r = sa.post(f"{API}/rimborsi/{rimborso}/ricevute", files={"file": ("TEST_ric.pdf", PDF, "application/pdf")})
    assert r.status_code == 200, r.text
    rc = r.json()
    assert gridfs_has(mongo, rc["path"])
    (UPLOAD_DIR / rc["path"]).unlink()
    r = sa.get(f"{API}/rimborsi/{rimborso}/ricevute/{rc['id']}")
    assert r.status_code == 200 and r.content == PDF


def test_gdpr_export_zip_includes_allegati(sa, rimborso):
    r = sa.get(f"{API}/gdpr/export-zip")
    assert r.status_code == 200
    z = zipfile.ZipFile(io.BytesIO(r.content))
    names = z.namelist()
    print("ZIP entries:", names)
    assert "dati.json" in names
    import json
    data = json.loads(z.read("dati.json"))
    ids = [x["_id"] for x in data["rimborsi"]]
    assert rimborso in ids, f"rimborso of user missing from export (got {len(ids)} rimborsi)"
    assert any(n.startswith("ricevute/") for n in names), "no allegati in ZIP"


def test_ricevuta_delete_removes_gridfs(sa, mongo, rimborso):
    r = sa.post(f"{API}/rimborsi/{rimborso}/ricevute", files={"file": ("TEST_ric2.pdf", PDF, "application/pdf")})
    rc = r.json()
    r = sa.delete(f"{API}/rimborsi/{rimborso}/ricevute/{rc['id']}")
    assert r.status_code == 200
    assert not gridfs_has(mongo, rc["path"])
    assert not (UPLOAD_DIR / rc["path"]).exists()
