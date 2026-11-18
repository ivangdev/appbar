"""Tests de la configuracion central (validacion de produccion)."""

from __future__ import annotations

from typing import Any

import pytest
from pydantic import ValidationError

from app.core.config import Settings

# Valores minimos seguros para construir un Settings de produccion sin leer .env.
_SECURE: dict[str, Any] = {
    "APP_ENV": "production",
    "POSTGRES_PASSWORD": "clave-bd-segura-123",
    "JWT_SECRET": "s" * 48,
    "COOKIE_SECURE": True,
    "INITIAL_ADMIN_PASSWORD": "clave-admin-segura-123",
    "SEED_DEMO_USERS": False,
}


def _settings(**overrides: Any) -> Settings:
    values = {**_SECURE, **overrides}
    # _env_file=None: los tests no deben depender del infra/.env del desarrollador.
    return Settings(_env_file=None, **values)


def test_production_accepts_secure_config() -> None:
    settings = _settings()

    assert settings.is_production is True
    assert settings.database_url.startswith("postgresql+psycopg://")


def test_development_allows_defaults() -> None:
    settings = Settings(_env_file=None, APP_ENV="development")

    assert settings.is_production is False
    assert settings.COOKIE_SECURE is False


@pytest.mark.parametrize(
    ("overrides", "expected"),
    [
        ({"JWT_SECRET": "corto"}, "JWT_SECRET"),
        ({"COOKIE_SECURE": False}, "COOKIE_SECURE"),
        ({"INITIAL_ADMIN_PASSWORD": "admin12345"}, "INITIAL_ADMIN_PASSWORD"),
        ({"SEED_DEMO_USERS": True}, "SEED_DEMO_USERS"),
    ],
)
def test_production_rejects_insecure_config(overrides: dict[str, Any], expected: str) -> None:
    with pytest.raises(ValidationError, match=expected):
        _settings(**overrides)
