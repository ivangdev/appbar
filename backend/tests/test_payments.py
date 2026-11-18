"""Tests de integracion de pagos (parciales, totales y cancelacion)."""

from __future__ import annotations

from collections.abc import Callable

from fastapi.testclient import TestClient

from app.models.user import User


def _setup_order(
    client: TestClient, menu: dict[str, object], login: Callable[[str], None], waiter: User
) -> dict[str, object]:
    """Abre una orden con 2 unidades (total 10000) y devuelve orden + item."""
    table, product = menu["table"], menu["product"]
    assert isinstance(table, dict) and isinstance(product, dict)
    login(waiter.email)
    order = client.post("/v1/orders", json={"table_id": table["id"]}).json()
    item = client.post(
        f"/v1/orders/{order['id']}/items",
        json={"product_id": product["id"], "quantity": 2},
    ).json()
    return {"order": order, "item": item, "table": table}


def test_partial_payment_by_items(
    client: TestClient,
    menu: dict[str, object],
    waiter_user: User,
    login: Callable[[str], None],
) -> None:
    ctx = _setup_order(client, menu, login, waiter_user)
    order, item = ctx["order"], ctx["item"]
    assert isinstance(order, dict) and isinstance(item, dict)

    response = client.post(
        f"/v1/orders/{order['id']}/pay",
        json={
            "amount": 5000,
            "method": "cash",
            "allocations": [{"item_id": item["id"], "quantity": 1}],
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["remaining"] == 5000
    assert body["order"]["status"] == "partially_paid"
    assert body["order"]["amount_paid"] == 5000

    fetched = client.get(f"/v1/orders?table_id={ctx['table']['id']}").json()
    assert fetched["items"][0]["paid_quantity"] == 1
    assert fetched["status"] == "partially_paid"


def test_full_payment_without_allocations(
    client: TestClient,
    menu: dict[str, object],
    waiter_user: User,
    login: Callable[[str], None],
) -> None:
    ctx = _setup_order(client, menu, login, waiter_user)
    order = ctx["order"]
    assert isinstance(order, dict)

    response = client.post(
        f"/v1/orders/{order['id']}/pay",
        json={"amount": 10000, "method": "nequi"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["remaining"] == 0
    assert body["order"]["status"] == "paid"
    assert body["order"]["paid_at"] is not None

    # La mesa queda libre.
    assert client.get("/v1/tables").json()[0]["status"] == "free"


def test_payment_amount_must_match_allocations(
    client: TestClient,
    menu: dict[str, object],
    waiter_user: User,
    login: Callable[[str], None],
) -> None:
    ctx = _setup_order(client, menu, login, waiter_user)
    order, item = ctx["order"], ctx["item"]
    assert isinstance(order, dict) and isinstance(item, dict)

    response = client.post(
        f"/v1/orders/{order['id']}/pay",
        json={
            "amount": 4000,
            "method": "cash",
            "allocations": [{"item_id": item["id"], "quantity": 1}],
        },
    )
    assert response.status_code == 409


def test_payment_quantity_exceeds_pending(
    client: TestClient,
    menu: dict[str, object],
    waiter_user: User,
    login: Callable[[str], None],
) -> None:
    ctx = _setup_order(client, menu, login, waiter_user)
    order, item = ctx["order"], ctx["item"]
    assert isinstance(order, dict) and isinstance(item, dict)

    response = client.post(
        f"/v1/orders/{order['id']}/pay",
        json={
            "amount": 15000,
            "method": "cash",
            "allocations": [{"item_id": item["id"], "quantity": 3}],
        },
    )
    assert response.status_code == 409


def test_total_payment_must_cover_remaining(
    client: TestClient,
    menu: dict[str, object],
    waiter_user: User,
    login: Callable[[str], None],
) -> None:
    ctx = _setup_order(client, menu, login, waiter_user)
    order = ctx["order"]
    assert isinstance(order, dict)

    response = client.post(
        f"/v1/orders/{order['id']}/pay",
        json={"amount": 5000, "method": "cash"},
    )
    assert response.status_code == 409


def test_cancel_payment_after_full_payment(
    client: TestClient,
    menu: dict[str, object],
    waiter_user: User,
    login: Callable[[str], None],
) -> None:
    ctx = _setup_order(client, menu, login, waiter_user)
    order = ctx["order"]
    assert isinstance(order, dict)

    paid = client.post(
        f"/v1/orders/{order['id']}/pay",
        json={"amount": 10000, "method": "cash"},
    ).json()
    payment_id = paid["payment"]["id"]

    cancelled = client.post(f"/v1/payments/{payment_id}/cancel")
    assert cancelled.status_code == 200
    body = cancelled.json()
    assert body["cancelled"] is True
    assert body["amount"] == 10000
    assert body["remaining"] == 10000
    # se quitaron todos los pagos -> 'closed' y paid_at limpio
    assert body["order"]["status"] == "closed"
    assert body["order"]["paid_at"] is None

    # La mesa vuelve a estar ocupada (saldo pendiente > 0).
    assert client.get("/v1/tables").json()[0]["status"] == "occupied"


def test_cancel_partial_payment(
    client: TestClient,
    menu: dict[str, object],
    waiter_user: User,
    login: Callable[[str], None],
) -> None:
    ctx = _setup_order(client, menu, login, waiter_user)
    order, item = ctx["order"], ctx["item"]
    assert isinstance(order, dict) and isinstance(item, dict)

    partial = client.post(
        f"/v1/orders/{order['id']}/pay",
        json={
            "amount": 5000,
            "method": "cash",
            "allocations": [{"item_id": item["id"], "quantity": 1}],
        },
    ).json()
    payment_id = partial["payment"]["id"]

    cancelled = client.post(f"/v1/payments/{payment_id}/cancel").json()
    assert cancelled["remaining"] == 10000
    assert cancelled["order"]["amount_paid"] == 0
    assert cancelled["order"]["status"] == "closed"

    fetched = client.get(f"/v1/orders?table_id={ctx['table']['id']}").json()
    assert fetched["items"][0]["paid_quantity"] == 0
