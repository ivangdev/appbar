"""Tests unitarios de seguridad (sin base de datos)."""

from __future__ import annotations

import jwt
import pytest

from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_password_hash_roundtrip() -> None:
    hashed = hash_password("secret12345")
    assert hashed != "secret12345"
    assert verify_password("secret12345", hashed) is True
    assert verify_password("otra-password", hashed) is False


def test_jwt_roundtrip() -> None:
    token = create_access_token(user_id="user-1", role="admin")
    payload = decode_access_token(token)
    assert payload["sub"] == "user-1"
    assert payload["role"] == "admin"
    assert "exp" in payload


def test_jwt_invalid_token() -> None:
    with pytest.raises(jwt.PyJWTError):
        decode_access_token("esto-no-es-un-jwt")
