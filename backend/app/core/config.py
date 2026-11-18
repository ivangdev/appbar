"""Configuracion central de la aplicacion.

Lee variables de entorno:
- En desarrollo, desde `infra/.env` (lo carga pydantic-settings).
- En produccion (Dokploy), desde las variables de entorno del servicio.
Las variables de entorno tienen prioridad sobre el archivo .env.
"""

from pathlib import Path

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# app/core/config.py -> parents: [core, app, backend, <repo>]
REPO_ROOT = Path(__file__).resolve().parents[3]
INFRA_ENV = REPO_ROOT / "infra" / ".env"

_DEV_JWT_SECRET = "dev-insecure-secret"
_DEV_ADMIN_PASSWORD = "admin12345"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(INFRA_ENV) if INFRA_ENV.exists() else None,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ------------------------- Entorno -------------------------
    # "development" | "production". En produccion se exigen secretos fuertes.
    APP_ENV: str = "development"

    # ------------------------- PostgreSQL -------------------------
    POSTGRES_DB: str = "pos_bar"
    POSTGRES_USER: str = "pos_user"
    POSTGRES_PASSWORD: str = ""
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432

    # ------------------------- JWT (Fase 2) -------------------------
    JWT_SECRET: str = _DEV_JWT_SECRET
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_HOURS: int = 24
    # En dev (http://localhost) debe ser False; en produccion (HTTPS) True.
    COOKIE_SECURE: bool = False

    # Rate limiting (slowapi). Se desactiva en tests.
    RATE_LIMIT_ENABLED: bool = True

    # ------------------------- Seed inicial -------------------------
    # Usuario admin que se crea al arrancar si no existe (idempotente).
    INITIAL_ADMIN_NAME: str = "Administrador"
    INITIAL_ADMIN_EMAIL: str = "admin@posbar.com"
    INITIAL_ADMIN_PASSWORD: str = _DEV_ADMIN_PASSWORD
    # Usuario mesero de ejemplo: solo se crea si SEED_DEMO_USERS=True (dev).
    SEED_DEMO_USERS: bool = False
    INITIAL_WAITER_NAME: str = "Mesero"
    INITIAL_WAITER_EMAIL: str = "mesero@posbar.com"
    INITIAL_WAITER_PASSWORD: str = "mesero12345"

    @property
    def is_production(self) -> bool:
        """True cuando la app corre en produccion (HTTPS)."""
        return self.APP_ENV.strip().lower() in {"production", "prod"}

    @property
    def database_url(self) -> str:
        """URL de conexion para SQLAlchemy (driver psycopg 3, sincronico)."""
        return (
            f"postgresql+psycopg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @model_validator(mode="after")
    def _validate_production(self) -> "Settings":
        """Falla al arrancar si produccion queda con defaults inseguros."""
        if not self.is_production:
            return self

        problems: list[str] = []
        if self.JWT_SECRET == _DEV_JWT_SECRET or len(self.JWT_SECRET) < 32:
            problems.append("JWT_SECRET debe ser aleatorio y tener al menos 32 caracteres")
        if not self.COOKIE_SECURE:
            problems.append("COOKIE_SECURE debe ser True en produccion (HTTPS)")
        if (
            self.INITIAL_ADMIN_PASSWORD == _DEV_ADMIN_PASSWORD
            or len(self.INITIAL_ADMIN_PASSWORD) < 8
        ):
            problems.append(
                "INITIAL_ADMIN_PASSWORD debe cambiarse en produccion (min. 8 caracteres)"
            )
        if self.SEED_DEMO_USERS:
            problems.append("SEED_DEMO_USERS debe ser False en produccion")

        if problems:
            raise ValueError("Configuracion insegura para produccion: " + "; ".join(problems))
        return self


settings = Settings()
