"""Conexion a la base de datos (SQLAlchemy 2.0).

- engine:          motor que mantiene el pool de conexiones a PostgreSQL.
- SessionLocal:    fabrica de sesiones (una unidad de trabajo por request).
- Base:            clase base declarativa; registra el metadata de las tablas.
- get_db:          dependencia de FastAPI que abre y cierra una sesion.
"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings

# pool_pre_ping: valida la conexion antes de usarla (evita conexiones muertas).
engine = create_engine(settings.database_url, pool_pre_ping=True, future=True)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Base declarativa: todas las tablas heredan de aqui."""


def get_db() -> Generator[Session, None, None]:
    """Dependencia: abre una sesion por request y la cierra al terminar."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
