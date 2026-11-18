"""Endpoints de categorias del catalogo.

- GET: mesero/admin (el mesero solo ve activas).
- POST/PUT/DELETE: solo admin.
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_role
from app.core.db import get_db
from app.models.category import Category
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.category import CategoryCreate, CategoryRead

router = APIRouter(prefix="/categories", tags=["categories"])

AdminUser = Annotated[User, Depends(require_role(UserRole.ADMIN))]
CurrentUser = Annotated[User, Depends(get_current_user)]
DbSession = Annotated[Session, Depends(get_db)]


@router.get("", response_model=list[CategoryRead])
def list_categories(user: CurrentUser, db: DbSession) -> list[Category]:
    """Lista categorias ordenadas. El mesero solo ve las activas."""
    stmt = select(Category).order_by(Category.sort_order, Category.name)
    if user.role != UserRole.ADMIN.value:
        stmt = stmt.where(Category.is_active.is_(True))
    return list(db.scalars(stmt).all())


@router.post("", response_model=CategoryRead, status_code=status.HTTP_201_CREATED)
def create_category(payload: CategoryCreate, db: DbSession, _user: AdminUser) -> Category:
    """Crea una categoria (admin). 409 si el nombre ya existe."""
    exists = db.scalar(select(Category).where(Category.name == payload.name))
    if exists is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "La categoria ya existe")

    category = Category(name=payload.name, sort_order=payload.sort_order)
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


@router.put("/{id}", response_model=CategoryRead)
def update_category(
    id: uuid.UUID,  # noqa: A002
    payload: CategoryCreate,
    db: DbSession,
    _user: AdminUser,
) -> Category:
    """Actualiza una categoria (admin)."""
    category = db.get(Category, id)
    if category is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Categoria no encontrada")

    duplicate = db.scalar(select(Category).where(Category.name == payload.name, Category.id != id))
    if duplicate is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "La categoria ya existe")

    category.name = payload.name
    category.sort_order = payload.sort_order
    db.commit()
    db.refresh(category)
    return category


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(id: uuid.UUID, db: DbSession, _user: AdminUser) -> None:  # noqa: A002
    """Soft-delete de una categoria (admin): is_active = False."""
    category = db.get(Category, id)
    if category is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Categoria no encontrada")

    category.is_active = False
    db.commit()
