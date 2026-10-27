"""Impostazioni per concessionaria: motivi per sede, invii automatici email, preferenze, riepilogo."""
import uuid

import pytest
import requests
from bson import ObjectId

from core.auth import hash_password
from tests.conftest import PUBLIC, mongo_db

API = f"{PUBLIC}/api"
TAG = uuid.uuid4().hex[:6]
PWD = "Test!Pass123"
PDF = b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF"


def _login(email, password=PWD):
    s = requests.Session()
    r = s.post(f"{API}/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return s


@pytest.fixture(scope="module")
def env():
    db = mongo_db()
    sA = str(db.sedi.insert_one({"nome": f"TEST_SedeA_{TAG}", "codice": f"TA{TAG}", "tariffa_km": 0.3, "rimborso_pasti": 10, "rimborso_autostrada": True}).inserted_id)
    sB = str(db.sedi.insert_one({"nome": f"TEST_SedeB_{TAG}", "codice": f"TB{TAG}", "tariffa_km": 0.4, "rimborso_pasti": 12, "rimborso_autostrada": False}).inserted_id)
    utenti = {}
    for chiave, ruolo, sede, extra in [("admA", "admin", sA, {}), ("delA", "delegato", sA, {}), ("isA", "iscritto", sA, {"email_documenti": False}), ("admB", "admin", sB, {})]:
        email = f"test_{chiave.lower()}_{TAG}@example.com"
        db.users.insert_one({"email": email, "password_hash": hash_password(PWD), "nome": chiave, "cognome": "Test",
                             "ruolo": ruolo, "ruoli": [ruolo], "sede_id": sede, "stato_approvazione": "approvato", "created_at": "2026-01-01T00:00:00+00:00", **extra})
        utenti[chiave] = email
    sa = _login("superadmin@sla.it", "SlaAdmin2024!")
    yield {"sA": sA, "sB": sB, "u": utenti, "sa": sa, "db": db}
    db.users.delete_many({"email": {"$regex": f"_{TAG}@example.com$"}})
    db.motivi_rimborso.delete_many({"nome": {"$regex": f"^TEST_{TAG}"}})
    ids = [str(c["_id"]) for c in db.cartelle.find({"sede_id": {"$in": [sA, sB]}})]
    db.documenti.delete_many({"cartella_id": {"$in": ids}})
    db.cartelle.delete_many({"sede_id": {"$in": [sA, sB]}})
    db.sedi.delete_many({"_id": {"$in": [ObjectId(sA), ObjectId(sB)]}})


def test_riepilogo_solo_superadmin_nazionale_in_cima(env):
    r = env["sa"].get(f"{API}/sedi/riepilogo-impostazioni")
    assert r.status_code == 200
    righe = r.json()
    nomi = [x["nome"] for x in righe]
    assert f"TEST_SedeA_{TAG}" in nomi
    if any(x["is_nazionale"] for x in righe):
        assert righe[0]["is_nazionale"]
    assert _login(env["u"]["admA"]).get(f"{API}/sedi/riepilogo-impostazioni").status_code == 403


def test_admin_modifica_tariffe_solo_propria_sede(env):
    s = _login(env["u"]["admA"])
    assert s.put(f"{API}/sedi/{env['sA']}", json={"tariffa_km": 0.42}).status_code == 200
    assert env["db"].sedi.find_one({"_id": ObjectId(env["sA"])})["tariffa_km"] == 0.42
    assert s.put(f"{API}/sedi/{env['sB']}", json={"tariffa_km": 0.99}).status_code == 403


def test_motivi_per_sede(env):
    sa = env["sa"]
    r = sa.post(f"{API}/motivi-rimborso", json={"nome": f"TEST_{TAG}_soloA", "richiede_note": False, "sede_ids": [env["sA"]]})
    assert r.status_code == 200
    mid = r.json()["id"]
    assert _login(env["u"]["admA"]).post(f"{API}/motivi-rimborso", json={"nome": f"TEST_{TAG}_x"}).status_code == 403
    nomi_a = [m["nome"] for m in _login(env["u"]["delA"]).get(f"{API}/motivi-rimborso").json()]
    nomi_b = [m["nome"] for m in _login(env["u"]["admB"]).get(f"{API}/motivi-rimborso", params={"sede_id": env["sA"]}).json()]
    assert f"TEST_{TAG}_soloA" in nomi_a
    assert f"TEST_{TAG}_soloA" not in nomi_b
    sb_filtrati = [m["nome"] for m in sa.get(f"{API}/motivi-rimborso", params={"sede_id": env["sB"]}).json()]
    assert f"TEST_{TAG}_soloA" not in sb_filtrati
    r = _login(env["u"]["admB"]).post(f"{API}/rimborsi", json={"data": "2026-06-01", "motivo_id": mid, "indirizzo_partenza": "A", "indirizzo_arrivo": "B", "km_andata": 10})
    assert r.status_code in (400, 422)


def test_invio_email_cartella_valori(env):
    s = _login(env["u"]["admA"])
    r = s.post(f"{API}/cartelle", json={"nome": f"TEST_Verbali_{TAG}"})
    assert r.status_code == 200, r.text
    cid = r.json()["id"]
    assert s.put(f"{API}/cartelle/{cid}/invio-email", json={"invio_email": "tutte"}).status_code == 400
    assert s.put(f"{API}/cartelle/{cid}/invio-email", json={"invio_email": "si"}).status_code == 200
    assert _login(env["u"]["admB"]).put(f"{API}/cartelle/{cid}/invio-email", json={"invio_email": "no"}).status_code == 403
    c = next(x for x in s.get(f"{API}/cartelle").json() if x["id"] == cid)
    assert c["invio_email"] == "si"
    env["cid"] = cid


def test_upload_con_invio_email(env):
    s = _login(env["u"]["admA"])
    r = s.post(f"{API}/documenti", data={"nome": f"TEST_doc_{TAG}", "cartella_id": env["cid"]}, files={"file": ("v.pdf", PDF, "application/pdf")})
    assert r.status_code == 200, r.text


def test_preferenze_email_documenti(env):
    s = _login(env["u"]["delA"])
    assert s.put(f"{API}/auth/me/preferenze", json={"email_documenti": False}).json() == {"email_documenti": False}
    assert s.get(f"{API}/auth/me").json()["email_documenti"] is False
    assert s.put(f"{API}/auth/me/preferenze", json={"email_documenti": True}).status_code == 200


def test_destinatari_email_documento(env):
    """Ricevono gli iscritti della sede; no chi ha disattivato, l'autore e le altre sedi."""
    from routes.documenti import filtro_destinatari
    db = env["db"]
    autore = db.users.find_one({"email": env["u"]["admA"]})
    q = filtro_destinatari("si", env["sA"], None, str(autore["_id"]))
    email = {u["email"] for u in db.users.find(q)}
    assert env["u"]["delA"] in email
    assert not email & {env["u"]["isA"], env["u"]["admA"], env["u"]["admB"]}
    tutte = {u["email"] for u in db.users.find(filtro_destinatari("tutte", None, None, str(autore["_id"])))}
    assert env["u"]["admB"] in tutte and env["u"]["isA"] not in tutte
