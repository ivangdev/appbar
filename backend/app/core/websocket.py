"""Gestor de conexiones WebSocket y emision de eventos.

El WebSocket se autentica por la cookie HttpOnly `access_token` enviada en el
handshake (nunca por la URL). Desde endpoints sincronos (threadpool) se
programan los broadcasts sobre el event loop del servidor con
`broadcast_event`.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Mantiene las conexiones WS activas y difunde eventos a todas."""

    def __init__(self) -> None:
        self._connections: set[WebSocket] = set()
        self._loop: asyncio.AbstractEventLoop | None = None

    def bind_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        """Guarda el event loop del servidor para programar broadcasts."""
        self._loop = loop

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections.add(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        self._connections.discard(websocket)

    async def broadcast(self, event: dict[str, Any]) -> None:
        """Envia el evento a todas las conexiones; descarta las muertas."""
        dead: list[WebSocket] = []
        for websocket in list(self._connections):
            try:
                await websocket.send_json(event)
            except Exception:  # noqa: BLE001 - cualquier fallo = conexion muerta
                dead.append(websocket)
        for websocket in dead:
            self._connections.discard(websocket)


manager = ConnectionManager()


def broadcast_event(event: dict[str, Any]) -> None:
    """Programa un broadcast desde codigo sincrono (threadpool).

    Si no hay event loop ligado (p.ej. en tests sin lifespan) es un no-op.
    """
    loop = manager._loop
    if loop is None or loop.is_closed():
        return
    try:
        asyncio.run_coroutine_threadsafe(manager.broadcast(event), loop)
    except RuntimeError:
        logger.debug("No se pudo programar el broadcast del evento", exc_info=True)
