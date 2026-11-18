"""Configuracion de Alembic para el POS Bar.

- Toma la URL de conexion desde la configuracion de la app (`settings`),
  que a su vez la lee de `infra/.env` (dev) o de las env vars (produccion).
- `target_metadata = Base.metadata` permite el `--autogenerate`: Alembic
  compara los modelos con la base de datos y escribe la migracion.
"""

from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context
from app.core.config import settings
from app.models import Base  # importa TODOS los modelos -> metadata completo

config = context.config

# Inyecta la URL real (con credenciales) en la config de Alembic.
config.set_main_option("sqlalchemy.url", settings.database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Metadata de las tablas: la fuente para el autogenerate.
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Modo 'offline': emite el SQL sin conectarse (util para revisar/exportar)."""
    context.configure(
        url=settings.database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Modo 'online': se conecta y aplica las migraciones."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
