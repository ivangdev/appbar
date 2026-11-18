"""Endpoints de autenticacion: login, logout y usuario actual.

La sesion viaja en una cookie HttpOnly (`access_token`); el token nunca se
expone en la URL ni en el cuerpo mas alla del login.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.constants import AUTH_RATE_LIMIT
from app.core.db import get_db
from app.core.rate_limit import limiter
from app.core.security import ACCESS_COOKIE_NAME, create_access_token, verify_password
from app.models.user import User
from app.schemas.auth import Token, UserLogin
from app.schemas.user import UserRead

router = APIRouter(prefix="/auth", tags=["auth"])

CurrentUser = Annotated[User, Depends(get_current_user)]
DbSession = Annotated[Session, Depends(get_db)]


def _set_auth_cookie(response: Response, token: str) -> None:
    """Setea la cookie HttpOnly con el JWT."""
    response.set_cookie(
        key=ACCESS_COOKIE_NAME,
        value=token,
        max_age=settings.ACCESS_TOKEN_EXPIRE_HOURS * 3600,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite="lax",
        path="/",
    )


@router.post("/token", response_model=Token)
@limiter.limit(AUTH_RATE_LIMIT)
def login(request: Request, payload: UserLogin, response: Response, db: DbSession) -> Token:
    """Valida credenciales, emite el JWT y lo setea en cookie HttpOnly."""
    email = payload.email.strip().lower()
    user = db.scalar(select(User).where(func.lower(User.email) == email))
    if (
        user is None
        or not user.is_active
        or not verify_password(payload.password, user.password_hash)
    ):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Credenciales invalidas")

    token = create_access_token(str(user.id), user.role)
    _set_auth_cookie(response, token)
    return Token(access_token=token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response) -> None:
    """Borra la cookie de sesion."""
    response.delete_cookie(ACCESS_COOKIE_NAME, path="/")


@router.get("/me", response_model=UserRead)
def me(user: CurrentUser) -> User:
    """Devuelve el usuario autenticado."""
    return user
