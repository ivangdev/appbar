"""Tests de integracion del reporte diario."""

from __future__ import annotations

from collections.abc import Callable

from fastapi.testclient import TestClient

from app.models.user import User


def _pay_order(client: TestClient, table_id: str, product_id: str, quantity: int) -> None:
    order = client.post("/v1/orders", json={"table_id": table_id}).json()
    client.post(
        f"/v1/orders/{order['id']}/items",
        json={"product_id": product_id, "quantity": quantity},
    )
    total = quantity * 5000
    response = client.post(
        f"/v1/orders/{order['id']}/pay",
        json={"amount": total, "method": "cash"},
    )
    assert response.status_code == 200


def test_daily_report_counts_only_paid_orders(
    client: TestClient,
    menu: dict[str, object],
    waiter_user: User,
    login: Callable[[str], None],
) -> None:
    table, product = menu["table"], menu["product"]
    assert isinstance(table, dict) and isinstance(product, dict)

    login(waiter_user.email)
    _pay_order(client, table["id"], product["id"], quantity=2)

    report = client.get("/v1/reports/daily").json()
    assert report["total"] == 10000
    assert report["by_table"] == [{"table_number": 1, "total": 10000}]
    assert report["by_product"] == [{"name": "Poker", "qty": 2, "revenue": 10000}]


def test_daily_report_excludes_unpaid_orders(
    client: TestClient,
    menu: dict[str, object],
    waiter_user: User,
    login: Callable[[str], None],
) -> None:
    table, product = menu["table"], menu["product"]
    assert isinstance(table, dict) and isinstance(product, dict)

    login(waiter_user.email)
    order = client.post("/v1/orders", json={"table_id": table["id"]}).json()
    client.post(
        f"/v1/orders/{order['id']}/items",
        json={"product_id": product["id"], "quantity": 1},
    )

    report = client.get("/v1/reports/daily").json()
    assert report["total"] == 0
    assert report["by_table"] == []
    assert report["by_product"] == []


def test_daily_report_requires_auth(client: TestClient) -> None:
    assert client.get("/v1/reports/daily").status_code == 401
