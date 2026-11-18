"""Enumeraciones del dominio.

Se persisten como VARCHAR + CheckConstraint (portable entre motores y
mas facil de migrar que los ENUM nativos de PostgreSQL).
"""

import enum


class UserRole(enum.StrEnum):
    ADMIN = "admin"
    WAITER = "waiter"


class TableStatus(enum.StrEnum):
    FREE = "free"
    OCCUPIED = "occupied"


class OrderStatus(enum.StrEnum):
    OPEN = "open"
    CLOSED = "closed"
    PARTIALLY_PAID = "partially_paid"
    PAID = "paid"
    CANCELLED = "cancelled"


class PaymentMethod(enum.StrEnum):
    CASH = "cash"
    NEQUI = "nequi"
    TRANSFER = "transfer"
