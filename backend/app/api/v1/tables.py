"""Endpoints de mesas.

- GET: mesero/admin.
- POST/PATCH/DELETE: solo admin.
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_role
from app.core.db import get_db
from app.models.enums import UserRole
from app.models.order import Order
from app.models.table import Table
from app.models.user import User
from app.schemas.table import TableCreate, TableRead, TableUpdate

router = APIRouter(prefix="/tables", tags=["tables"])

AdminUser = Annotated[User, Depends(require_role(UserRole.ADMIN))]
CurrentUser = Annotated[User, Depends(get_current_user)]
DbSession = Annotated[Session, Depends(get_db)]


@router.get("", response_model=list[TableRead])
def list_tables(_user: CurrentUser, db: DbSession) -> list[Table]:
    """Lista todas las mesas ordenadas por numero."""
    return list(db.scalars(select(Table).order_by(Table.table_number)).all())


@router.post("", response_model=TableRead, status_code=status.HTTP_201_CREATED)
def create_table(payload: TableCreate, db: DbSession, _user: AdminUser) -> Table:
    """Crea una mesa (admin). 409 si el numero ya existe."""
    exists = db.scalar(select(Table).where(Table.table_number == payload.table_number))
    if exists is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "El numero de mesa ya existe")

    table = Table(table_number=payload.table_number, label=payload.label)
    db.add(table)
    db.commit()
    db.refresh(table)
    return table


@router.patch("/{id}", response_model=TableRead)
def update_table(
    id: uuid.UUID,  # noqa: A002
    payload: TableUpdate,
    db: DbSession,
    _user: AdminUser,
) -> Table:
    """Actualiza la etiqueta de una mesa (admin)."""
    table = db.get(Table, id)
    if table is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Mesa no encontrada")

    table.label = payload.label
    db.commit()
    db.refresh(table)
    return table


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_table(id: uuid.UUID, db: DbSession, _user: AdminUser) -> None:  # noqa: A002
    """Elimina una mesa (admin). 409 si tiene ordenes asociadas."""
    table = db.get(Table, id)
    if table is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Mesa no encontrada")

    has_orders = db.scalar(select(Order.id).where(Order.table_id == id).limit(1))
    if has_orders is not None:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "No se puede eliminar una mesa con ordenes asociadas",
        )

    db.delete(table)
    db.commit()
