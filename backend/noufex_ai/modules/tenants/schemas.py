from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from noufex_ai.modules.tenants.models import Tenant


class TenantCreate(BaseModel):
    slug: str = Field(min_length=3, max_length=50, pattern=r"^[a-z0-9-]+$")
    name: str = Field(min_length=1, max_length=255)
    plan: str = Field(default="free", pattern=r"^(free|pro|enterprise)$")


class TenantUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    plan: str | None = Field(default=None, pattern=r"^(free|pro|enterprise)$")


class TenantRead(BaseModel):
    id: UUID
    slug: str
    name: str
    plan: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_orm_obj(cls, tenant: Tenant) -> TenantRead:
        return cls(
            id=tenant.id,
            slug=tenant.slug,
            name=tenant.name,
            plan=tenant.plan,
            created_at=tenant.created_at or datetime.now(timezone.utc),
            updated_at=tenant.updated_at or datetime.now(timezone.utc),
        )
