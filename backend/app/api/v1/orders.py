"""Endpoints de ordenes, items y pagos.

Reglas (PDR v1.3): montos en pesos COP enteros; `remaining = total - pagado`;
mesa libre solo con saldo 0.
"""

from __future__ import annotations

import datetime as dt
import uuid
from typing import Annotated
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.constants import WRITE_RATE_LIMIT
from app.core.db import get_db
from app.core.rate_limit import limiter
from app.models.order import Order, OrderItem
from app.models.payment import Payment, PaymentAllocation
from app.models.product import Product
from app.models.table import Table
from app.models.user import User
from app.schemas.order import (
    OrderCreate,
    OrderItemCreate,
    OrderItemRead,
    OrderItemUpdate,
    OrderRead,
    PaymentResult,
)
from app.schemas.payment import OrderPayment, PaymentRead
from app.services.orders import (
    ACTIVE_STATUSES,
    active_order_for_table,
    apply_payment_state,
    emit_order_events,
    recalc_order,
    remaining_of,
)

router = APIRouter(prefix="/orders", tags=["orders"])

CurrentUser = Annotated[User, Depends(get_current_user)]
DbSession = Annotated[Session, Depends(get_db)]

BOGOTA = ZoneInfo("America/Bogota")


def _get_active_or_404(db: Session, order_id: uuid.UUID) -> Order:
    order = db.get(Order, order_id)
    if order is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Orden no encontrada")
    return order


@router.get("", response_model=OrderRead)
def get_active_order(
    _user: CurrentUser,
    db: DbSession,
    table_id: Annotated[uuid.UUID, Query(description="ID de la mesa")],
) -> Order:
    """Orden activa de una mesa. 404 si la mesa no tiene orden activa."""
    order = active_order_for_table(db, table_id)
    if order is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "La mesa no tiene orden activa")
    return order


@router.post("", response_model=OrderRead, status_code=status.HTTP_201_CREATED)
def create_order(payload: OrderCreate, db: DbSession, user: CurrentUser) -> Order:
    """Abre una orden en una mesa libre. 409 si ya tiene una activa."""
    table = db.get(Table, payload.table_id)
    if table is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Mesa no encontrada")

    if active_order_for_table(db, table.id) is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "La mesa ya tiene una orden activa")

    order = Order(table_id=table.id, user_id=user.id, status="open")
    db.add(order)
    table.status = "occupied"
    db.commit()
    db.refresh(order)
    emit_order_events("new_order", order)
    return order


@router.get("/history", response_model=list[OrderRead])
def order_history(
    _user: CurrentUser,
    db: DbSession,
    date: Annotated[dt.date | None, Query()] = None,
) -> list[Order]:
    """Ordenes del dia (TZ America/Bogota), mas recientes primero."""
    day = date or dt.datetime.now(BOGOTA).date()
    start = dt.datetime.combine(day, dt.time.min, tzinfo=BOGOTA)
    end = start + dt.timedelta(days=1)
    stmt = (
        select(Order)
        .where(Order.created_at >= start, Order.created_at < end)
        .order_by(Order.created_at.desc())
    )
    return list(db.scalars(stmt).all())


@router.post("/{id}/close", response_model=OrderRead)
def close_order(id: uuid.UUID, db: DbSession, _user: CurrentUser) -> Order:  # noqa: A002
    """Cierra una orden (open -> closed). La mesa sigue ocupada."""
    order = _get_active_or_404(db, id)
    if order.status != "open":
        raise HTTPException(status.HTTP_409_CONFLICT, "Solo se puede cerrar una orden 'open'")
    if not order.items:
        raise HTTPException(status.HTTP_409_CONFLICT, "La orden no tiene items")

    order.status = "closed"
    order.closed_at = dt.datetime.now(dt.UTC)
    db.commit()
    db.refresh(order)
    emit_order_events("order_closed", order)
    return order


@router.post("/{id}/cancel", response_model=OrderRead)
def cancel_order(id: uuid.UUID, db: DbSession, _user: CurrentUser) -> Order:  # noqa: A002
    """Cancela una orden sin pagos (open o closed). La mesa queda libre."""
    order = _get_active_or_404(db, id)
    if order.status not in ("open", "closed"):
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Solo se puede cancelar una orden 'open' o 'closed' sin pagos",
        )
    recalc_order(order)
    if order.amount_paid > 0:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "La orden tiene pagos: anula primero los pagos",
        )

    order.status = "cancelled"
    order.table.status = "free"
    db.commit()
    db.refresh(order)
    emit_order_events("order_cancelled", order)
    return order


@router.post("/{id}/items", response_model=OrderItemRead, status_code=status.HTTP_201_CREATED)
def add_item(
    id: uuid.UUID,  # noqa: A002
    payload: OrderItemCreate,
    db: DbSession,
    _user: CurrentUser,
) -> OrderItem:
    """Agrega un item a una orden activa."""
    order = _get_active_or_404(db, id)
    if order.status not in ACTIVE_STATUSES:
        raise HTTPException(status.HTTP_409_CONFLICT, "La orden no permite cambios")

    product = db.get(Product, payload.product_id)
    if product is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Producto no encontrado")
    if not product.is_active:
        raise HTTPException(status.HTTP_409_CONFLICT, "El producto esta inactivo")

    item = OrderItem(
        order_id=order.id,
        product_id=product.id,
        quantity=payload.quantity,
        unit_price=product.price,
        total_price=product.price * payload.quantity,
        notes=payload.notes,
    )
    db.add(item)
    db.flush()
    apply_payment_state(order, order.table)
    db.commit()
    db.refresh(item)
    db.refresh(order)
    emit_order_events("order_updated", order)
    return item


