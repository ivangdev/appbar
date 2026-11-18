"""Schemas de ordenes (orders) y sus items."""

from __future__ import annotations

import datetime as dt
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, computed_field

from app.schemas.payment import PaymentRead


class OrderCreate(BaseModel):
    """Datos para abrir una orden sobre una mesa."""

    table_id: UUID = Field(description="ID de la mesa donde se abre la orden")


class OrderItemCreate(BaseModel):
    """Datos para agregar un item a una orden."""

    product_id: UUID
    quantity: int = Field(default=1, ge=1, le=999)
    notes: str | None = Field(default=None, max_length=255)


class OrderItemUpdate(BaseModel):
    """Datos para actualizar un item (cantidad y/o notas)."""

    quantity: int | None = Field(default=None, ge=1, le=999)
    notes: str | None = Field(default=None, max_length=255)


class OrderItemRead(BaseModel):
    """Item de una orden."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    order_id: UUID
    product_id: UUID
    quantity: int
    paid_quantity: int
    unit_price: int
    total_price: int
    notes: str | None


class OrderRead(BaseModel):
    """Orden completa con items y pagos; incluye el saldo pendiente."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    table_id: UUID
    user_id: UUID
    status: str
    subtotal: int
    total_amount: int
    amount_paid: int
    closed_at: dt.datetime | None
    paid_at: dt.datetime | None
    items: list[OrderItemRead] = Field(default_factory=list)
    payments: list[PaymentRead] = Field(default_factory=list)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def remaining(self) -> int:
        """Saldo pendiente = total - pagado."""
        return self.total_amount - self.amount_paid


class PaymentResult(BaseModel):
    """Resultado de registrar un pago."""

    payment: PaymentRead
    order: OrderRead
    remaining: int


class PaymentCancelResponse(BaseModel):
    """Resultado de cancelar un pago."""

    cancelled: bool = True
    amount: int
    order: OrderRead
    remaining: int
