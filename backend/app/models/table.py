"""Modelo: tables (mesas del bar)."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.order import Order


class Table(TimestampMixin, Base):
    __tablename__ = "tables"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, server_default=text("gen_random_uuid()")
    )
    table_number: Mapped[int] = mapped_column(Integer, nullable=False, unique=True)
    label: Mapped[str | None] = mapped_column(String(80), nullable=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False, server_default=text("'free'"))

    orders: Mapped[list[Order]] = relationship(back_populates="table")

    __table_args__ = (CheckConstraint("status IN ('free','occupied')", name="ck_tables_status"),)
