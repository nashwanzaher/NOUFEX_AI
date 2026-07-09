from __future__ import annotations

import json
import logging
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from noufex_ai.modules.audit import AuditLog

logger = logging.getLogger(__name__)


class AuditService:
    """Service for logging audit events."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def log(
        self,
        *,
        action: str,
        resource_type: str,
        resource_id: str | None = None,
        tenant_id: UUID | None = None,
        user_id: UUID | None = None,
        details: dict[str, Any] | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        status: str = "success",
    ) -> AuditLog:
        """Log an audit event.

        Args:
            action: The action performed (e.g., 'create', 'update', 'delete', 'login')
            resource_type: The type of resource (e.g., 'user', 'agent', 'document')
            resource_id: The ID of the resource
            tenant_id: The tenant ID
            user_id: The user ID
            details: Additional details as a dict
            ip_address: The client IP address
            user_agent: The client user agent
            status: The status of the action ('success', 'failure', 'error')

        Returns:
            The created AuditLog entry
        """
        details_json = json.dumps(details, ensure_ascii=False) if details else None

        audit_log = AuditLog(
            tenant_id=str(tenant_id) if tenant_id else None,
            user_id=str(user_id) if user_id else None,
            action=action,
            resource_type=resource_type,
            resource_id=str(resource_id) if resource_id else None,
            details=details_json,
            ip_address=ip_address,
            user_agent=user_agent,
            status=status,
        )
        self.session.add(audit_log)
        await self.session.flush()

        logger.info(
            "Audit: %s %s %s (tenant=%s, user=%s, status=%s)",
            action,
            resource_type,
            resource_id or "",
            tenant_id or "",
            user_id or "",
            status,
        )
        return audit_log

    async def log_auth_event(
        self,
        *,
        action: str,
        user_id: UUID | None = None,
        email: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        status: str = "success",
        details: dict[str, Any] | None = None,
    ) -> AuditLog:
        """Log an authentication event.

        Args:
            action: The auth action ('login', 'logout', 'signup', 'password_reset', etc.)
            user_id: The user ID
            email: The user email
            ip_address: The client IP address
            user_agent: The client user agent
            status: The status ('success', 'failure')
            details: Additional details

        Returns:
            The created AuditLog entry
        """
        event_details = details or {}
        if email:
            event_details["email"] = email

        return await self.log(
            action=action,
            resource_type="auth",
            resource_id=str(user_id) if user_id else None,
            user_id=user_id,
            details=event_details,
            ip_address=ip_address,
            user_agent=user_agent,
            status=status,
        )

    async def log_data_event(
        self,
        *,
        action: str,
        resource_type: str,
        resource_id: str,
        tenant_id: UUID,
        user_id: UUID,
        details: dict[str, Any] | None = None,
        ip_address: str | None = None,
        status: str = "success",
    ) -> AuditLog:
        """Log a data operation event.

        Args:
            action: The data action ('create', 'update', 'delete', 'export')
            resource_type: The resource type ('document', 'agent', 'conversation')
            resource_id: The resource ID
            tenant_id: The tenant ID
            user_id: The user ID
            details: Additional details
            ip_address: The client IP address
            status: The status ('success', 'failure')

        Returns:
            The created AuditLog entry
        """
        return await self.log(
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            tenant_id=tenant_id,
            user_id=user_id,
            details=details,
            ip_address=ip_address,
            status=status,
        )

    async def log_security_event(
        self,
        *,
        action: str,
        user_id: UUID | None = None,
        ip_address: str | None = None,
        details: dict[str, Any] | None = None,
        status: str = "warning",
    ) -> AuditLog:
        """Log a security event.

        Args:
            action: The security action ('rate_limit_exceeded', 'invalid_token', 'suspicious_activity')
            user_id: The user ID
            ip_address: The client IP address
            details: Additional details
            status: The status ('warning', 'critical')

        Returns:
            The created AuditLog entry
        """
        return await self.log(
            action=action,
            resource_type="security",
            user_id=user_id,
            details=details,
            ip_address=ip_address,
            status=status,
        )

    async def get_logs(
        self,
        *,
        tenant_id: UUID | None = None,
        user_id: UUID | None = None,
        action: str | None = None,
        resource_type: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AuditLog]:
        """Get audit logs with filtering.

        Args:
            tenant_id: Filter by tenant ID
            user_id: Filter by user ID
            action: Filter by action
            resource_type: Filter by resource type
            limit: Maximum number of results
            offset: Offset for pagination

        Returns:
            List of AuditLog entries
        """
        from sqlmodel import select

        query = select(AuditLog)

        if tenant_id:
            query = query.where(AuditLog.tenant_id == str(tenant_id))
        if user_id:
            query = query.where(AuditLog.user_id == str(user_id))
        if action:
            query = query.where(AuditLog.action == action)
        if resource_type:
            query = query.where(AuditLog.resource_type == resource_type)

        query = query.order_by(AuditLog.created_at.desc()).offset(offset).limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())
