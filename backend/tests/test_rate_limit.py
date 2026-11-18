"""Tests del rate limiting (slowapi) en el endpoint de login."""

from __future__ import annotations

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from app.core.constants import AUTH_RATE_LIMIT
from app.core.rate_limit import limiter


@pytest.fixture
def limited_client(client: TestClient) -> Generator[TestClient, None, None]:
    """Reactiva el limiter solo para este test y limpia el contador al final."""
    limiter.reset()
    limiter.enabled = True
    yield client
    limiter.enabled = False
    limiter.reset()


def test_login_rate_limited(limited_client: TestClient) -> None:
    """Tras superar el limite de intentos, el login responde 429."""
    limit = int(AUTH_RATE_LIMIT.split("/")[0])
    payload = {"email": "nadie@posbar.com", "password": "malapassword"}

    for _ in range(limit):
        response = limited_client.post("/v1/auth/token", json=payload)
        assert response.status_code == 401

    blocked = limited_client.post("/v1/auth/token", json=payload)
    assert blocked.status_code == 429
