"""Logica de negocio de ordenes y pagos.

Concentra el recalculo de montos y las transiciones de estado, de modo que
los routers solo orquesten. Reglas (PDR v1.3):

- `remaining = total_amount - amount_paid`.
- Estados activos: open, closed, partially_paid.
- Tras aplicar/quitar pagos: remaining == 0 y hay pagos -> `paid`;
  amount_paid > 0 -> `partially_paid`; sin pagos -> `closed`.
- La mesa queda `free` solo cuando el saldo pendiente es 0.
"""

from __future__ import annotations

import datetime as dt

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.websocket import broadcast_event
from app.models.enums import OrderStatus, TableStatus
from app.models.order import Order
from app.models.table import Table

ACTIVE_STATUSES = (
    OrderStatus.OPEN.value,
    OrderStatus.CLOSED.value,
    OrderStatus.PARTIALLY_PAID.value,
)


def remaining_of(order: Order) -> int:
    """Saldo pendiente de la orden."""
    return order.total_amount - order.amount_paid


def recalc_order(order: Order) -> None:
    """Recalcula subtotal, total y pagado a partir de items y pagos vigentes.

    Los pagos cancelados se conservan por auditoria pero NO suman a
    `amount_paid`.
    """
    order.subtotal = sum(item.total_price for item in order.items)
    order.total_amount = order.subtotal
    order.amount_paid = sum(
        payment.amount for payment in order.payments if payment.cancelled_at is None
    )


def apply_payment_state(order: Order, table: Table) -> None:
    """Ajusta estado de la orden y de la mesa segun los pagos aplicados.

    La mesa solo se libera cuando la orden queda pagada (o se cancela, lo que
    maneja el endpoint). Una orden activa vacia sigue manteniendo la mesa
    ocupada: si la mesa dijera "libre" pero existiera una orden activa, abrir
    otra daria 409 y el tablero mentiria.
    """
    recalc_order(order)
    remaining = remaining_of(order)

    if remaining == 0 and order.amount_paid > 0:
        order.status = OrderStatus.PAID.value
        if order.paid_at is None:
            order.paid_at = dt.datetime.now(dt.UTC)
    elif order.amount_paid > 0:
        order.status = OrderStatus.PARTIALLY_PAID.value
        order.paid_at = None
    elif order.status in (OrderStatus.PAID.value, OrderStatus.PARTIALLY_PAID.value):
        # Se quitaron/cancelaron todos los pagos: vuelve a 'closed'.
        order.status = OrderStatus.CLOSED.value
        order.paid_at = None

    is_paid = order.status == OrderStatus.PAID.value
    table.status = TableStatus.FREE.value if is_paid else TableStatus.OCCUPIED.value


def active_order_for_table(db: Session, table_id: object) -> Order | None:
    """Devuelve la orden activa de una mesa, si existe."""
    stmt = select(Order).where(
        Order.table_id == table_id,
        Order.status.in_(ACTIVE_STATUSES),
    )
    return db.scalar(stmt)


def order_event(event_type: str, order: Order) -> dict[str, object]:
    """Payload WebSocket con el estado de la orden y su mesa."""
    table = order.table
    return {
        "type": event_type,
        "data": {
            "order_id": str(order.id),
            "table_id": str(order.table_id),
            "table_number": table.table_number,
            "status": order.status,
            "table_status": table.status,
            "total_amount": order.total_amount,
            "amount_paid": order.amount_paid,
            "remaining": remaining_of(order),
        },
    }


def table_event(order: Order) -> dict[str, object]:
    """Payload WebSocket con el estado de la mesa."""
    table = order.table
    return {
        "type": "table_status_update",
        "data": {
            "table_id": str(table.id),
            "table_number": table.table_number,
            "status": table.status,
        },
    }


def emit_order_events(event_type: str, order: Order) -> None:
    """Difunde el evento de la orden y el estado de su mesa."""
    broadcast_event(order_event(event_type, order))
    broadcast_event(table_event(order))
