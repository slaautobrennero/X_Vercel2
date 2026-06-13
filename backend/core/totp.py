"""
2FA TOTP (Time-based One-Time Password).
Compatibile con Google Authenticator, Authy, 1Password, Microsoft Authenticator.
"""
import io
import base64
from typing import Optional

import pyotp
import qrcode


ISSUER = "Portale SLA"


def generate_secret() -> str:
    """Genera un nuovo segreto TOTP (32 caratteri base32)."""
    return pyotp.random_base32()


def generate_qrcode_png(secret: str, email: str) -> str:
    """
    Genera un QR code PNG (base64) da scannerizzare con Google Authenticator.
    Restituisce 'data:image/png;base64,...' pronto per <img src>.
    """
    totp = pyotp.TOTP(secret)
    uri = totp.provisioning_uri(name=email, issuer_name=ISSUER)

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=8,
        border=2,
    )
    qr.add_data(uri)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    return f"data:image/png;base64,{b64}"


def verify_code(secret: str, code: str) -> bool:
    """Verifica un codice TOTP a 6 cifre. Accetta finestra +/- 1 (anti-clock-skew)."""
    if not secret or not code:
        return False
    code = code.strip().replace(" ", "")
    if not code.isdigit() or len(code) != 6:
        return False
    totp = pyotp.TOTP(secret)
    return totp.verify(code, valid_window=1)
