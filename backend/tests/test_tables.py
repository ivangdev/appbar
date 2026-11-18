"""Tests de integracion de mesas (tables)."""

from __future__ import annotations

from collections.abc import Callable

from fastapi.testclient import TestClient

from app.models.user import User


def test_create_table_admin(
    client: TestClient, admin_user: User, login: Callable[[str], None]
) -> None:
    login(admin_user.email)
    response = client.post("/v1/tables", json={"table_number": 7, "label": "Terraza"})
    assert response.status_code == 201
    body = response.json()
    assert body["table_number"] == 7
    assert body["status"] == "free"


def test_create_table_forbidden_for_waiter(
    client: TestClient, waiter_user: User, login: Callable[[str], None]
) -> None:
    login(waiter_user.email)
    response = client.post("/v1/tables", json={"table_number": 8})
    assert response.status_code == 403


def test_create_table_duplicate_conflict(
    client: TestClient, admin_user: User, login: Callable[[str], None]
) -> None:
    login(admin_user.email)
    client.post("/v1/tables", json={"table_number": 9})
    response = client.post("/v1/tables", json={"table_number": 9})
    assert response.status_code == 409


def test_update_and_list_tables(
    client: TestClient, admin_user: User, login: Callable[[str], None]
) -> None:
    login(admin_user.email)
    table = client.post("/v1/tables", json={"table_number": 10}).json()
    updated = client.patch(f"/v1/tables/{table['id']}", json={"label": "Ventana"})
    assert updated.status_code == 200
    assert updated.json()["label"] == "Ventana"
    assert len(client.get("/v1/tables").json()) == 1


def test_delete_table_empty_ok(
    client: TestClient, admin_user: User, login: Callable[[str], None]
) -> None:
    login(admin_user.email)
    table = client.post("/v1/tables", json={"table_number": 11}).json()
    assert client.delete(f"/v1/tables/{table['id']}").status_code == 204


def test_delete_table_with_orders_conflict(
    client: TestClient,
    menu: dict[str, object],
    admin_user: User,
    waiter_user: User,
    login: Callable[[str], None],
) -> None:
    table = menu["table"]
    assert isinstance(table, dict)

    # El mesero abre una orden en la mesa.
    login(waiter_user.email)
    client.post("/v1/orders", json={"table_id": table["id"]})

    # El admin intenta borrar la mesa con ordenes -> 409.
    login(admin_user.email)
    response = client.delete(f"/v1/tables/{table['id']}")
    assert response.status_code == 409
