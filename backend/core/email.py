"""Email transazionali tramite Emergent Managed Email (Resend)."""
import asyncio
import base64
import hashlib
import smtplib
import ssl
from email.message import EmailMessage
from email.utils import formataddr
import ipaddress
import os
import re
from html import escape
from html.parser import HTMLParser
from typing import Optional
from urllib.parse import urlparse

import httpx
from bson import ObjectId
from cryptography.fernet import Fernet

from .config import FRONTEND_URL, JWT_SECRET, logger
from .db import db

EMAIL_BASE_URL = "https://integrations.emergentagent.com"
EMAIL_KEY = os.environ.get("EMERGENT_EMAIL_KEY", "")
EMAIL_FROM_NAME = os.environ["EMAIL_FROM_NAME"]
_LIMITE = asyncio.Semaphore(2)
_TASKS: set = set()

# ---------- Guardrail gate (G2/G3) ----------
_SHORTENERS = ("bit.ly", "tinyurl.com", "t.co", "is.gd", "cutt.ly", "goo.gl", "rebrand.ly")
_CRED_ASK = ("reply with your password", "reply with the code", "send your password", "cvv",
             "send us your password", "enter your password below", "confirm your card number",
             "your full card number", "seed phrase", "recovery phrase", "verify your card",
             "social security number", "confirm your bank details")
_HOSTISH = re.compile(r"\b(?:https?://)?((?:[a-z0-9-]+\.)+[a-z]{2,})", re.I)


def _host_ok(host: str) -> bool:
    if not host or "xn--" in host:
        return False
    try:
        ipaddress.ip_address(host)
        return False
    except ValueError:
        pass
    return not any(host == s or host.endswith("." + s) for s in _SHORTENERS)


def _same_site(shown: str, real: str) -> bool:
    return shown == real or real.endswith("." + shown) or shown.endswith("." + real)


