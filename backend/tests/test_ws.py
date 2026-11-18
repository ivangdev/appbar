"""Tests del WebSocket del tablero de mesas (auth por cookie)."""

from __future__ import annotations

from collections.abc import Callable

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from app.core.security import ACCESS_COOKIE_NAME
from app.models.user import User


def test_websocket_requires_auth(client: TestClient) -> None:
    """Sin cookie, la conexion se rechaza (close 1008)."""
    with (
        pytest.raises(WebSocketDisconnect),
        client.websocket_connect("/ws/tables"),
    ):
        pass


def test_websocket_rejects_invalid_token(client: TestClient) -> None:
    with (
        pytest.raises(WebSocketDisconnect),
        client.websocket_connect(
            "/ws/tables", headers={"cookie": f"{ACCESS_COOKIE_NAME}=no-es-jwt"}
        ),
    ):
        pass


def test_websocket_accepts_valid_cookie(
    client: TestClient, admin_user: User, login: Callable[[str], None]
) -> None:
    """Con cookie valida, la conexion se acepta (no lanza)."""
    login(admin_user.email)
    token = client.cookies.get(ACCESS_COOKIE_NAME)
    assert token

    with client.websocket_connect(
        "/ws/tables", headers={"cookie": f"{ACCESS_COOKIE_NAME}={token}"}
    ):
        # Si llegamos aqui sin excepcion, el handshake fue aceptado.
        assert True


def test_websocket_receives_order_event(
    client: TestClient,
    menu: dict[str, object],
    waiter_user: User,
    login: Callable[[str], None],
) -> None:
    """Abrir una orden difunde un evento a los clientes conectados."""
    table = menu["table"]
    assert isinstance(table, dict)

    login(waiter_user.email)
    token = client.cookies.get(ACCESS_COOKIE_NAME)
    assert token

    with client.websocket_connect(
        "/ws/tables", headers={"cookie": f"{ACCESS_COOKIE_NAME}={token}"}
    ) as ws:
        response = client.post("/v1/orders", json={"table_id": table["id"]})
        assert response.status_code == 201

        event = ws.receive_json()
        assert event["type"] in {"new_order", "table_status_update"}
        assert event["data"]["table_id"] == table["id"]
