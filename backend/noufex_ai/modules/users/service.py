from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from noufex_ai.exceptions import ConflictError, UnauthorizedError
from noufex_ai.modules.tenants.models import Tenant
from noufex_ai.modules.tenants.schemas import TenantCreate
from noufex_ai.modules.users.models import User
from noufex_ai.modules.users.schemas import SignupRequest
from noufex_ai.modules.users.security import hash_password, verify_password


class UserService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def signup(self, payload: SignupRequest) -> tuple[Tenant, User]:
        existing_tenant = await self.session.execute(
            select(Tenant).where(Tenant.slug == payload.slug)
        )
        if existing_tenant.scalar_one_or_none():
            raise ConflictError(f"Slug '{payload.slug}' is already taken")

        existing_user = await self.session.execute(
            select(User).where(User.email == str(payload.email))
        )
        if existing_user.scalar_one_or_none():
            raise ConflictError("Email already registered")

        tenant = Tenant(slug=payload.slug, name=payload.name, plan=payload.plan)
        self.session.add(tenant)
        await self.session.flush()

        user = User(
            tenant_id=tenant.id,
            email=str(payload.email),
            password_hash=hash_password(payload.password),
            full_name=payload.full_name,
            role="owner",
        )
        self.session.add(user)
        await self.session.flush()
        return tenant, user

    async def authenticate(self, *, email: str, password: str) -> User:
        result = await self.session.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

        if user is None or not user.is_active:
            raise UnauthorizedError("Invalid credentials")

        if not verify_password(password, user.password_hash):
            raise UnauthorizedError("Invalid credentials")

        user.last_login_at = datetime.now(timezone.utc)
        self.session.add(user)
        await self.session.flush()
        return user

    async def get_by_id(self, user_id: UUID) -> User | None:
        return await self.session.get(User, user_id)
