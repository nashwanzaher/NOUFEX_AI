from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime, String, Text, func, text
from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class TimestampMixin(SQLModel):
    created_at: datetime | None = Field(
        default=None,
        sa_column=Column(
            DateTime(timezone=True),
            server_default=func.now(),
            nullable=False,
        ),
    )
    updated_at: datetime | None = Field(
        default=None,
        sa_column=Column(
            DateTime(timezone=True),
            server_default=func.now(),
            onupdate=func.now(),
            nullable=False,
        ),
    )


class SoftDeleteMixin(SQLModel):
    deleted_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True, index=True),
    )

    def soft_delete(self) -> None:
        self.deleted_at = utc_now()


class AuditLog(TimestampMixin, table=True):
    """Audit log for tracking important operations."""
    __tablename__ = "audit_logs"
    __table_args__ = (
        ("ix_audit_logs_tenant_id", "tenant_id"),
        ("ix_audit_logs_user_id", "user_id"),
        ("ix_audit_logs_action", "action"),
        ("ix_audit_logs_created_at", "created_at"),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    tenant_id: UUID | None = Field(default=None, sa_column=Column(String(36), nullable=True))
    user_id: UUID | None = Field(default=None, sa_column=Column(String(36), nullable=True))
    action: str = Field(sa_column=Column(String(100), nullable=False))
    resource_type: str = Field(sa_column=Column(String(50), nullable=False))
    resource_id: str | None = Field(default=None, sa_column=Column(String(36), nullable=True))
    details: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    ip_address: str | None = Field(default=None, sa_column=Column(String(45), nullable=True))
    user_agent: str | None = Field(default=None, sa_column=Column(String(512), nullable=True))
    status: str = Field(default="success", sa_column=Column(String(20), nullable=False))
