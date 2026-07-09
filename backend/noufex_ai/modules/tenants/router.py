from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from noufex_ai.deps import CurrentUserDep, SessionDep, require_scope
from noufex_ai.modules.tenants.schemas import TenantCreate, TenantRead, TenantUpdate
from noufex_ai.modules.tenants.service import TenantService

router = APIRouter()


@router.get("/me", response_model=TenantRead)
async def get_my_tenant(session: SessionDep, user: CurrentUserDep) -> TenantRead:
    if user.tenant_id is None:
        from noufex_ai.exceptions import ForbiddenError

        raise ForbiddenError("User is not associated with a tenant")
    service = TenantService(session)
    tenant = await service.get_by_id(UUID(user.tenant_id))
    return TenantRead.from_orm_obj(tenant)


@router.get("/", response_model=list[TenantRead])
async def list_tenants(
    session: SessionDep,
    user: CurrentUserDep = Depends(require_scope("admin:read")),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
) -> list[TenantRead]:
    from sqlmodel import select
    from noufex_ai.modules.tenants.models import Tenant

    service = TenantService(session)
    result = await session.execute(
        select(Tenant).offset(offset).limit(limit)
    )
    tenants = result.scalars().all()
    return [TenantRead.from_orm_obj(t) for t in tenants]


@router.post("/", response_model=TenantRead, status_code=status.HTTP_201_CREATED)
async def create_tenant(
    payload: TenantCreate,
    session: SessionDep,
    user: CurrentUserDep = Depends(require_scope("admin:write")),
) -> TenantRead:
    service = TenantService(session)
    tenant = await service.create(payload)
    return TenantRead.from_orm_obj(tenant)


@router.get("/{tenant_id}", response_model=TenantRead)
async def get_tenant(
    tenant_id: UUID,
    session: SessionDep,
    user: CurrentUserDep = Depends(require_scope("admin:read")),
) -> TenantRead:
    service = TenantService(session)
    tenant = await service.get_by_id(tenant_id)
    return TenantRead.from_orm_obj(tenant)


@router.patch("/{tenant_id}", response_model=TenantRead)
async def update_tenant(
    tenant_id: UUID,
    payload: TenantUpdate,
    session: SessionDep,
    user: CurrentUserDep = Depends(require_scope("admin:write")),
) -> TenantRead:
    service = TenantService(session)
    tenant = await service.update(tenant_id, payload)
    return TenantRead.from_orm_obj(tenant)
