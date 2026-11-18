"""Endpoint WebSocket para el tablero de mesas.

Autenticacion por la cookie HttpOnly `access_token` del handshake (nunca por
la URL). Si el token falta o es invalido se rechaza la conexion (close 1008).
"""

from __future__ import annotations

import uuid
from typing import Annotated

import jwt
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import ACCESS_COOKIE_NAME, decode_access_token
from app.core.websocket import manager
from app.models.user import User

router = APIRouter()

DbSession = Annotated[Session, Depends(get_db)]


def _is_authorized(db: Session, token: str | None) -> bool:
    """Valida el JWT de la cookie y que el usuario exista y este activo."""
    if not token:
        return False
    try:
        payload = decode_access_token(token)
        user_id = uuid.UUID(str(payload.get("sub")))
    except (jwt.PyJWTError, ValueError):
        return False

    user = db.get(User, user_id)
    return user is not None and user.is_active


@router.websocket("/ws/tables")
async def tables_websocket(websocket: WebSocket, db: DbSession) -> None:
    """Canal de eventos en vivo del tablero de mesas."""
    if not _is_authorized(db, websocket.cookies.get(ACCESS_COOKIE_NAME)):
        await websocket.close(code=1008)
        return

    await manager.connect(websocket)
    try:
        while True:
            # No esperamos mensajes del cliente; solo mantenemos viva la conexion.
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
