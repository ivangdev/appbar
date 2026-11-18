"""Seed de usuarios iniciales (idempotente).

- Crea el admin configurado en `INITIAL_ADMIN_*` si su email no existe.
- Si `SEED_DEMO_USERS=True` (solo dev), crea tambien el mesero de ejemplo.
- Nunca sobreescribe un usuario existente ni su password.

Se ejecuta automaticamente al arrancar el contenedor (ver Dockerfile).
Tambien se puede ejecutar a mano desde `backend/`:

    ./.venv/bin/python -m app.db.seed
"""

from __future__ import annotations

from typing import NamedTuple

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import SessionLocal
from app.core.security import hash_password
from app.models.enums import UserRole
from app.models.user import User


class SeedUser(NamedTuple):
    name: str
    email: str
    password: str
    role: UserRole


def seed_users() -> list[SeedUser]:
    """Usuarios que deben existir segun la configuracion."""
    users = [
        SeedUser(
            settings.INITIAL_ADMIN_NAME,
            settings.INITIAL_ADMIN_EMAIL,
            settings.INITIAL_ADMIN_PASSWORD,
            UserRole.ADMIN,
        )
    ]
    if settings.SEED_DEMO_USERS:
        users.append(
            SeedUser(
                settings.INITIAL_WAITER_NAME,
                settings.INITIAL_WAITER_EMAIL,
                settings.INITIAL_WAITER_PASSWORD,
                UserRole.WAITER,
            )
        )
    return users


def seed(db: Session) -> list[str]:
    """Crea los usuarios que falten. Devuelve los emails creados."""
    created: list[str] = []
    for user in seed_users():
        email = user.email.strip().lower()
        exists = db.scalar(select(User).where(func.lower(User.email) == email))
        if exists is not None:
            continue
        db.add(
            User(
                name=user.name,
                email=email,
                password_hash=hash_password(user.password),
                role=user.role.value,
            )
        )
        created.append(email)
    db.commit()
    return created


def main() -> None:
    """Punto de entrada CLI: crea los usuarios iniciales."""
    with SessionLocal() as db:
        created = seed(db)
        if created:
            for email in created:
                print(f"+ creado: {email}")
        else:
            print("= usuarios iniciales ya existen (nada que hacer)")


if __name__ == "__main__":
    main()
