"""Tests de integracion de ordenes e items."""

from __future__ import annotations

from collections.abc import Callable

from fastapi.testclient import TestClient

from app.models.user import User


def _open_order(client: TestClient, table_id: str) -> dict[str, object]:
    response = client.post("/v1/orders", json={"table_id": table_id})
    assert response.status_code == 201
    return response.json()


def _add_item(client: TestClient, order_id: str, product_id: str, quantity: int = 1) -> dict:
    response = client.post(
        f"/v1/orders/{order_id}/items",
        json={"product_id": product_id, "quantity": quantity},
    )
    assert response.status_code == 201
    return response.json()


def test_open_order_sets_table_occupied(
    client: TestClient,
    menu: dict[str, object],
    waiter_user: User,
    login: Callable[[str], None],
) -> None:
    table = menu["table"]
    assert isinstance(table, dict)
    login(waiter_user.email)
    order = _open_order(client, table["id"])
    assert order["status"] == "open"

    tables = client.get("/v1/tables").json()
    assert tables[0]["status"] == "occupied"


def test_open_second_order_conflict(
    client: TestClient,
    menu: dict[str, object],
    waiter_user: User,
    login: Callable[[str], None],
) -> None:
    table = menu["table"]
    assert isinstance(table, dict)
    login(waiter_user.email)
    _open_order(client, table["id"])
    response = client.post("/v1/orders", json={"table_id": table["id"]})
    assert response.status_code == 409


def test_add_item_snapshots_price(
    client: TestClient,
    menu: dict[str, object],
    waiter_user: User,
    login: Callable[[str], None],
) -> None:
    table, product = menu["table"], menu["product"]
    assert isinstance(table, dict) and isinstance(product, dict)
    login(waiter_user.email)
    order = _open_order(client, table["id"])
    item = _add_item(client, order["id"], product["id"], quantity=2)
    assert item["unit_price"] == 5000
    assert item["total_price"] == 10000
    assert item["paid_quantity"] == 0


def test_get_active_order_and_404(
    client: TestClient,
    menu: dict[str, object],
    waiter_user: User,
    login: Callable[[str], None],
) -> None:
    table = menu["table"]
    assert isinstance(table, dict)
    login(waiter_user.email)

    assert client.get(f"/v1/orders?table_id={table['id']}").status_code == 404
    order = _open_order(client, table["id"])
    fetched = client.get(f"/v1/orders?table_id={table['id']}")
    assert fetched.status_code == 200
    assert fetched.json()["id"] == order["id"]


def test_update_item_recomputes_total(
    client: TestClient,
    menu: dict[str, object],
    waiter_user: User,
    login: Callable[[str], None],
) -> None:
    table, product = menu["table"], menu["product"]
    assert isinstance(table, dict) and isinstance(product, dict)
    login(waiter_user.email)
    order = _open_order(client, table["id"])
    item = _add_item(client, order["id"], product["id"], quantity=1)

    updated = client.patch(f"/v1/orders/items/{item['id']}", json={"quantity": 3})
    assert updated.status_code == 200
    assert updated.json()["total_price"] == 15000

    fetched = client.get(f"/v1/orders?table_id={table['id']}").json()
    assert fetched["total_amount"] == 15000


def test_delete_item(
    client: TestClient,
    menu: dict[str, object],
    waiter_user: User,
    login: Callable[[str], None],
) -> None:
    table, product = menu["table"], menu["product"]
    assert isinstance(table, dict) and isinstance(product, dict)
    login(waiter_user.email)
    order = _open_order(client, table["id"])
    item = _add_item(client, order["id"], product["id"])

    assert client.delete(f"/v1/orders/items/{item['id']}").status_code == 204
    fetched = client.get(f"/v1/orders?table_id={table['id']}").json()
    assert fetched["total_amount"] == 0


def test_close_and_cancel_order(
    client: TestClient,
    menu: dict[str, object],
    waiter_user: User,
    login: Callable[[str], None],
) -> None:
    table, product = menu["table"], menu["product"]
    assert isinstance(table, dict) and isinstance(product, dict)
    login(waiter_user.email)
    order = _open_order(client, table["id"])
    _add_item(client, order["id"], product["id"])

    closed = client.post(f"/v1/orders/{order['id']}/close")
    assert closed.status_code == 200
    assert closed.json()["status"] == "closed"
    # no se puede cerrar dos veces
    assert client.post(f"/v1/orders/{order['id']}/close").status_code == 409

    cancelled = client.post(f"/v1/orders/{order['id']}/cancel")
    assert cancelled.status_code == 409  # ya no esta 'open'


def test_cancel_open_order_frees_table(
    client: TestClient,
    menu: dict[str, object],
    waiter_user: User,
    login: Callable[[str], None],
) -> None:
    table, product = menu["table"], menu["product"]
    assert isinstance(table, dict) and isinstance(product, dict)
    login(waiter_user.email)
    order = _open_order(client, table["id"])
    _add_item(client, order["id"], product["id"])

    cancelled = client.post(f"/v1/orders/{order['id']}/cancel")
    assert cancelled.status_code == 200
    assert cancelled.json()["status"] == "cancelled"
    assert client.get("/v1/tables").json()[0]["status"] == "free"


def test_order_history(
    client: TestClient,
    menu: dict[str, object],
    waiter_user: User,
    login: Callable[[str], None],
) -> None:
    table = menu["table"]
    assert isinstance(table, dict)
    login(waiter_user.email)
    _open_order(client, table["id"])
    history = client.get("/v1/orders/history")
    assert history.status_code == 200
    assert len(history.json()) == 1
