from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Column, Index, String, UniqueConstraint
from sqlmodel import Field, Relationship
from uuid import UUID, uuid4

from noufex_ai.modules.audit import TimestampMixin

if TYPE_CHECKING:
    from noufex_ai.modules.agents.models import Agent, Document
    from noufex_ai.modules.billing.models import Subscription
    from noufex_ai.modules.chat.models import Conversation
    from noufex_ai.modules.users.models import User


class Tenant(TimestampMixin, table=True):
    __tablename__ = "tenants"
    __table_args__ = (
        UniqueConstraint("slug", name="uq_tenants_slug"),
        Index("ix_tenants_plan", "plan"),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    slug: str = Field(sa_column=Column(String(50), nullable=False))
    name: str = Field(sa_column=Column(String(255), nullable=False))
    plan: str = Field(default="free", sa_column=Column(String(20), nullable=False))
    stripe_customer_id: str | None = Field(
        default=None, sa_column=Column(String(64), nullable=True, index=True)
    )

    users: list["User"] = Relationship(
        back_populates="tenant",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
    agents: list["Agent"] = Relationship(
        back_populates="tenant",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
    documents: list["Document"] = Relationship(
        back_populates="tenant",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
    conversations: list["Conversation"] = Relationship(
        back_populates="tenant",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
    subscription: "Subscription | None" = Relationship(
        back_populates="tenant",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
