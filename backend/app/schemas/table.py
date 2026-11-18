"""Schemas de mesas (tables)."""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class TableCreate(BaseModel):
    """Datos para crear una mesa (solo admin)."""

    table_number: int = Field(
        ge=1,
        le=999,
        description="Numero identificador de la mesa (unico)",
    )
    label: str | None = Field(
        default=None,
        max_length=80,
        description="Etiqueta opcional (ej: 'Terraza 1')",
    )


class TableUpdate(BaseModel):
    """Datos para actualizar una mesa (solo admin)."""

    label: str | None = Field(
        default=None,
        max_length=80,
        description="Etiqueta opcional de la mesa",
    )


class TableRead(BaseModel):
    """Mesa tal como se devuelve al cliente."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    table_number: int
    label: str | None
    status: str
