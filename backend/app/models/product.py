"""Modelo: products (productos del catalogo)."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.category import Category


class Product(TimestampMixin, Base):
    __tablename__ = "products"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, server_default=text("gen_random_uuid()")
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    category_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("categories.id"), nullable=False, index=True
    )
    price: Mapped[int] = mapped_column(Integer, nullable=False)
    cost: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    sku: Mapped[str | None] = mapped_column(String(64), nullable=True, unique=True)
    is_active: Mapped[bool] = mapped_column(nullable=False, server_default=text("true"))

    category: Mapped[Category] = relationship(back_populates="products")

    __table_args__ = (
        CheckConstraint("price >= 0", name="ck_products_price"),
        CheckConstraint("cost >= 0", name="ck_products_cost"),
    )
