"""Tests de integracion de los endpoints de autenticacion."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.models.user import User


def test_health(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_login_ok_sets_httponly_cookie(client: TestClient, admin_user: User) -> None:
    response = client.post(
        "/v1/auth/token",
        json={"email": admin_user.email, "password": "secret12345"},
    )
    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"
    set_cookie = response.headers.get("set-cookie", "")
    assert "access_token=" in set_cookie
    assert "HttpOnly" in set_cookie


def test_login_bad_password(client: TestClient, admin_user: User) -> None:
    response = client.post(
        "/v1/auth/token",
        json={"email": admin_user.email, "password": "password-mala"},
    )
    assert response.status_code == 401


def test_me_requires_auth(client: TestClient) -> None:
    assert client.get("/v1/auth/me").status_code == 401


def test_me_with_cookie(client: TestClient, admin_user: User) -> None:
    login = client.post(
        "/v1/auth/token",
        json={"email": admin_user.email, "password": "secret12345"},
    )
    assert login.status_code == 200

    me = client.get("/v1/auth/me")
    assert me.status_code == 200
    body = me.json()
    assert body["email"] == admin_user.email
    assert body["role"] == "admin"


def test_logout_clears_cookie(client: TestClient, admin_user: User) -> None:
    client.post(
        "/v1/auth/token",
        json={"email": admin_user.email, "password": "secret12345"},
    )
    logout = client.post("/v1/auth/logout")
    assert logout.status_code == 204
