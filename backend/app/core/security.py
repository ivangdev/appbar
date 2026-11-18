"""Seguridad: hashing de passwords (Argon2id) y tokens JWT (HS256).

- Passwords: nunca se guardan en claro. Se guarda un hash Argon2id.
- Sesion: se emite un JWT firmado (HS256) que se envia en una cookie HttpOnly.
  El token NUNCA va en la URL.
"""

from __future__ import annotations

import datetime as dt
from typing import Any

import jwt
from pwdlib import PasswordHash

from app.core.config import settings

# Nombre de la cookie donde viaja el JWT (compartido entre login y dependencias).
ACCESS_COOKIE_NAME = "access_token"

# Argon2id es el algoritmo recomendado por pwdlib.
_password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    """Devuelve el hash Argon2id del password."""
    return _password_hash.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Compara un password en claro contra su hash."""
    return _password_hash.verify(password, password_hash)


def create_access_token(user_id: str, role: str) -> str:
    """Firma un JWT con el id y rol del usuario, con expiracion."""
    now = dt.datetime.now(dt.UTC)
    payload: dict[str, Any] = {
        "sub": user_id,
        "role": role,
        "iat": now,
        "exp": now + dt.timedelta(hours=settings.ACCESS_TOKEN_EXPIRE_HOURS),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    """Decodifica y valida el JWT.

    Lanza `jwt.PyJWTError` si la firma es invalida o el token expiro.
    """
    return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
