"""Tests de integracion de usuarios (admin)."""

from __future__ import annotations

from collections.abc import Callable

from fastapi.testclient import TestClient

from app.models.user import User


def test_create_user_admin(
    client: TestClient, admin_user: User, login: Callable[[str], None]
) -> None:
    login(admin_user.email)
    response = client.post(
        "/v1/users",
        json={
            "name": "Nuevo Mesero",
            "email": "nuevo@posbar.com",
            "password": "secret12345",
            "role": "waiter",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "nuevo@posbar.com"
    assert body["role"] == "waiter"
    assert "password" not in body


def test_create_user_duplicate_email(
    client: TestClient, admin_user: User, login: Callable[[str], None]
) -> None:
    login(admin_user.email)
    payload = {
        "name": "Dup",
        "email": "dup@posbar.com",
        "password": "secret12345",
        "role": "waiter",
    }
    assert client.post("/v1/users", json=payload).status_code == 201
    assert client.post("/v1/users", json=payload).status_code == 409


def test_list_users_forbidden_for_waiter(
    client: TestClient, waiter_user: User, login: Callable[[str], None]
) -> None:
    login(waiter_user.email)
    assert client.get("/v1/users").status_code == 403


def test_update_user(client: TestClient, admin_user: User, login: Callable[[str], None]) -> None:
    login(admin_user.email)
    created = client.post(
        "/v1/users",
        json={
            "name": "Camila",
            "email": "camila@posbar.com",
            "password": "secret12345",
            "role": "waiter",
        },
    ).json()

    updated = client.patch(f"/v1/users/{created['id']}", json={"name": "Camila R"})
    assert updated.status_code == 200
    assert updated.json()["name"] == "Camila R"


def test_deactivate_user(
    client: TestClient, admin_user: User, login: Callable[[str], None]
) -> None:
    login(admin_user.email)
    created = client.post(
        "/v1/users",
        json={
            "name": "Temporal",
            "email": "temp@posbar.com",
            "password": "secret12345",
            "role": "waiter",
        },
    ).json()

    assert client.delete(f"/v1/users/{created['id']}").status_code == 204
    users = client.get("/v1/users").json()
    assert all(u["id"] != created["id"] or u["is_active"] is False for u in users)


def test_cannot_deactivate_self(
    client: TestClient, admin_user: User, login: Callable[[str], None]
) -> None:
    login(admin_user.email)
    response = client.delete(f"/v1/users/{admin_user.id}")
    assert response.status_code == 409
