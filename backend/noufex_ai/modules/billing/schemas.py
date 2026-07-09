from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class PlanRead(BaseModel):
    id: UUID
    slug: str
    name: str
    price_monthly: int
    features: str | None = None

    model_config = ConfigDict(from_attributes=True)


class SubscriptionRead(BaseModel):
    id: UUID
    tenant_id: UUID
    stripe_subscription_id: str | None = None
    plan_slug: str
    status: str
    current_period_start: datetime | None = None
    current_period_end: datetime | None = None
    cancel_at_period_end: bool = False

    model_config = ConfigDict(from_attributes=True)


class InvoiceRead(BaseModel):
    id: UUID
    tenant_id: UUID
    stripe_invoice_id: str | None = None
    amount: int
    currency: str
    status: str
    invoice_url: str | None = None
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class CreateCheckoutRequest(BaseModel):
    plan_slug: str = Field(..., description="Plan to subscribe to")
    success_url: str = Field(..., description="URL to redirect on success")
    cancel_url: str = Field(..., description="URL to redirect on cancel")


class CreatePortalRequest(BaseModel):
    return_url: str = Field(..., description="URL to return to after portal")
