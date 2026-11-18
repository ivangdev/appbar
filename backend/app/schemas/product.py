"""Schemas de productos.

`cost` (precio de compra) solo se incluye para el rol admin: el mesero
recibe `ProductRead` (sin cost), el admin recibe `ProductReadAdmin` (con cost).
"""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ProductCreate(BaseModel):
    """Datos para crear/actualizar un producto (solo admin)."""

    name: str = Field(
        min_length=1,
        max_length=150,
        description="Nombre del producto (ej: Cerveza Artesanal)",
    )

    category_id: UUID = Field(
        description="ID de la categoría a la que pertenece",
    )

    price: int = Field(
        ge=0,
        le=10_000_000,
        description="Precio de venta al público en pesos COP (entero)",
    )

    cost: int = Field(
        default=0,
        ge=0,
        le=10_000_000,
        description="Precio de costo/margen en pesos COP (solo admin; el mesero nunca lo ve)",
    )

    sku: str | None = Field(
        default=None,
        max_length=64,
        pattern=r"^[A-Z0-9_-]+$",
        description="SKU único del producto (formato: mayúsculas, números, guión, underline)",
    )


class ProductRead(BaseModel):
    """Producto visible para el mesero (SIN cost)."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    category_id: UUID
    price: int
    sku: str | None
    is_active: bool


class ProductUpdate(BaseModel):
    """Actualizacion parcial de un producto (solo admin).

    Permite editar precio/costo/SKU, mover de categoria y reactivar
    (is_active=True) un producto con soft-delete.
    """

    name: str | None = Field(default=None, min_length=1, max_length=150)
    category_id: UUID | None = None
    price: int | None = Field(default=None, ge=0, le=10_000_000)
    cost: int | None = Field(default=None, ge=0, le=10_000_000)
    sku: str | None = Field(default=None, max_length=64, pattern=r"^[A-Z0-9_-]+$")
    is_active: bool | None = None


class ProductReadAdmin(ProductRead):
    """Producto visible para el admin (incluye cost)."""

    cost: int
