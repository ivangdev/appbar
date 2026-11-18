"""Punto de entrada de la aplicacion FastAPI (POS Bar).

Ejecutar en dev:
    ./.venv/bin/uvicorn app.main:app --reload
Docs interactivas: http://localhost:8000/docs
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api.v1.auth import router as auth_router
from app.api.v1.categories import router as categories_router
from app.api.v1.orders import router as orders_router
from app.api.v1.payments import router as payments_router
from app.api.v1.products import router as products_router
from app.api.v1.reports import router as reports_router
from app.api.v1.tables import router as tables_router
from app.api.v1.users import router as users_router
from app.api.ws import router as ws_router
from app.core.rate_limit import limiter
from app.core.websocket import manager


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Liga el event loop del servidor para poder emitir eventos WebSocket."""
    manager.bind_loop(asyncio.get_running_loop())
    yield


app = FastAPI(title="POS Bar API", version="1.3.0", lifespan=lifespan)

# Rate limiting (slowapi): estado + manejador de error 429.
app.state.limiter = limiter
# El handler de slowapi tipa el segundo argumento como RateLimitExceeded (mas
# especifico que Exception); es compatible en runtime pero mypy es estricto.
app.add_exception_handler(
    RateLimitExceeded,
    _rate_limit_exceeded_handler,  # type: ignore[arg-type]
)

API_PREFIX = "/v1"
app.include_router(auth_router, prefix=API_PREFIX)
app.include_router(categories_router, prefix=API_PREFIX)
app.include_router(products_router, prefix=API_PREFIX)
app.include_router(tables_router, prefix=API_PREFIX)
app.include_router(orders_router, prefix=API_PREFIX)
app.include_router(payments_router, prefix=API_PREFIX)
app.include_router(reports_router, prefix=API_PREFIX)
app.include_router(users_router, prefix=API_PREFIX)

# WebSocket fuera de /v1 (ruta /ws/tables).
app.include_router(ws_router)


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    """Chequeo simple de que el servidor esta arriba."""
    return {"status": "ok"}
