from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from noufex_ai.exceptions import UnauthorizedError
from noufex_ai.settings import settings


_password_hasher = PasswordHasher(
    time_cost=settings.argon2_time_cost,
    memory_cost=settings.argon2_memory_cost,
    parallelism=settings.argon2_parallelism,
)


def hash_password(plain: str) -> str:
    return _password_hasher.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return _password_hasher.verify(hashed, plain)
    except VerifyMismatchError:
        return False


def needs_rehash(hashed: str) -> bool:
    return _password_hasher.check_needs_rehash(hashed)


def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_access_token(
    *,
    sub: str,
    tenant_id: str,
    email: str,
    role: str,
    scopes: list[str],
) -> tuple[str, int]:
    now = datetime.now(timezone.utc)
    exp = now + timedelta(minutes=settings.access_token_ttl_minutes)
    payload = {
        "sub": sub,
        "tenant_id": tenant_id,
        "email": email,
        "role": role,
        "scope": " ".join(scopes),
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
        "iss": settings.project_name,
    }

    if settings.jwt_algorithm == "EdDSA":
        if not settings.jwt_private_key:
            raise UnauthorizedError("Server private key not configured")
        token = jwt.encode(
            payload, settings.jwt_private_key.get_secret_value(), algorithm="EdDSA"
        )
    else:
        token = jwt.encode(
            payload, settings.secret_key.get_secret_value(), algorithm=settings.jwt_algorithm
        )

    return token, settings.access_token_ttl_minutes * 60


def create_refresh_token() -> tuple[str, datetime]:
    token = secrets.token_urlsafe(48)
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_ttl_days)
    return token, expires_at
