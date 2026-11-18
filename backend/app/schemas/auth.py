"""Schemas de autenticacion."""

from __future__ import annotations

from pydantic import BaseModel, EmailStr


class UserLogin(BaseModel):
    """Credenciales de login."""

    email: EmailStr
    password: str


class Token(BaseModel):
    """Respuesta del login (el token tambien viaja en cookie HttpOnly)."""

    access_token: str
    token_type: str = "bearer"
