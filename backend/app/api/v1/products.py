"""Endpoints de productos del catalogo.

- GET: mesero/admin. El mesero NO recibe `cost` (solo price).
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
from app.models.product import Product
from app.models.user import User
from app.schemas.product import (
    ProductCreate,
    ProductRead,
    ProductReadAdmin,
)

router = APIRouter(prefix="/products", tags=["products"])

AdminUser = Annotated[User, Depends(require_role(UserRole.ADMIN))]
CurrentUser = Annotated[User, Depends(get_current_user)]
DbSession = Annotated[Session, Depends(get_db)]


def _serialize(product: Product, include_cost: bool) -> ProductRead | ProductReadAdmin:
    """Devuelve el schema con o sin `cost` segun el rol."""
    if include_cost:
        return ProductReadAdmin.model_validate(product)
    return ProductRead.model_validate(product)


@router.get("", response_model=list[ProductRead | ProductReadAdmin])
def list_products(
    user: CurrentUser,
    db: DbSession,
    category_id: uuid.UUID | None = None,
) -> list[ProductRead | ProductReadAdmin]:
    """Lista productos (filtrable por categoria). El mesero solo ve activos y sin cost."""
    stmt = select(Product).order_by(Product.name)
    if category_id is not None:
        stmt = stmt.where(Product.category_id == category_id)

    is_admin = user.role == UserRole.ADMIN.value
    if not is_admin:
        stmt = stmt.where(Product.is_active.is_(True))

    products = db.scalars(stmt).all()
    return [_serialize(product, is_admin) for product in products]


@router.post("", response_model=ProductReadAdmin, status_code=status.HTTP_201_CREATED)
def create_product(payload: ProductCreate, db: DbSession, _user: AdminUser) -> Product:
    """Crea un producto (admin)."""
    if db.get(Category, payload.category_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Categoria no encontrada")

    if payload.sku is not None:
        duplicate = db.scalar(select(Product).where(Product.sku == payload.sku))
        if duplicate is not None:
            raise HTTPException(status.HTTP_409_CONFLICT, "El SKU ya existe")

    product = Product(
        name=payload.name,
        category_id=payload.category_id,
        price=payload.price,
        cost=payload.cost,
        sku=payload.sku,
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@router.put("/{id}", response_model=ProductReadAdmin)
def update_product(
    id: uuid.UUID,  # noqa: A002
    payload: ProductCreate,
    db: DbSession,
    _user: AdminUser,
) -> Product:
    """Actualiza un producto (admin)."""
    product = db.get(Product, id)
    if product is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Producto no encontrado")

    if db.get(Category, payload.category_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Categoria no encontrada")

    if payload.sku is not None:
        duplicate = db.scalar(select(Product).where(Product.sku == payload.sku, Product.id != id))
        if duplicate is not None:
            raise HTTPException(status.HTTP_409_CONFLICT, "El SKU ya existe")

    product.name = payload.name
    product.category_id = payload.category_id
    product.price = payload.price
    product.cost = payload.cost
    product.sku = payload.sku
    db.commit()
    db.refresh(product)
    return product


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(id: uuid.UUID, db: DbSession, _user: AdminUser) -> None:  # noqa: A002
    """Soft-delete de un producto (admin): is_active = False."""
    product = db.get(Product, id)
    if product is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Producto no encontrado")

    product.is_active = False
    db.commit()
