"""
core/captcha.py
Verifica token hCaptcha lato backend.

Comportamento:
- Se HCAPTCHA_SECRET NON è configurato → salta verifica (log warning).
  Utile per dev/testing e come "soft rollout" durante il deploy.
- Se HCAPTCHA_SECRET è configurato → verifica obbligatoria via
  https://hcaptcha.com/siteverify.

Uso:
    from core.captcha import verify_hcaptcha
    await verify_hcaptcha(token, action="register", client_ip="1.2.3.4")

Fonti:
- https://docs.hcaptcha.com/
- L'endpoint siteverify richiede application/x-www-form-urlencoded.
"""
import os

import httpx
from fastapi import HTTPException, status

from core.config import logger

HCAPTCHA_VERIFY_URL = "https://hcaptcha.com/siteverify"
HCAPTCHA_TIMEOUT_SECONDS = 5


def hcaptcha_enabled() -> bool:
    """True se il backend ha una secret key configurata."""
    return bool(os.environ.get("HCAPTCHA_SECRET", "").strip())


async def verify_hcaptcha(token: str | None, action: str = "generic", client_ip: str | None = None) -> None:
    """
    Verifica un token hCaptcha. Solleva HTTPException 400 in caso di fallimento.

    - action: descrizione umana usata solo nei log/audit (es. "register", "login").
    - client_ip: IP del client, opzionale (rafforza la verifica in some cases).
    """
    secret = os.environ.get("HCAPTCHA_SECRET", "").strip()

    if not secret:
        # hCaptcha non configurato → skip (fail-open) per non bloccare gli utenti
        # se il sindacato non ha ancora ottenuto le chiavi. Loggo però un warning.
        logger.warning(
            "hCaptcha non configurato: verifica saltata per action=%s. "
            "Imposta HCAPTCHA_SECRET nel .env del backend per abilitare.",
            action,
        )
        return

    if not token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Completa il captcha per continuare.",
        )

    data = {"secret": secret, "response": token}
    if client_ip:
        data["remoteip"] = client_ip

    try:
        async with httpx.AsyncClient(timeout=HCAPTCHA_TIMEOUT_SECONDS) as client:
            resp = await client.post(HCAPTCHA_VERIFY_URL, data=data)
            result = resp.json()
    except Exception as exc:
        # In caso di errore di rete verso hCaptcha, fail-closed: meglio bloccare
        # una registrazione lecita che aprire la porta ai bot.
        logger.error("Errore verifica hCaptcha (action=%s): %s", action, exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Servizio captcha temporaneamente non disponibile. Riprova tra un minuto.",
        )

    if not result.get("success"):
        codes = result.get("error-codes", [])
        logger.warning("hCaptcha fallito (action=%s, ip=%s, codes=%s)", action, client_ip, codes)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verifica captcha fallita. Riprova.",
        )
