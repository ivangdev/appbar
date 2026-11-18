"""Modelos: payments y payment_allocations.

- payments: cada pago (parcial o total) registrado en una orden.
- payment_allocations: a que item y cantidad se aplico ese pago (los "pokers").
"""

from __future__ import annotations

import datetime as dt
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.models.base import CreatedAtMixin

if TYPE_CHECKING:
    from app.models.order import Order, OrderItem
    from app.models.user import User


class Payment(CreatedAtMixin, Base):
    __tablename__ = "payments"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, server_default=text("gen_random_uuid()")
    )
    order_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True
    )
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    method: Mapped[str] = mapped_column(String(16), nullable=False)
    reference: Mapped[str | None] = mapped_column(String(120), nullable=True)
    payment_date: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    # Cancelacion auditada: el pago NO se borra, se marca como anulado.
    cancelled_at: Mapped[dt.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    cancelled_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)

    order: Mapped[Order] = relationship(back_populates="payments")
    user: Mapped[User] = relationship(foreign_keys=[user_id])
    cancelled_by_user: Mapped[User | None] = relationship(foreign_keys=[cancelled_by])
    allocations: Mapped[list[PaymentAllocation]] = relationship(
        back_populates="payment", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint("method IN ('cash','nequi','transfer')", name="ck_payments_method"),
        CheckConstraint("amount > 0", name="ck_payments_amount"),
    )


class PaymentAllocation(CreatedAtMixin, Base):
    __tablename__ = "payment_allocations"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, server_default=text("gen_random_uuid()")
    )
    payment_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("payments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    order_item_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("order_items.id", ondelete="CASCADE"), nullable=False, index=True
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)

    payment: Mapped[Payment] = relationship(back_populates="allocations")
    order_item: Mapped[OrderItem] = relationship()

    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_allocations_quantity"),
        CheckConstraint("amount >= 0", name="ck_allocations_amount"),
    )
