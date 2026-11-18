"""Rate limiting (slowapi) para la API.

Expone un unico `limiter` (key por IP) que se registra en `main.py` y se usa
como decorador en endpoints sensibles. El backend esta detras del proxy de
Caddy/Next, que reenvian la IP real en `X-Forwarded-For`; `get_remote_address`
lee eso cuando el header esta presente.

Los limites son por-ruta (no hay limite global por defecto) para no penalizar
la operacion normal del POS. En produccion con multiples replicas conviene un
backend compartido (Redis); para un solo proceso el storage en memoria basta.
"""

from __future__ import annotations

from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import settings
from app.core.constants import (
    AUTH_RATE_LIMIT,
    DEFAULT_RATE_LIMIT,
    READ_ONLY_RATE_LIMIT,
    WRITE_RATE_LIMIT,
)

limiter = Limiter(
    key_func=get_remote_address,
    enabled=settings.RATE_LIMIT_ENABLED,
)

__all__ = [
    "limiter",
    "AUTH_RATE_LIMIT",
    "DEFAULT_RATE_LIMIT",
    "READ_ONLY_RATE_LIMIT",
    "WRITE_RATE_LIMIT",
]
