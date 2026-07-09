"""Unit tests for the billing module."""
from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest

from noufex_ai.modules.billing.models import Invoice, Plan, Subscription
from noufex_ai.modules.billing.schemas import (
    CreateCheckoutRequest,
    CreatePortalRequest,
    InvoiceRead,
    PlanRead,
    SubscriptionRead,
)


class TestPlanModel:
    def test_plan_creation(self):
        plan = Plan(slug="pro", name="Pro", price_monthly=2900)
        assert plan.slug == "pro"
        assert plan.name == "Pro"
        assert plan.price_monthly == 2900

    def test_plan_defaults(self):
        plan = Plan(slug="free", name="Free")
        assert plan.price_monthly == 0


class TestSubscriptionModel:
    def test_subscription_creation(self):
        tenant_id = uuid4()
        sub = Subscription(
            tenant_id=tenant_id,
            plan_slug="pro",
            status="active",
            stripe_subscription_id="sub_123",
            stripe_customer_id="cus_456",
        )
        assert sub.tenant_id == tenant_id
        assert sub.plan_slug == "pro"
        assert sub.status == "active"

    def test_subscription_defaults(self):
        tenant_id = uuid4()
        sub = Subscription(tenant_id=tenant_id)
        assert sub.plan_slug == "free"
        assert sub.status == "active"
        assert sub.cancel_at_period_end is False


class TestInvoiceModel:
    def test_invoice_creation(self):
        tenant_id = uuid4()
        inv = Invoice(
            tenant_id=tenant_id,
            amount=2900,
            currency="usd",
            status="paid",
            stripe_invoice_id="inv_789",
        )
        assert inv.tenant_id == tenant_id
        assert inv.amount == 2900
        assert inv.currency == "usd"
        assert inv.status == "paid"

    def test_invoice_defaults(self):
        tenant_id = uuid4()
        inv = Invoice(tenant_id=tenant_id)
        assert inv.amount == 0
        assert inv.currency == "usd"
        assert inv.status == "pending"


class TestBillingSchemas:
    def test_plan_read(self):
        plan = PlanRead(id=uuid4(), slug="pro", name="Pro", price_monthly=2900)
        assert plan.slug == "pro"

    def test_subscription_read(self):
        sub = SubscriptionRead(
            id=uuid4(),
            tenant_id=uuid4(),
            plan_slug="pro",
            status="active",
        )
        assert sub.plan_slug == "pro"
        assert sub.status == "active"
        assert sub.cancel_at_period_end is False

    def test_invoice_read(self):
        inv = InvoiceRead(
            id=uuid4(),
            tenant_id=uuid4(),
            amount=2900,
            currency="usd",
            status="paid",
        )
        assert inv.amount == 2900

    def test_create_checkout_request(self):
        req = CreateCheckoutRequest(
            plan_slug="pro",
            success_url="https://example.com/success",
            cancel_url="https://example.com/cancel",
        )
        assert req.plan_slug == "pro"

    def test_create_portal_request(self):
        req = CreatePortalRequest(return_url="https://example.com/dashboard")
        assert req.return_url == "https://example.com/dashboard"
