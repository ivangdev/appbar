"""Endpoints de pagos.

- POST /payments/{id}/cancel: revierte las asignaciones y recalcula la orden.
"""

from __future__ import annotations

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
def cancel_payment(id: uuid.UUID, db: DbSession, _user: CurrentUser) -> PaymentCancelResponse:  # noqa: A002
    """Cancela un pago: revierte sus asignaciones y recalcula la orden."""
    payment = db.get(Payment, id)
    if payment is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Pago no encontrado")

    order = payment.order
    amount = payment.amount

    for allocation in list(payment.allocations):
        item = db.get(OrderItem, allocation.order_item_id)
        if item is not None:
            item.paid_quantity -= allocation.quantity

    order.payments.remove(payment)
    db.delete(payment)
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
