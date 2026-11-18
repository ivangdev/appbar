"""Schemas de pagos (payments) y asignaciones a items (allocations)."""

from __future__ import annotations

import datetime as dt
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import PaymentMethod


class AllocationInput(BaseModel):
    """Asignacion de una cantidad de un item a un pago parcial (poker)."""

    item_id: UUID = Field(description="ID del item de la orden cubierto")
    quantity: int = Field(ge=1, le=999, description="Cantidad de unidades que cubre este pago")


class OrderPayment(BaseModel):
    """Datos para registrar un pago.

    - Con `allocations`: pago parcial que cubre cantidades especificas.
    - Sin `allocations`: pago total que cubre todo lo pendiente.
    """

    amount: int = Field(gt=0, le=100_000_000, description="Monto en pesos COP (entero)")
    method: PaymentMethod = Field(description="Metodo de pago")
    reference: str | None = Field(
        default=None,
        max_length=120,
        description="Referencia opcional (ej: numero de transaccion)",
    )
    allocations: list[AllocationInput] | None = Field(
        default=None,
        description="Detalle de items cubiertos (pago parcial). Vacio/omitido = pago total.",
    )


class AllocationRead(BaseModel):
    """Asignacion de un pago a un item."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    item_id: UUID = Field(validation_alias="order_item_id")
    quantity: int
    amount: int


class PaymentRead(BaseModel):
    """Pago tal como se devuelve al cliente."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    order_id: UUID
    amount: int
    method: str
    reference: str | None
    payment_date: dt.datetime
    user_id: UUID
    allocations: list[AllocationRead] = Field(default_factory=list)
