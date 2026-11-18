"""Constantes centralizadas para el proyecto POS Bar.

Un solo punto de verdad para valores que aparecen en múltiples lugares.
Evita numbers/mágicos strings esparcidos por el código.
"""

from __future__ import annotations

from decimal import Decimal

# ---------------------------------------------------------------------------
# Dinero y moneda
# ---------------------------------------------------------------------------
CURRENCY = "COP"  # Pesos colombianos
CURRENCY_NAME = "Peso Colombiano"
CURRENCY_DECIMAL_PLACES = 0  # ENTEROS, sin centavos (regla del PDR)
ROUNDING_MODE = "ROUND_HALF_UP"  # Redondeo bancario estándar

# Rangos monetarios razonables para un bar
MIN_PAYMENT_AMOUNT = 1  # Pesos mínimos por payment (1 COP)
MAX_PAYMENT_AMOUNT = 10_000_000  # Máximo por payment (10 millones COP)
MAX_PRODUCT_PRICE = 10_000_000  # Máximo precio de producto (10M COP)
MAX_PRODUCT_COST = 10_000_000  # Máximo costo de producto (10M COP)

# ---------------------------------------------------------------------------
# Tiempos y fechas
# ---------------------------------------------------------------------------
TIMEZONE = "America/Bogota"  # Zona horaria de todos los reports

# Timestamps clave (según PDR business rules)
ORDER_CREATED = "created_at"
ORDER_CLOSED = "closed_at"
ORDER_PAID = "paid_at"
PAYMENT_DATE = "payment_date"

# Duraciones
JWT_TOKEN_EXPIRE_HOURS_DEFAULT = 24  # Default expiración token (24h sin refresh)
ACCESS_TOKEN_MAX_AGE_SECONDS = 86_400  # 24 * 60 * 60

# ---------------------------------------------------------------------------
# Roles y permisos
# ---------------------------------------------------------------------------
ROLE_ADMIN = "admin"
ROLE_WAITER = "waiter"

# ---------------------------------------------------------------------------
# Estados de negocio (enums definitivos)
# ---------------------------------------------------------------------------
# Estos mapean a las tablas de la BD (orders.status, payments.method, etc.)
ORDER_STATUS_VALUES = ["open", "closed", "partially_paid", "paid", "cancelled"]
PAYMENT_METHOD_VALUES = ["cash", "nequi", "transfer"]

# Restricciones de negocio para quantities
MIN_ITEM_QUANTITY = 1
MAX_ITEM_QUANTITY = 999
MIN_PAID_QUANTITY = 0

# ---------------------------------------------------------------------------
# Mensajes de error consistentes
# ---------------------------------------------------------------------------
ERROR_MESSAGES = {
    "invalid_credentials": "Credenciales invalidas",
    "insufficient_permissions": "Permisos insuficientes",
    "not_authenticated": "No autenticado",
    "rate_limit_exceeded": "Demasiados intentos. Intente de nuevo más tarde.",
    "validation_error": "Error de validación de datos",
}

# ---------------------------------------------------------------------------
# URLs y rutas
# ---------------------------------------------------------------------------
API_V1_PREFIX = "/v1"
API_DOCS_URL = "/docs"
API_REDOC_URL = "/redoc"

# ---------------------------------------------------------------------------
# Configuración de slowapi rate limiting (por defecto, por IP)
# ---------------------------------------------------------------------------
DEFAULT_RATE_LIMIT = "120/minute"  # Límite global por defecto
AUTH_RATE_LIMIT = "20/minute"  # Endpoints de auth (login, logout)
READ_ONLY_RATE_LIMIT = "120/minute"  # Endpoints de solo lectura
WRITE_RATE_LIMIT = "60/minute"  # Endpoints de escritura


# ---------------------------------------------------------------------------
# Helpers útiles
# ---------------------------------------------------------------------------
def format_currency(amount: int | Decimal, symbol: bool = True) -> str:
    """Formatea un amount en COP como string legible.

    Ej: format_currency(5000) -> "$5.000" o "$5000"
    """
    if symbol:
        # Formato con separador de miles y sin decimales
        formatted = f"{amount:,.0f}"
        # Reemplazar la coma por punto si se desea (formato COP typical)
        return f"${formatted}"
    return str(amount)


# Constants already exported at module level for easy import
__all__ = [
    "CURRENCY",
    "CURRENCY_NAME",
    "CURRENCY_DECIMAL_PLACES",
    "ROUNDING_MODE",
    "MIN_PAYMENT_AMOUNT",
    "MAX_PAYMENT_AMOUNT",
    "MAX_PRODUCT_PRICE",
    "MAX_PRODUCT_COST",
    "TIMEZONE",
    "ORDER_CREATED",
    "ORDER_CLOSED",
    "ORDER_PAID",
    "PAYMENT_DATE",
    "JWT_TOKEN_EXPIRE_HOURS_DEFAULT",
    "ACCESS_TOKEN_MAX_AGE_SECONDS",
    "ROLE_ADMIN",
    "ROLE_WAITER",
    "ORDER_STATUS_VALUES",
    "PAYMENT_METHOD_VALUES",
    "MIN_ITEM_QUANTITY",
    "MAX_ITEM_QUANTITY",
    "MIN_PAID_QUANTITY",
    "ERROR_MESSAGES",
    "API_V1_PREFIX",
    "API_DOCS_URL",
    "API_REDOC_URL",
    "DEFAULT_RATE_LIMIT",
    "AUTH_RATE_LIMIT",
    "READ_ONLY_RATE_LIMIT",
    "WRITE_RATE_LIMIT",
    "format_currency",
]
