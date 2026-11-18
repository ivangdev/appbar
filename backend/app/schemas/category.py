"""Schemas de categorias."""

from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict, Field


class CategoryCreate(BaseModel):
    """Datos para crear/actualizar una categoria."""

    name: str = Field(min_length=1, max_length=120)
    sort_order: int = Field(default=0, ge=0)


class CategoryUpdate(BaseModel):
    """Actualizacion parcial de una categoria (admin)."""

    name: str | None = Field(default=None, min_length=1, max_length=120)
    sort_order: int | None = Field(default=None, ge=0)
    is_active: bool | None = None


class CategoryRead(BaseModel):
    """Categoria devuelta al cliente."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    is_active: bool
    sort_order: int
