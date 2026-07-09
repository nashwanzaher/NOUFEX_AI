from __future__ import annotations

import logging
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from noufex_ai.exceptions import NotFoundError, UpstreamError
from noufex_ai.modules.billing.models import Invoice, Plan, Subscription
from noufex_ai.modules.tenants.models import Tenant

logger = logging.getLogger(__name__)


class BillingService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_plans(self) -> list[Plan]:
        result = await self.session.execute(select(Plan).order_by(Plan.price_monthly))
        return list(result.scalars().all())

    async def get_plan_by_slug(self, slug: str) -> Plan:
        result = await self.session.execute(select(Plan).where(Plan.slug == slug))
        plan = result.scalar_one_or_none()
        if plan is None:
            raise NotFoundError(f"Plan '{slug}' not found")
        return plan

    async def get_subscription(self, tenant_id: UUID) -> Subscription | None:
        result = await self.session.execute(
            select(Subscription).where(
                Subscription.tenant_id == tenant_id,
                Subscription.status.in_(["active", "trialing"]),
            )
        )
        return result.scalar_one_or_none()

    async def get_invoices(self, tenant_id: UUID, limit: int = 20) -> list[Invoice]:
        result = await self.session.execute(
            select(Invoice)
            .where(Invoice.tenant_id == tenant_id)
            .order_by(Invoice.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def create_checkout_session(
        self, *, tenant_id: UUID, plan_slug: str, success_url: str, cancel_url: str
    ) -> dict:
        plan = await self.get_plan_by_slug(plan_slug)

        tenant = await self.session.get(Tenant, tenant_id)
        if tenant is None:
            raise NotFoundError("Tenant not found")

        try:
            import stripe
            from noufex_ai.settings import settings

            if not settings.stripe_secret_key:
                raise UpstreamError("Stripe secret key not configured")

            stripe.api_key = settings.stripe_secret_key.get_secret_value()

            session = stripe.checkout.Session.create(
                mode="subscription",
                line_items=[{"price": plan.stripe_price_id, "quantity": 1}],
                success_url=success_url,
                cancel_url=cancel_url,
                client_reference_id=str(tenant_id),
                metadata={"tenant_id": str(tenant_id), "plan_slug": plan_slug},
            )
            return {"checkout_url": session.url, "session_id": session.id}
        except Exception as exc:
            logger.error("Failed to create checkout session: %s", exc)
            raise UpstreamError(f"Failed to create checkout session: {exc}") from exc

    async def create_portal_session(self, *, tenant_id: UUID, return_url: str) -> dict:
        sub = await self.get_subscription(tenant_id)
        if sub is None or not sub.stripe_customer_id:
            raise NotFoundError("No active subscription found")

        try:
            import stripe
            from noufex_ai.settings import settings

            if not settings.stripe_secret_key:
                raise UpstreamError("Stripe secret key not configured")

            stripe.api_key = settings.stripe_secret_key.get_secret_value()

            session = stripe.billing_portal.Session.create(
                customer=sub.stripe_customer_id,
                return_url=return_url,
            )
            return {"portal_url": session.url}
        except Exception as exc:
            logger.error("Failed to create portal session: %s", exc)
            raise UpstreamError(f"Failed to create portal session: {exc}") from exc

    async def handle_checkout_completed(self, data: dict) -> None:
        tenant_id = data.get("metadata", {}).get("tenant_id")
        subscription_id = data.get("subscription")
        customer_id = data.get("customer")

        if not tenant_id:
            logger.warning("Checkout completed with no tenant_id in metadata")
            return

        tenant = await self.session.get(Tenant, UUID(tenant_id))
        if tenant is None:
            logger.warning("Tenant %s not found for checkout", tenant_id)
            return

        plan_slug = data.get("metadata", {}).get("plan_slug", "pro")
        tenant.plan = plan_slug
        self.session.add(tenant)

        sub = Subscription(
            tenant_id=UUID(tenant_id),
            stripe_subscription_id=subscription_id,
            stripe_customer_id=customer_id,
            plan_slug=plan_slug,
            status="active",
        )
        self.session.add(sub)
        await self.session.flush()
        logger.info("Checkout completed: tenant=%s plan=%s", tenant_id, plan_slug)

    async def handle_subscription_updated(self, data: dict) -> None:
        stripe_sub_id = data.get("id")
        status = data.get("status")

        result = await self.session.execute(
            select(Subscription).where(Subscription.stripe_subscription_id == stripe_sub_id)
        )
        sub = result.scalar_one_or_none()
        if sub is None:
            logger.warning("Subscription %s not found", stripe_sub_id)
            return

        sub.status = status or "active"
        if data.get("current_period_start"):
            sub.current_period_start = datetime.fromtimestamp(data["current_period_start"], tz=timezone.utc)
        if data.get("current_period_end"):
            sub.current_period_end = datetime.fromtimestamp(data["current_period_end"], tz=timezone.utc)
        sub.cancel_at_period_end = data.get("cancel_at_period_end", False)

        self.session.add(sub)

        if status in ("active", "trialing"):
            tenant = await self.session.get(Tenant, sub.tenant_id)
            if tenant:
                tenant.plan = sub.plan_slug
                self.session.add(tenant)

        await self.session.flush()
        logger.info("Subscription updated: stripe_id=%s status=%s", stripe_sub_id, status)

    async def handle_subscription_deleted(self, data: dict) -> None:
        stripe_sub_id = data.get("id")

        result = await self.session.execute(
            select(Subscription).where(Subscription.stripe_subscription_id == stripe_sub_id)
        )
        sub = result.scalar_one_or_none()
        if sub is None:
            return

        sub.status = "canceled"
        self.session.add(sub)

        tenant = await self.session.get(Tenant, sub.tenant_id)
        if tenant:
            tenant.plan = "free"
            self.session.add(tenant)

        await self.session.flush()
        logger.info("Subscription deleted: stripe_id=%s", stripe_sub_id)

    async def handle_invoice_paid(self, data: dict) -> None:
        customer_id = data.get("customer")
        amount = data.get("amount_paid", 0)
        currency = data.get("currency", "usd")
        invoice_url = data.get("hosted_invoice_url")

        result = await self.session.execute(
            select(Subscription).where(Subscription.stripe_customer_id == customer_id)
        )
        sub = result.scalar_one_or_none()
        if sub is None:
            return

        invoice = Invoice(
            tenant_id=sub.tenant_id,
            stripe_invoice_id=data.get("id"),
            amount=amount,
            currency=currency,
            status="paid",
            invoice_url=invoice_url,
        )
        self.session.add(invoice)
        await self.session.flush()
        logger.info("Invoice paid: tenant=%s amount=%s", sub.tenant_id, amount)

    async def seed_plans(self) -> None:
        plans = [
            {"slug": "free", "name": "Free", "price_monthly": 0},
            {"slug": "pro", "name": "Pro", "price_monthly": 2900},
            {"slug": "enterprise", "name": "Enterprise", "price_monthly": 9900},
        ]
        for p in plans:
            existing = await self.session.execute(
                select(Plan).where(Plan.slug == p["slug"])
            )
            if existing.scalar_one_or_none() is None:
                self.session.add(Plan(**p))
        await self.session.flush()
