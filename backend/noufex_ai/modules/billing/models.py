from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import Column, ForeignKey, Index, String, Text
from sqlmodel import Field, Relationship

from noufex_ai.modules.audit import TimestampMixin

if TYPE_CHECKING:
    from noufex_ai.modules.tenants.models import Tenant


class Plan(TimestampMixin, table=True):
    __tablename__ = "plans"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    slug: str = Field(sa_column=Column(String(50), nullable=False, unique=True))
    name: str = Field(sa_column=Column(String(100), nullable=False))
    stripe_price_id: str | None = Field(default=None, sa_column=Column(String(64), nullable=True))
    price_monthly: int = Field(default=0, sa_column=Column(nullable=False))
    features: str | None = Field(default=None, sa_column=Column(Text, nullable=True))


class Subscription(TimestampMixin, table=True):
    __tablename__ = "subscriptions"
    __table_args__ = (
        Index("ix_subscriptions_tenant_id", "tenant_id"),
        Index("ix_subscriptions_stripe_id", "stripe_subscription_id"),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    tenant_id: UUID = Field(
        sa_column=Column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    )
    stripe_subscription_id: str | None = Field(
        default=None, sa_column=Column(String(64), nullable=True, index=True)
    )
    stripe_customer_id: str | None = Field(
        default=None, sa_column=Column(String(64), nullable=True)
    )
    plan_slug: str = Field(default="free", sa_column=Column(String(50), nullable=False))
    status: str = Field(default="active", sa_column=Column(String(32), nullable=False))
    current_period_start: datetime | None = Field(default=None, nullable=True)
    current_period_end: datetime | None = Field(default=None, nullable=True)
    cancel_at_period_end: bool = Field(default=False)

    tenant: "Tenant" = Relationship(back_populates="subscription")


class Invoice(TimestampMixin, table=True):
    __tablename__ = "invoices"
    __table_args__ = (
        Index("ix_invoices_tenant_id", "tenant_id"),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    tenant_id: UUID = Field(
        sa_column=Column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    )
    stripe_invoice_id: str | None = Field(
        default=None, sa_column=Column(String(64), nullable=True, index=True)
    )
    amount: int = Field(default=0, sa_column=Column(nullable=False))
    currency: str = Field(default="usd", sa_column=Column(String(3), nullable=False))
    status: str = Field(default="pending", sa_column=Column(String(32), nullable=False))
    invoice_url: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
