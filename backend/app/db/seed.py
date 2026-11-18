"""Seed de usuarios iniciales (1 admin + 1 mesero).

Idempotente: si el email ya existe, no lo vuelve a crear.

Ejecutar desde `backend/`:
    ./.venv/bin/python -m app.db.seed
"""

from __future__ import annotations

from sqlalchemy import func, select

from app.core.db import SessionLocal
from app.core.security import hash_password
from app.models.enums import UserRole
from app.models.user import User

# (name, email, password, role)
SEED_USERS: list[tuple[str, str, str, UserRole]] = [
    ("Admin", "admin@posbar.com", "admin12345", UserRole.ADMIN),
    ("Mesero", "mesero@posbar.com", "mesero12345", UserRole.WAITER),
]


def seed() -> None:
    """Crea los usuarios iniciales si no existen."""
    with SessionLocal() as db:
        for name, email, password, role in SEED_USERS:
            exists = db.scalar(select(User).where(func.lower(User.email) == email.lower()))
            if exists is not None:
                print(f"= ya existe: {email}")
                continue

            db.add(
                User(
                    name=name,
                    email=email,
                    password_hash=hash_password(password),
                    role=role.value,
                )
            )
            print(f"+ creado: {email} ({role.value})")

        db.commit()


if __name__ == "__main__":
    seed()
