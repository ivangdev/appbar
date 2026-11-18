"""Dependencias compartidas de FastAPI.

- get_current_user: lee el JWT de la cookie HttpOnly y devuelve el usuario.
- require_role: fabrica de dependencias que exige uno o varios roles.
"""

from __future__ import annotations

import uuid
from collections.abc import Callable
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import ACCESS_COOKIE_NAME, decode_access_token
from app.models.enums import UserRole
from app.models.user import User

_CREDENTIALS_ERROR = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="No autenticado",
    headers={"WWW-Authenticate": "Cookie"},
)


def get_current_user(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
) -> User:
    """Devuelve el usuario autenticado a partir de la cookie JWT."""
    token = request.cookies.get(ACCESS_COOKIE_NAME)
    if not token:
        raise _CREDENTIALS_ERROR

    try:
        payload = decode_access_token(token)
    except jwt.PyJWTError as exc:
        raise _CREDENTIALS_ERROR from exc

    subject = payload.get("sub")
    if not subject:
        raise _CREDENTIALS_ERROR

    try:
        user_id = uuid.UUID(str(subject))
    except ValueError as exc:
        raise _CREDENTIALS_ERROR from exc

    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise _CREDENTIALS_ERROR

    return user


def require_role(*roles: UserRole) -> Callable[..., User]:
    """Dependencia que exige que el usuario tenga uno de los roles dados."""
    allowed = {role.value for role in roles}

    def checker(user: Annotated[User, Depends(get_current_user)]) -> User:
        if user.role not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permisos insuficientes",
            )
        return user

    return checker
