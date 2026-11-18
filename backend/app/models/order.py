"""Modelos: orders y order_items (ordenes y sus lineas)."""

from __future__ import annotations

import datetime as dt
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.models.base import CreatedAtMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.payment import Payment
    from app.models.product import Product
    from app.models.table import Table
    from app.models.user import User


class Order(TimestampMixin, Base):
    __tablename__ = "orders"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, server_default=text("gen_random_uuid()")
    )
    table_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tables.id"), nullable=False, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default=text("'open'"))
    subtotal: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    total_amount: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    amount_paid: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    closed_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    paid_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    table: Mapped[Table] = relationship(back_populates="orders")
    user: Mapped[User] = relationship()
    items: Mapped[list[OrderItem]] = relationship(
        back_populates="order", cascade="all, delete-orphan"
    )
    payments: Mapped[list[Payment]] = relationship(
        back_populates="order", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('open','closed','partially_paid','paid','cancelled')",
            name="ck_orders_status",
        ),
        # Una sola orden ACTIVA por mesa (regla del PDR v1.3)
        Index(
            "ux_orders_one_active_per_table",
            "table_id",
            unique=True,
            postgresql_where=text("status IN ('open','closed','partially_paid')"),
        ),
    )


class OrderItem(CreatedAtMixin, Base):
    __tablename__ = "order_items"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, server_default=text("gen_random_uuid()")
    )
    order_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True
    )
    product_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("products.id"), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("1"))
    paid_quantity: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    unit_price: Mapped[int] = mapped_column(Integer, nullable=False)
    total_price: Mapped[int] = mapped_column(Integer, nullable=False)
    notes: Mapped[str | None] = mapped_column(String(255), nullable=True)

    order: Mapped[Order] = relationship(back_populates="items")
    product: Mapped[Product] = relationship()

    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_order_items_quantity"),
        CheckConstraint(
            "paid_quantity >= 0 AND paid_quantity <= quantity",
            name="ck_order_items_paid_quantity",
        ),
    )