class _EmailScan(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags, self.urls, self.anchors = set(), [], []
        self._href, self._text = None, []

    def handle_starttag(self, tag, attrs):
        self.tags.add(tag.lower())
        self.urls += [v for k, v in attrs if k.lower() in ("href", "src") and v]
        if tag.lower() == "a":
            self._href = dict((k.lower(), v) for k, v in attrs).get("href")
            self._text = []

    def handle_data(self, data):
        if self._href is not None:
            self._text.append(data)

    def handle_endtag(self, tag):
        if tag.lower() == "a" and self._href is not None:
            self.anchors.append((self._href, "".join(self._text)))
            self._href, self._text = None, []


def _assert_safe_email(subject: str, html: str) -> None:
    scan = _EmailScan()
    scan.feed(html)
    if scan.tags & {"form", "input", "textarea", "select"}:
        raise ValueError("No forms or input fields in email (G2)")
    body = f"{subject}\n{html}".lower()
    for p in _CRED_ASK:
        if p in body:
            raise ValueError(f"Email asks the recipient for credentials: {p!r} (G2)")
    for url in scan.urls:
        low = url.strip().lower()
        if low.startswith(("mailto:", "tel:", "cid:", "#")):
            continue
        if not low.startswith("https://"):
            raise ValueError(f"Email links/assets must be absolute https: {url!r} (G3)")
        host = urlparse(low).hostname or ""
        if not _host_ok(host) or urlparse(low).username is not None:
            raise ValueError(f"Shortened, numeric-host or credential-bearing URL: {url!r} (G3)")
    for href, text in scan.anchors:
        real = urlparse(href.strip().lower()).hostname or ""
        if not real:
            continue
        for m in _HOSTISH.finditer(text):
            if not _same_site(m.group(1).lower(), real):
                raise ValueError(f"Anchor text {m.group(1)!r} ≠ real link host {real!r} (G3)")


async def send_email(*, to: str, subject: str, html: str, reply_to: Optional[str] = None) -> Optional[str]:
    if not EMAIL_KEY:
        logger.warning("EMERGENT_EMAIL_KEY non impostata: email non inviata")
        return None
    _assert_safe_email(subject, html)
    payload = {"to": [to], "subject": subject, "html": html, "from_name": EMAIL_FROM_NAME}
    if reply_to:
        payload["contact_email"] = reply_to
    for tentativo in range(4):
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(f"{EMAIL_BASE_URL}/api/v1/email/send", headers={"X-Email-Key": EMAIL_KEY}, json=payload)
        if resp.status_code != 429:
            break
        await asyncio.sleep(2 ** tentativo)
    if resp.status_code >= 400:
        try:
            body = resp.json()
        except ValueError:
            body = {}
        if body.get("code") in ("insufficient_credits", "integration_disabled", "daily_limit_reached"):
            logger.warning(f"Email sospese: {body.get('code')} - {body.get('message', '')}")
        else:
            logger.error(f"Invio email fallito: {resp.status_code} {resp.text[:300]}")
        return None
    return resp.json().get("id")


# ---------- Template ----------
def _link(path: str) -> str:
    return f"{FRONTEND_URL.rstrip('/')}{path}"


def _layout(titolo: str, paragrafi: list, cta: Optional[tuple] = None) -> str:
    righe = "".join(f'<p style="margin:0 0 14px;font-size:15px;line-height:1.55;color:#1f2937">{p}</p>' for p in paragrafi)
    bottone = ""
    if cta and FRONTEND_URL.startswith("https://"):
        bottone = (f'<p style="margin:22px 0"><a href="{escape(cta[1])}" style="background:#1E4D8C;color:#ffffff;'
                   f'text-decoration:none;padding:12px 22px;border-radius:6px;font-weight:bold;display:inline-block">'
                   f'{escape(cta[0])}</a></p>')
    return (
        '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#F2F5FA;padding:24px 0">'
        '<tr><td align="center"><table role="presentation" width="560" cellpadding="0" cellspacing="0" '
        'style="background:#ffffff;border-radius:10px;font-family:Arial,sans-serif">'
        '<tr><td style="background:#1E4D8C;color:#ffffff;padding:18px 28px;font-size:18px;font-weight:bold;'
        f'border-radius:10px 10px 0 0">{escape(EMAIL_FROM_NAME)}</td></tr>'
        f'<tr><td style="padding:28px"><h1 style="margin:0 0 16px;font-size:20px;color:#143766">{escape(titolo)}</h1>'
        f'{righe}{bottone}</td></tr>'
        '<tr><td style="padding:16px 28px;border-top:1px solid #e5e7eb;font-size:12px;color:#6b7280">'
        f'Email automatica del Portale {escape(EMAIL_FROM_NAME)}. '
        'Non ti chiederemo mai la password, né per email né per telefono.</td></tr>'
        '</table></td></tr></table>'
    )


def _nome(u: dict) -> str:
    return escape(f"{u.get('nome', '')}".strip() or "iscritto")


def tpl_registrazione_approvata(u: dict):
    return ("La tua registrazione è stata approvata",
            _layout("Benvenuto nel portale", [f"Ciao {_nome(u)},", "la tua registrazione è stata approvata dalla tua concessionaria. Ora puoi accedere con la tua email e la password che hai scelto."], ("Accedi al portale", _link("/login"))))


def tpl_registrazione_rifiutata(u: dict):
    return ("Registrazione non approvata",
            _layout("Registrazione non approvata", [f"Ciao {_nome(u)},", "la tua richiesta di registrazione non è stata approvata e i dati inseriti sono stati eliminati.", "Se pensi si tratti di un errore, contatta la segreteria della tua concessionaria."]))


def tpl_nuova_registrazione(approvatore: dict, nuovo: dict, ruolo: str):
    chi = escape(f"{nuovo.get('nome', '')} {nuovo.get('cognome', '')}")
    return ("Nuova registrazione da approvare",
            _layout("Nuova registrazione da approvare", [f"Ciao {_nome(approvatore)},", f"<b>{chi}</b> ({escape(nuovo.get('email', ''))}) chiede di accedere al portale come <b>{escape(ruolo)}</b>.", "Controlla che sia davvero un iscritto e approva o rifiuta dalla pagina Utenti."], ("Apri la pagina Utenti", _link("/utenti"))))


_STATI = {"approvato": "approvata", "rifiutato": "rifiutata", "pagato": "pagata"}


def tpl_rimborso_stato(u: dict, rimborso: dict, stato: str):
    data = escape(str(rimborso.get("data", "")))
    importo = rimborso.get("importo_totale")
    righe = [f"Ciao {_nome(u)},", f"la tua richiesta di rimborso del <b>{data}</b> è stata <b>{_STATI[stato]}</b>."]
    if importo is not None:
        righe.append(f"Importo: <b>€ {float(importo):.2f}</b>")
    if stato == "pagato":
        righe.append("Nel dettaglio del rimborso trovi la contabile del bonifico.")
    if stato == "rifiutato":
        righe.append("Per conoscere il motivo contatta la segreteria o il cassiere della tua concessionaria.")
    return (f"Rimborso {_STATI[stato]}", _layout(f"Rimborso {_STATI[stato]}", righe, ("Vedi i tuoi rimborsi", _link("/rimborsi"))))


def tpl_reset_password(u: dict, token: str):
    return ("Reimposta la tua password",
            _layout("Reimposta la password", [f"Ciao {_nome(u)},", "abbiamo ricevuto una richiesta per reimpostare la password del tuo account. Il link vale 30 minuti e si può usare una sola volta.", "Se non sei stato tu, ignora questa email: la tua password resta invariata."], ("Scegli una nuova password", _link(f"/reset-password?token={token}"))))


_SICUREZZA = {
    "password_cambiata": ("La tua password è stata cambiata", "La password del tuo account è stata appena cambiata e sei stato scollegato da tutti i dispositivi."),
    "password_reimpostata_admin": ("Password reimpostata dalla segreteria", "Un responsabile della tua concessionaria ha reimpostato la tua password. Al prossimo accesso dovrai sceglierne una nuova."),
    "account_bloccato": ("Accesso bloccato per troppi tentativi", "Sono stati fatti 5 tentativi di accesso errati al tuo account: l'accesso è bloccato per 15 minuti."),
    "2fa_attivata": ("Verifica in due passaggi attivata", "La verifica in due passaggi (2FA) è stata attivata sul tuo account."),
    "2fa_disattivata": ("Verifica in due passaggi disattivata", "La verifica in due passaggi (2FA) è stata disattivata sul tuo account."),
}


def tpl_nuovo_documento(u: dict, nome_doc: str, cartella: str):
    return (f"Nuovo documento: {nome_doc}"[:150],
            _layout("Nuovo documento disponibile", [f"Ciao {_nome(u)},", f"nella cartella <b>{escape(cartella)}</b> è stato caricato il documento <b>{escape(nome_doc)}</b>.", "Puoi disattivare queste email dal tuo Profilo."], ("Apri i documenti", _link("/documenti"))))


def tpl_prova():
    return ("Email di prova dal Portale", _layout("Email di prova", ["Se leggi questo messaggio, le email della tua concessionaria sono configurate correttamente."]))


def tpl_sicurezza(u: dict, evento: str):
    titolo, testo = _SICUREZZA[evento]
    return (titolo, _layout(titolo, [f"Ciao {_nome(u)},", testo, "Se non sei stato tu, contatta subito la segreteria della tua concessionaria."]))


# ---------- Configurazione per sede (nessuna | smtp | emergent) ----------
def _fernet() -> Fernet:
    return Fernet(base64.urlsafe_b64encode(hashlib.sha256(JWT_SECRET.encode()).digest()))


def cifra(testo: str) -> str:
    return _fernet().encrypt(testo.encode()).decode()


def decifra(testo: str) -> str:
    return _fernet().decrypt(testo.encode()).decode()


def _smtp_send(cfg: dict, to: str, subject: str, html: str, reply_to: Optional[str]) -> None:
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = formataddr((EMAIL_FROM_NAME, cfg["smtp_from"] or cfg["smtp_user"]))
    msg["To"] = to
    if reply_to:
        msg["Reply-To"] = reply_to
    msg.set_content("Apri questa email con un programma che supporta l'HTML.")
    msg.add_alternative(html, subtype="html")
    password = decifra(cfg["smtp_password_enc"]) if cfg.get("smtp_password_enc") else ""
    if cfg.get("smtp_tls") == "ssl":
        server = smtplib.SMTP_SSL(cfg["smtp_host"], int(cfg["smtp_port"]), timeout=20, context=ssl.create_default_context())
    else:
        server = smtplib.SMTP(cfg["smtp_host"], int(cfg["smtp_port"]), timeout=20)
        server.starttls(context=ssl.create_default_context())
    with server:
        if cfg.get("smtp_user"):
            server.login(cfg["smtp_user"], password)
        server.send_message(msg)


async def sede_per_utente(user: dict) -> Optional[dict]:
    """Sede dell'utente; per chi non ha sede (SuperAdmin) si usa la Sede Nazionale."""
    query = {"_id": ObjectId(user["sede_id"])} if user.get("sede_id") else {"is_nazionale": True}
    return await db.sedi.find_one(query, {"email_config": 1, "email_contatto": 1})


async def invia_con_config(cfg: dict, to: str, tpl: tuple, reply_to: Optional[str]) -> None:
    subject, html = tpl
    _assert_safe_email(subject, html)
    modalita = cfg.get("modalita", "nessuna")
    if modalita == "smtp":
        await asyncio.wait_for(asyncio.to_thread(_smtp_send, cfg, to, subject, html, reply_to), timeout=40)
    elif modalita == "emergent":
        if not await send_email(to=to, subject=subject, html=html, reply_to=reply_to):
            raise RuntimeError("il servizio email ha rifiutato l'invio (crediti, limite giornaliero o chiave mancante)")


async def _invia(user: dict, tpl: tuple) -> None:
    try:
        sede = await sede_per_utente(user) or {}
        cfg = sede.get("email_config") or {}
        if cfg.get("modalita", "nessuna") == "nessuna":
            return
        async with _LIMITE:
            await invia_con_config(cfg, user["email"], tpl, sede.get("email_contatto"))
    except Exception as e:
        logger.error(f"Errore invio email a utente {user.get('_id') or user.get('id')}: {e}")


def invia_email(user: dict, tpl: tuple) -> None:
    """Non blocca la richiesta: l'email parte in background."""
    if user and user.get("email"):
        task = asyncio.create_task(_invia(user, tpl))
        _TASKS.add(task)
        task.add_done_callback(_TASKS.discard)


async def _invia_a_molti(utenti: list, tpl_fn) -> None:
    for u in utenti:
        await _invia(u, tpl_fn(u))


def invia_email_a_molti(utenti: list, tpl_fn) -> None:
    """Invio in background, uno alla volta, ognuno con la configurazione della propria sede."""
    if utenti:
        task = asyncio.create_task(_invia_a_molti(utenti, tpl_fn))
        _TASKS.add(task)
        task.add_done_callback(_TASKS.discard)
