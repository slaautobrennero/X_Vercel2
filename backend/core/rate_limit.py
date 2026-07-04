"""
core/rate_limit.py
Configurazione centralizzata di slowapi (rate limiting per IP).

Backend in-memory: perfetto per singolo processo/singolo Pi.
Se in futuro si scalerà a più istanze, sostituire con Redis:
    limiter = Limiter(key_func=get_remote_address, storage_uri="redis://redis:6379")

Uso nei router:
    from core.rate_limit import limiter

    @router.post("/endpoint")
    @limiter.limit("5/minute")
    async def endpoint(request: Request):  # request DEVE essere primo arg
        ...
"""
from slowapi import Limiter
from slowapi.util import get_remote_address

# ==============================================================
# Limiter globale: usa l'IP remoto come chiave.
# I limiti specifici per endpoint si applicano tramite decoratore.
# Il limite di default agisce come safety net su tutti gli endpoint
# che NON hanno un decoratore specifico.
# ==============================================================
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200/minute"],  # safety net globale, molto largo
    headers_enabled=True,             # aggiunge X-RateLimit-* header
)
