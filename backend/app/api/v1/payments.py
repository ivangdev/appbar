"""Endpoints de pagos.

- POST /payments/{id}/cancel: anula el pago (soft-cancel), revierte sus
  asignaciones y recalcula la orden. El pago se conserva para auditoria.
"""

from __future__ import annotations

import datetime as dt
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.db import get_db
from app.models.order import OrderItem
from app.models.payment import Payment
from app.models.user import User
from app.schemas.order import OrderRead, PaymentCancelResponse
from app.services.orders import apply_payment_state, emit_order_events, remaining_of

router = APIRouter(prefix="/payments", tags=["payments"])

CurrentUser = Annotated[User, Depends(get_current_user)]
DbSession = Annotated[Session, Depends(get_db)]


@router.post("/{id}/cancel", response_model=PaymentCancelResponse)
def cancel_payment(
    id: uuid.UUID,  # noqa: A002
    db: DbSession,
    user: CurrentUser,
) -> PaymentCancelResponse:
    """Anula un pago: revierte sus asignaciones y recalcula la orden."""
    payment = db.get(Payment, id)
    if payment is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Pago no encontrado")
    if payment.cancelled_at is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "El pago ya esta cancelado")

    order = payment.order
    amount = payment.amount

    for allocation in payment.allocations:
        item = db.get(OrderItem, allocation.order_item_id)
        if item is not None:
            item.paid_quantity -= allocation.quantity

    payment.cancelled_at = dt.datetime.now(dt.UTC)
    payment.cancelled_by = user.id
    db.flush()

    apply_payment_state(order, order.table)
    db.commit()
    db.refresh(order)
    emit_order_events("payment_cancelled", order)
    return PaymentCancelResponse(
        cancelled=True,
        amount=amount,
        order=OrderRead.model_validate(order),
        remaining=remaining_of(order),
    )
