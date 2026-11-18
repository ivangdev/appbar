"""Paquete de modelos.

Importar aqui TODOS los modelos garantiza que, al importar `app.models`,
SQLAlchemy registre su metadata completo (necesario para Alembic y para
resolver las relaciones en string entre clases).
"""

from app.core.db import Base
from app.models.category import Category
from app.models.order import Order, OrderItem
from app.models.payment import Payment, PaymentAllocation
from app.models.product import Product
from app.models.table import Table
from app.models.user import User

__all__ = [
    "Base",
    "User",
    "Category",
    "Product",
    "Table",
    "Order",
    "OrderItem",
    "Payment",
    "PaymentAllocation",
]
