from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Column, ForeignKey, Index, String
from sqlmodel import Field, Relationship
from uuid import UUID, uuid4

from noufex_ai.modules.audit import TimestampMixin

if TYPE_CHECKING:
    from noufex_ai.modules.chat.models import Conversation
    from noufex_ai.modules.tenants.models import Tenant


class User(TimestampMixin, table=True):
    __tablename__ = "users"
    __table_args__ = (
        Index("ix_users_tenant_id", "tenant_id"),
        Index("ix_users_email_active", "email", "is_active"),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    tenant_id: UUID = Field(
        sa_column=Column(
            ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        )
    )
    email: str = Field(sa_column=Column(String(255), nullable=False))
    password_hash: str = Field(sa_column=Column(String(512), nullable=False))
    full_name: str | None = Field(default=None, sa_column=Column(String(255), nullable=True))
    role: str = Field(default="member", sa_column=Column(String(32), nullable=False))
    is_active: bool = Field(default=True)
    last_login_at: datetime | None = Field(default=None, nullable=True)

    tenant: "Tenant" = Relationship(back_populates="users")
    conversations: list["Conversation"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )


class RefreshToken(TimestampMixin, table=True):
    __tablename__ = "refresh_tokens"
    __table_args__ = (
        Index("ix_refresh_user_active", "user_id", "revoked_at"),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(
        sa_column=Column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    )
    token_hash: str = Field(
        sa_column=Column(String(128), nullable=False, unique=True)
    )
    user_agent: str | None = Field(
        default=None, sa_column=Column(String(512), nullable=True)
    )
    ip_address: str | None = Field(
        default=None, sa_column=Column(String(45), nullable=True)
    )
    expires_at: datetime
    revoked_at: datetime | None = Field(default=None, nullable=True)
