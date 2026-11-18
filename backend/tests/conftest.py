"""Fixtures compartidas de los tests.

Cada test corre dentro de una transaccion que al final se revierte, asi no
deja datos en la base. Para eso se reemplaza la dependencia `get_db`.
"""

from __future__ import annotations

import uuid
from collections.abc import Callable, Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.db import engine, get_db
from app.core.rate_limit import limiter
from app.core.security import hash_password
from app.main import app
from app.models.user import User


@pytest.fixture(autouse=True)
def _disable_rate_limit() -> Generator[None, None, None]:
    """Desactiva slowapi en tests (salvo que el test lo reactive) y limpia el storage."""
    limiter.enabled = False
    limiter.reset()
    yield
    limiter.enabled = False
    limiter.reset()


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    """Sesion SQLAlchemy atada a una transaccion que se revierte al final."""
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """TestClient con `get_db` apuntando a la sesion de prueba."""

    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def _make_user(db_session: Session, role: str, name: str) -> User:
    user = User(
        name=name,
        email=f"{role}-{uuid.uuid4().hex[:8]}@posbar.com",
        password_hash=hash_password("secret12345"),
        role=role,
    )
    db_session.add(user)
    db_session.flush()
    return user


@pytest.fixture
def admin_user(db_session: Session) -> User:
    """Un usuario admin de prueba (unico por email)."""
    return _make_user(db_session, "admin", "Test Admin")


@pytest.fixture
def waiter_user(db_session: Session) -> User:
    """Un usuario mesero de prueba (unico por email)."""
    return _make_user(db_session, "waiter", "Test Mesero")


@pytest.fixture
def login(client: TestClient) -> Callable[[str], None]:
    """Devuelve un helper para loguear con la password de prueba."""

    def _login(email: str) -> None:
        response = client.post(
            "/v1/auth/token",
            json={"email": email, "password": "secret12345"},
        )
        assert response.status_code == 200

    return _login


@pytest.fixture
def menu(client: TestClient, admin_user: User, login: Callable[[str], None]) -> dict[str, object]:
    """Crea (como admin) una categoria, un producto y una mesa para los tests."""
    login(admin_user.email)
    category = client.post("/v1/categories", json={"name": "Cervezas"}).json()
    product = client.post(
        "/v1/products",
        json={
            "name": "Poker",
            "category_id": category["id"],
            "price": 5000,
            "cost": 3000,
        },
    ).json()
    table = client.post("/v1/tables", json={"table_number": 1}).json()
    return {"category": category, "product": product, "table": table}
