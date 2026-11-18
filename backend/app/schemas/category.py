"""Schemas de categorias."""

from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict, Field


class CategoryCreate(BaseModel):
    """Datos para crear/actualizar una categoria."""

    name: str = Field(min_length=1, max_length=120)
    sort_order: int = Field(default=0, ge=0)


class CategoryRead(BaseModel):
    """Categoria devuelta al cliente."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    is_active: bool
    sort_order: int
