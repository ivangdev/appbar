"""Schemas de usuarios (entrada/salida de la API)."""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models.enums import UserRole


class UserRead(BaseModel):
    """Usuario tal como se devuelve al cliente (sin password)."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    email: EmailStr
    role: UserRole
    is_active: bool


class UserCreate(BaseModel):
    """Datos para crear un usuario (solo admin)."""

    name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: UserRole = UserRole.WAITER

    @field_validator("email")
    @classmethod
    def _lowercase_email(cls, v: str) -> str:
        """Normaliza el email a minusculas."""
        return v.lower()


class UserUpdate(BaseModel):
    """Actualizacion parcial de usuario (solo admin)."""

    name: str | None = Field(default=None, min_length=1, max_length=120)
    email: EmailStr | None = None
    role: UserRole | None = None
    is_active: bool | None = None
    password: str | None = Field(default=None, min_length=8, max_length=128)

    @field_validator("email")
    @classmethod
    def _lowercase_email(cls, v: str | None) -> str | None:
        """Normaliza el email a minusculas si viene presente."""
        return v.lower() if v is not None else v