@router.patch("/items/{item_id}", response_model=OrderItemRead)
def update_item(
    item_id: uuid.UUID,
    payload: OrderItemUpdate,
    db: DbSession,
    _user: CurrentUser,
) -> OrderItem:
    """Edita cantidad/notas de un item. 409 si quantity < paid_quantity."""
    item = db.get(OrderItem, item_id)
    if item is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Item no encontrado")

    order = item.order
    if order.status not in ACTIVE_STATUSES:
        raise HTTPException(status.HTTP_409_CONFLICT, "La orden no permite cambios")

    if payload.quantity is not None:
        if payload.quantity < item.paid_quantity:
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                "La cantidad no puede ser menor que lo ya pagado",
            )
        item.quantity = payload.quantity
        item.total_price = item.unit_price * payload.quantity

    if "notes" in payload.model_fields_set:
        item.notes = payload.notes

    db.flush()
    apply_payment_state(order, order.table)
    db.commit()
    db.refresh(item)
    db.refresh(order)
    emit_order_events("order_updated", order)
    return item


@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(item_id: uuid.UUID, db: DbSession, _user: CurrentUser) -> None:
    """Quita un item. 409 si el item ya tiene pagos aplicados."""
    item = db.get(OrderItem, item_id)
    if item is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Item no encontrado")

    order = item.order
    if order.status not in ACTIVE_STATUSES:
        raise HTTPException(status.HTTP_409_CONFLICT, "La orden no permite cambios")
    if item.paid_quantity > 0:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "No se puede quitar un item que ya tiene pagos",
        )
    if order.status != "open" and len(order.items) == 1:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Una orden cerrada no puede quedar vacia: cancela la orden",
        )

    db.delete(item)
    db.flush()
    apply_payment_state(order, order.table)
    db.commit()
    emit_order_events("order_updated", order)


@router.post("/{id}/pay", response_model=PaymentResult)
@limiter.limit(WRITE_RATE_LIMIT)
def pay_order(
    request: Request,
    id: uuid.UUID,  # noqa: A002
    payload: OrderPayment,
    db: DbSession,
    user: CurrentUser,
) -> PaymentResult:
    """Registra un pago parcial (con allocations) o total (sin allocations)."""
    order = _get_active_or_404(db, id)
    if order.status not in ACTIVE_STATUSES:
        raise HTTPException(status.HTTP_409_CONFLICT, "La orden no esta activa")

    recalc_order(order)
    remaining = remaining_of(order)
    if remaining <= 0:
        raise HTTPException(status.HTTP_409_CONFLICT, "La orden no tiene saldo pendiente")

    planned: list[tuple[OrderItem, int]] = []
    allocations = payload.allocations or []
    if allocations:
        seen: set[uuid.UUID] = set()
        allocated_total = 0
        for alloc in allocations:
            item = next((i for i in order.items if i.id == alloc.item_id), None)
            if item is None:
                raise HTTPException(
                    status.HTTP_409_CONFLICT, "La asignacion referencia un item ajeno"
                )
            if item.id in seen:
                raise HTTPException(status.HTTP_409_CONFLICT, "Item duplicado en las asignaciones")
            seen.add(item.id)
            pending = item.quantity - item.paid_quantity
            if alloc.quantity > pending:
                raise HTTPException(
                    status.HTTP_409_CONFLICT,
                    "La cantidad asignada excede lo pendiente del item",
                )
            allocated_total += item.unit_price * alloc.quantity
            planned.append((item, alloc.quantity))

        if allocated_total != payload.amount:
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                "El monto no coincide con las asignaciones",
            )
        if allocated_total > remaining:
            raise HTTPException(status.HTTP_409_CONFLICT, "El pago excede el saldo pendiente")
    else:
        if payload.amount != remaining:
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                "El pago total debe cubrir exactamente el saldo pendiente",
            )
        planned = [
            (item, item.quantity - item.paid_quantity)
            for item in order.items
            if item.quantity - item.paid_quantity > 0
        ]
        if not planned:
            raise HTTPException(status.HTTP_409_CONFLICT, "No hay items pendientes de pago")

    payment = Payment(
        amount=payload.amount,
        method=payload.method.value,
        reference=payload.reference,
        user_id=user.id,
    )
    order.payments.append(payment)
    db.flush()

    for item, qty in planned:
        payment.allocations.append(
            PaymentAllocation(
                order_item_id=item.id,
                quantity=qty,
                amount=item.unit_price * qty,
            )
        )
        item.paid_quantity += qty

    apply_payment_state(order, order.table)
    db.commit()
    db.refresh(payment)
    db.refresh(order)
    emit_order_events("payment_made", order)
    if order.status == "paid":
        emit_order_events("order_paid", order)
    return PaymentResult(
        payment=PaymentRead.model_validate(payment),
        order=OrderRead.model_validate(order),
        remaining=remaining_of(order),
    )
