"""Configuracion central de la aplicacion.

Lee variables de entorno:
- En desarrollo, desde `infra/.env` (lo carga pydantic-settings).
- En produccion (Dokploy), desde las variables de entorno del servicio.
Las variables de entorno tienen prioridad sobre el archivo .env.
"""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# app/core/config.py -> parents: [core, app, backend, <repo>]
REPO_ROOT = Path(__file__).resolve().parents[3]
INFRA_ENV = REPO_ROOT / "infra" / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(INFRA_ENV) if INFRA_ENV.exists() else None,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ------------------------- PostgreSQL -------------------------
    POSTGRES_DB: str = "pos_bar"
    POSTGRES_USER: str = "pos_user"
    POSTGRES_PASSWORD: str = ""
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432

    # ------------------------- JWT (Fase 2) -------------------------
    JWT_SECRET: str = "dev-insecure-secret"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_HOURS: int = 24
    # En dev (http://localhost) debe ser False; en produccion (HTTPS) True.
    COOKIE_SECURE: bool = False

    # Rate limiting (slowapi). Se desactiva en tests.
    RATE_LIMIT_ENABLED: bool = True

    @property
    def database_url(self) -> str:
        """URL de conexion para SQLAlchemy (driver psycopg 3, sincronico)."""
        return (
            f"postgresql+psycopg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )


settings = Settings()
