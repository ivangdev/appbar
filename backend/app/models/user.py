"""Modelo: users (admins y meseros)."""

import uuid

from sqlalchemy import Boolean, CheckConstraint, Index, String, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models.base import TimestampMixin


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, server_default=text("gen_random_uuid()")
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(16), nullable=False, server_default=text("'waiter'"))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))

    __table_args__ = (
        CheckConstraint("role IN ('admin','waiter')", name="ck_users_role"),
        # email unico sin distinguir mayusculas/minusculas (regla del PDR)
        Index("ux_users_email_ci", func.lower(email), unique=True),
    )
