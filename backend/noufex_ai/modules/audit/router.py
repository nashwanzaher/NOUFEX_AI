from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query

from noufex_ai.deps import CurrentUserDep, SessionDep, require_scope
from noufex_ai.modules.audit.service import AuditService

router = APIRouter()


@router.get("/logs")
async def get_audit_logs(
    session: SessionDep,
    user: CurrentUserDep = Depends(require_scope("admin:read")),
    tenant_id: UUID | None = Query(None, description="Filter by tenant ID"),
    user_id: UUID | None = Query(None, description="Filter by user ID"),
    action: str | None = Query(None, description="Filter by action"),
    resource_type: str | None = Query(None, description="Filter by resource type"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
) -> dict:
    """Get audit logs (admin only)."""
    service = AuditService(session)
    logs = await service.get_logs(
        tenant_id=tenant_id,
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        limit=limit,
        offset=offset,
    )

    return {
        "items": [
            {
                "id": str(log.id),
                "tenant_id": log.tenant_id,
                "user_id": log.user_id,
                "action": log.action,
                "resource_type": log.resource_type,
                "resource_id": log.resource_id,
                "details": log.details,
                "ip_address": log.ip_address,
                "status": log.status,
                "created_at": log.created_at.isoformat() if log.created_at else None,
            }
            for log in logs
        ],
        "total": len(logs),
    }
