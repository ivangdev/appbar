"""Endpoints de usuarios (solo admin).

- GET: lista usuarios.
- POST: crea un usuario (mesero o admin).
- PATCH: edita nombre/email/rol/estado.
- DELETE: desactiva (soft) un usuario.
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.core.db import get_db
from app.core.security import hash_password
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.user import UserCreate, UserRead, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])

AdminUser = Annotated[User, Depends(require_role(UserRole.ADMIN))]
DbSession = Annotated[Session, Depends(get_db)]


def _find_by_email(db: Session, email: str, exclude_id: uuid.UUID | None = None) -> User | None:
    stmt = select(User).where(func.lower(User.email) == email.lower())
    if exclude_id is not None:
        stmt = stmt.where(User.id != exclude_id)
    return db.scalar(stmt)


@router.get("", response_model=list[UserRead])
def list_users(_user: AdminUser, db: DbSession) -> list[User]:
    """Lista todos los usuarios (admin)."""
    return list(db.scalars(select(User).order_by(User.name)).all())


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreate, db: DbSession, _user: AdminUser) -> User:
    """Crea un usuario (admin). 409 si el email ya existe."""
    if _find_by_email(db, payload.email) is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "El email ya esta registrado")

    user = User(
        name=payload.name,
        email=payload.email.lower(),
        password_hash=hash_password(payload.password),
        role=payload.role.value,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.patch("/{id}", response_model=UserRead)
def update_user(
    id: uuid.UUID,  # noqa: A002
    payload: UserUpdate,
    db: DbSession,
    _user: AdminUser,
) -> User:
    """Edita un usuario (admin). 409 si el email ya esta en uso."""
    user = db.get(User, id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Usuario no encontrado")

    if payload.email is not None:
        if _find_by_email(db, payload.email, exclude_id=id) is not None:
            raise HTTPException(status.HTTP_409_CONFLICT, "El email ya esta registrado")
        user.email = payload.email.lower()

    if payload.name is not None:
        user.name = payload.name
    if payload.role is not None:
        user.role = payload.role.value
    if payload.is_active is not None:
        user.is_active = payload.is_active

    db.commit()
    db.refresh(user)
    return user


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def deactivate_user(id: uuid.UUID, db: DbSession, user: AdminUser) -> None:  # noqa: A002
    """Desactiva un usuario (admin). No permite desactivarse a si mismo."""
    if id == user.id:
        raise HTTPException(status.HTTP_409_CONFLICT, "No puedes desactivar tu propio usuario")

    target = db.get(User, id)
    if target is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Usuario no encontrado")

    target.is_active = False
    db.commit()
