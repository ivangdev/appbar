"""Tests de reglas de negocio corregidas (corte, mesa/orden, auditoria)."""

from __future__ import annotations

import datetime as dt
import uuid
from collections.abc import Callable
from zoneinfo import ZoneInfo

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.seed import seed
from app.models.order import Order
from app.models.payment import Payment
from app.models.user import User

BOGOTA = ZoneInfo("America/Bogota")


def _open_with_item(
    client: TestClient,
    menu: dict[str, object],
    login: Callable[[str], None],
    waiter: User,
    quantity: int = 2,
) -> tuple[dict[str, object], dict[str, object]]:
    table, product = menu["table"], menu["product"]
    assert isinstance(table, dict) and isinstance(product, dict)
    login(waiter.email)
    order = client.post("/v1/orders", json={"table_id": table["id"]}).json()
    item = client.post(
        f"/v1/orders/{order['id']}/items",
        json={"product_id": product["id"], "quantity": quantity},
    ).json()
    return order, item


# --------------------------------------------------------------- Health ready
def test_health_ready_with_db(client: TestClient) -> None:
    response = client.get("/health/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


# ----------------------------------------------------------- Corte por paid_at
def test_daily_report_uses_paid_at_not_created_at(
    client: TestClient,
    db_session: Session,
    menu: dict[str, object],
    waiter_user: User,
    login: Callable[[str], None],
) -> None:
    """Una orden pagada ayer no debe aparecer en el corte de hoy."""
    order, _ = _open_with_item(client, menu, login, waiter_user, quantity=2)
    client.post(
        f"/v1/orders/{order['id']}/pay",
        json={"amount": 10000, "method": "cash"},
    )

    db_order = db_session.get(Order, uuid.UUID(str(order["id"])))
    assert db_order is not None
    yesterday = dt.datetime.now(BOGOTA) - dt.timedelta(days=1)
    db_order.paid_at = yesterday
    # created_at sigue siendo hoy: el corte debe ignorar la orden igualmente.
    db_session.flush()

    today = dt.datetime.now(BOGOTA).date().isoformat()
    yesterday_str = yesterday.date().isoformat()

    assert client.get(f"/v1/reports/daily?date={today}").json()["total"] == 0
    assert client.get(f"/v1/reports/daily?date={yesterday_str}").json()["total"] == 10000


# ------------------------------------------------------- Invariante mesa/orden
def test_empty_order_keeps_table_occupied(
    client: TestClient,
    menu: dict[str, object],
    waiter_user: User,
    login: Callable[[str], None],
) -> None:
    """Quitar el ultimo item no libera la mesa: la orden sigue activa."""
    order, item = _open_with_item(client, menu, login, waiter_user, quantity=1)
    assert client.get("/v1/tables").json()[0]["status"] == "occupied"

    response = client.delete(f"/v1/orders/items/{item['id']}")
    assert response.status_code == 204

    tables = client.get("/v1/tables").json()
    assert tables[0]["status"] == "occupied"
    # La orden sigue abierta (vacia) y se puede seguir usando.
    active = client.get(f"/v1/orders?table_id={order['table_id']}")
    assert active.status_code == 200
    assert active.json()["status"] == "open"


def test_paying_everything_frees_table(
    client: TestClient,
    menu: dict[str, object],
    waiter_user: User,
    login: Callable[[str], None],
) -> None:
    order, _ = _open_with_item(client, menu, login, waiter_user, quantity=1)
    paid = client.post(
        f"/v1/orders/{order['id']}/pay",
        json={"amount": 5000, "method": "cash"},
    )
    assert paid.status_code == 200
    assert paid.json()["order"]["status"] == "paid"
    assert client.get("/v1/tables").json()[0]["status"] == "free"


# ------------------------------------------------- Cancelacion auditada (soft)
def test_cancel_payment_is_soft_and_audited(
    client: TestClient,
    db_session: Session,
    menu: dict[str, object],
    waiter_user: User,
    login: Callable[[str], None],
) -> None:
    order, item = _open_with_item(client, menu, login, waiter_user, quantity=2)
    assert isinstance(item, dict)
    paid = client.post(
        f"/v1/orders/{order['id']}/pay",
        json={
            "amount": 5000,
            "method": "cash",
            "allocations": [{"item_id": item["id"], "quantity": 1}],
        },
    ).json()
    payment_id = uuid.UUID(paid["payment"]["id"])

    cancelled = client.post(f"/v1/payments/{payment_id}/cancel")
    assert cancelled.status_code == 200
    body = cancelled.json()
    assert body["order"]["amount_paid"] == 0
    assert body["order"]["status"] == "closed"
    assert body["remaining"] == 10000

    # La fila sigue existiendo (auditoria): no se borra.
    payment = db_session.get(Payment, payment_id)
    assert payment is not None
    assert payment.cancelled_at is not None
    assert payment.cancelled_by is not None

    # El corte no cuenta el pago anulado.
    report = client.get("/v1/reports/daily").json()
    assert report["total"] == 0


def test_double_cancel_payment_conflict(
    client: TestClient,
    menu: dict[str, object],
    waiter_user: User,
    login: Callable[[str], None],
) -> None:
    order, _ = _open_with_item(client, menu, login, waiter_user, quantity=1)
    paid = client.post(
        f"/v1/orders/{order['id']}/pay",
        json={"amount": 5000, "method": "cash"},
    ).json()
    payment_id = paid["payment"]["id"]

    assert client.post(f"/v1/payments/{payment_id}/cancel").status_code == 200
    assert client.post(f"/v1/payments/{payment_id}/cancel").status_code == 409


def test_cancelled_payment_excluded_from_amount_paid(
    client: TestClient,
    menu: dict[str, object],
    waiter_user: User,
    login: Callable[[str], None],
) -> None:
    """Dos pagos parciales: anular uno deja el otro vigente."""
    order, item = _open_with_item(client, menu, login, waiter_user, quantity=2)
    assert isinstance(item, dict)

    first = client.post(
        f"/v1/orders/{order['id']}/pay",
        json={
            "amount": 5000,
            "method": "cash",
            "allocations": [{"item_id": item["id"], "quantity": 1}],
        },
    ).json()
    second = client.post(
        f"/v1/orders/{order['id']}/pay",
        json={
            "amount": 5000,
            "method": "nequi",
            "allocations": [{"item_id": item["id"], "quantity": 1}],
        },
    ).json()
    assert second["order"]["status"] == "paid"

    cancelled = client.post(f"/v1/payments/{first['payment']['id']}/cancel")
    assert cancelled.status_code == 200
    body = cancelled.json()
    assert body["order"]["amount_paid"] == 5000
    assert body["order"]["status"] == "partially_paid"
    assert body["order"]["paid_at"] is None
    assert client.get("/v1/tables").json()[0]["status"] == "occupied"


# ----------------------------------------------------------- Seed idempotente
def test_seed_is_idempotent(db_session: Session, monkeypatch: pytest.MonkeyPatch) -> None:
    email = f"seed-{uuid.uuid4().hex[:8]}@posbar.com"
    monkeypatch.setattr(settings, "INITIAL_ADMIN_EMAIL", email)
    monkeypatch.setattr(settings, "INITIAL_ADMIN_PASSWORD", "seed-password-123")
    monkeypatch.setattr(settings, "SEED_DEMO_USERS", False)

    assert seed(db_session) == [email]
    assert seed(db_session) == []
    users = db_session.scalars(select(User).where(User.email == email)).all()
    assert len(users) == 1


# ------------------------------------------------------- Orden cerrada vacia
def test_closed_order_cannot_be_left_empty(
    client: TestClient,
    menu: dict[str, object],
    waiter_user: User,
    login: Callable[[str], None],
) -> None:
    """Una orden cerrada no puede quedar vacia; se cancela explicitamente."""
    order, item = _open_with_item(client, menu, login, waiter_user, quantity=1)
    assert client.post(f"/v1/orders/{order['id']}/close").status_code == 200

    blocked = client.delete(f"/v1/orders/items/{item['id']}")
    assert blocked.status_code == 409

    cancelled = client.post(f"/v1/orders/{order['id']}/cancel")
    assert cancelled.status_code == 200
    assert cancelled.json()["status"] == "cancelled"
    assert client.get("/v1/tables").json()[0]["status"] == "free"


def test_partially_paid_order_cannot_be_cancelled(
    client: TestClient,
    menu: dict[str, object],
    waiter_user: User,
    login: Callable[[str], None],
) -> None:
    """Con pagos vigentes hay que anular los pagos antes de cancelar la orden."""
    order, item = _open_with_item(client, menu, login, waiter_user, quantity=2)
    assert isinstance(item, dict)
    client.post(
        f"/v1/orders/{order['id']}/pay",
        json={
            "amount": 5000,
            "method": "cash",
            "allocations": [{"item_id": item["id"], "quantity": 1}],
        },
    )
    assert client.post(f"/v1/orders/{order['id']}/cancel").status_code == 409
