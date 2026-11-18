"""Tests de integracion del catalogo (categorias y productos)."""

from __future__ import annotations

from collections.abc import Callable

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User


def _create_category(client: TestClient, name: str = "Cervezas") -> dict[str, object]:
    response = client.post("/v1/categories", json={"name": name, "sort_order": 1})
    assert response.status_code == 201
    return response.json()


def test_create_category_admin(
    client: TestClient, admin_user: User, login: Callable[[str], None]
) -> None:
    login(admin_user.email)
    body = _create_category(client)
    assert body["name"] == "Cervezas"
    assert body["is_active"] is True


def test_create_category_forbidden_for_waiter(
    client: TestClient, waiter_user: User, login: Callable[[str], None]
) -> None:
    login(waiter_user.email)
    response = client.post("/v1/categories", json={"name": "Licores"})
    assert response.status_code == 403


def test_create_category_duplicate_conflict(
    client: TestClient, admin_user: User, login: Callable[[str], None]
) -> None:
    login(admin_user.email)
    _create_category(client, "Cocteles")
    response = client.post("/v1/categories", json={"name": "Cocteles"})
    assert response.status_code == 409


def test_delete_category_is_soft(
    client: TestClient, admin_user: User, login: Callable[[str], None]
) -> None:
    login(admin_user.email)
    category = _create_category(client, "Snacks")
    assert client.delete(f"/v1/categories/{category['id']}").status_code == 204

    # admin la sigue viendo (inactiva); el mesero no.
    admin_list = client.get("/v1/categories").json()
    assert any(c["id"] == category["id"] for c in admin_list)


def test_create_product_admin(
    client: TestClient, admin_user: User, login: Callable[[str], None]
) -> None:
    login(admin_user.email)
    category = _create_category(client, "Cervezas")
    response = client.post(
        "/v1/products",
        json={
            "name": "Poker",
            "category_id": category["id"],
            "price": 5000,
            "cost": 3000,
            "sku": "POK-001",
        },
    )
    assert response.status_code == 201
    assert response.json()["cost"] == 3000


def test_product_cost_hidden_from_waiter(
    client: TestClient,
    admin_user: User,
    waiter_user: User,
    login: Callable[[str], None],
    db_session: Session,
) -> None:
    # admin crea categoria y producto
    login(admin_user.email)
    category = _create_category(client, "Cervezas")
    client.post(
        "/v1/products",
        json={"name": "Aguila", "category_id": category["id"], "price": 4000, "cost": 2500},
    )
    client.post("/v1/auth/logout")

    # mesero: no debe ver cost
    login(waiter_user.email)
    products = client.get("/v1/products").json()
    assert len(products) == 1
    assert products[0]["price"] == 4000
    assert "cost" not in products[0]


def test_admin_sees_cost(
    client: TestClient, admin_user: User, login: Callable[[str], None]
) -> None:
    login(admin_user.email)
    category = _create_category(client, "Cervezas")
    client.post(
        "/v1/products",
        json={"name": "Aguila", "category_id": category["id"], "price": 4000, "cost": 2500},
    )
    products = client.get("/v1/products").json()
    assert products[0]["cost"] == 2500


def test_waiter_only_sees_active_products(
    client: TestClient, admin_user: User, waiter_user: User, login: Callable[[str], None]
) -> None:
    login(admin_user.email)
    category = _create_category(client, "Cervezas")
    created = client.post(
        "/v1/products",
        json={"name": "Aguila", "category_id": category["id"], "price": 4000},
    ).json()
    client.delete(f"/v1/products/{created['id']}")
    client.post("/v1/auth/logout")

    login(waiter_user.email)
    assert client.get("/v1/products").json() == []
