from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from noufex_ai.exceptions import ConflictError, NotFoundError
from noufex_ai.modules.tenants.models import Tenant
from noufex_ai.modules.tenants.schemas import TenantCreate, TenantUpdate


class TenantService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, payload: TenantCreate) -> Tenant:
        existing = await self.session.execute(select(Tenant).where(Tenant.slug == payload.slug))
        if existing.scalar_one_or_none():
            raise ConflictError(f"Tenant with slug '{payload.slug}' already exists")

        tenant = Tenant(slug=payload.slug, name=payload.name, plan=payload.plan)
        self.session.add(tenant)
        await self.session.flush()
        return tenant

    async def get_by_id(self, tenant_id: UUID) -> Tenant:
        tenant = await self.session.get(Tenant, tenant_id)
        if tenant is None:
            raise NotFoundError(f"Tenant {tenant_id} not found")
        return tenant

    async def get_by_slug(self, slug: str) -> Tenant:
        result = await self.session.execute(select(Tenant).where(Tenant.slug == slug))
        tenant = result.scalar_one_or_none()
        if tenant is None:
            raise NotFoundError(f"Tenant '{slug}' not found")
        return tenant

    async def update(self, tenant_id: UUID, payload: TenantUpdate) -> Tenant:
        tenant = await self.get_by_id(tenant_id)
        if payload.name is not None:
            tenant.name = payload.name
        if payload.plan is not None:
            tenant.plan = payload.plan
        self.session.add(tenant)
        await self.session.flush()
        return tenant
