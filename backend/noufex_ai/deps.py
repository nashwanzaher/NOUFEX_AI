from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated
from uuid import UUID

import jwt
from fastapi import Depends, Header, Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from noufex_ai.db import get_session
from noufex_ai.exceptions import ForbiddenError, UnauthorizedError
from noufex_ai.settings import settings


@dataclass(frozen=True, slots=True)
class CurrentUser:
    id: UUID
    tenant_id: UUID | None
    email: str
    scopes: frozenset[str]
    role: str


SessionDep = Annotated[AsyncSession, Depends(get_session)]


def _decode_token(token: str) -> dict:
    try:
        if settings.jwt_algorithm == "EdDSA":
            if not settings.jwt_public_key:
                raise UnauthorizedError("Server public key not configured")
            public_key = settings.jwt_public_key.get_secret_value()
            return jwt.decode(token, public_key, algorithms=["EdDSA"])
        return jwt.decode(token, settings.secret_key.get_secret_value(), algorithms=[settings.jwt_algorithm])
    except jwt.ExpiredSignatureError as exc:
        raise UnauthorizedError("Token expired") from exc
    except jwt.InvalidTokenError as exc:
        raise UnauthorizedError("Invalid token") from exc


async def get_current_user(
    authorization: Annotated[str | None, Header()] = None,
) -> CurrentUser:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise UnauthorizedError("Missing bearer token")

    token = authorization.split(" ", 1)[1].strip()
    claims = _decode_token(token)

    if "sub" not in claims or "tenant_id" not in claims:
        raise UnauthorizedError("Token missing required claims")

    return CurrentUser(
        id=UUID(claims["sub"]),
        tenant_id=UUID(claims["tenant_id"]) if claims.get("tenant_id") else None,
        email=claims.get("email", ""),
        scopes=frozenset(s for s in claims.get("scope", "").split() if s),
        role=claims.get("role", "member"),
    )


CurrentUserDep = Annotated[CurrentUser, Depends(get_current_user)]


def require_scope(*required: str):
    async def _checker(user: CurrentUserDep) -> CurrentUser:
        missing = [s for s in required if s not in user.scopes]
        if missing:
            raise ForbiddenError(f"Missing scopes: {' '.join(missing)}")
        return user

    return _checker


def require_tenant(user: CurrentUserDep) -> CurrentUser:
    if user.tenant_id is None:
        raise ForbiddenError("Tenant context required")
    return user


TenantUserDep = Annotated[CurrentUser, Depends(require_tenant)]


def tenant_path_param(
    tenant_id: Annotated[UUID, Path(...)],
    user: TenantUserDep,
) -> UUID:
    if user.tenant_id is None or user.tenant_id != tenant_id:
        raise ForbiddenError("Cross-tenant access denied")
    return tenant_id
