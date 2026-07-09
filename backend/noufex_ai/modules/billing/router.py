from __future__ import annotations

import hashlib
import hmac
import json
import logging
from typing import Any

from fastapi import APIRouter, Depends, Request

from noufex_ai.deps import CurrentUserDep, SessionDep, require_scope
from noufex_ai.exceptions import ValidationError
from noufex_ai.modules.billing.schemas import (
    CreateCheckoutRequest,
    CreatePortalRequest,
    InvoiceRead,
    PlanRead,
    SubscriptionRead,
)
from noufex_ai.modules.billing.service import BillingService

logger = logging.getLogger(__name__)

router = APIRouter()


def _verify_stripe_signature(body: bytes, signature: str, secret: str) -> bool:
    if "v1=" not in signature:
        return False
    elements = dict(item.split("=", 1) for item in signature.split(",") if "=" in item)
    timestamp = elements.get("t", "")
    expected_sig = elements.get("v1", "")
    signed_payload = f"{timestamp}.{body.decode('utf-8')}"
    computed = hmac.new(secret.encode(), signed_payload.encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(computed, expected_sig)


@router.get("/plans", response_model=list[PlanRead])
async def list_plans(session: SessionDep, user: CurrentUserDep) -> list[PlanRead]:
    service = BillingService(session)
    plans = await service.get_plans()
    return [PlanRead.model_validate(p) for p in plans]


@router.get("/subscription", response_model=SubscriptionRead | None)
async def get_subscription(
    session: SessionDep,
    user: CurrentUserDep,
) -> SubscriptionRead | None:
    service = BillingService(session)
    sub = await service.get_subscription(user.tenant_id)
    return SubscriptionRead.model_validate(sub) if sub else None


@router.get("/invoices", response_model=list[InvoiceRead])
async def list_invoices(
    session: SessionDep,
    user: CurrentUserDep,
) -> list[InvoiceRead]:
    service = BillingService(session)
    invoices = await service.get_invoices(user.tenant_id)
    return [InvoiceRead.model_validate(i) for i in invoices]


@router.post("/checkout")
async def create_checkout(
    payload: CreateCheckoutRequest,
    session: SessionDep,
    user: CurrentUserDep = Depends(require_scope("billing:write")),
) -> dict:
    service = BillingService(session)
    return await service.create_checkout_session(
        tenant_id=user.tenant_id,
        plan_slug=payload.plan_slug,
        success_url=payload.success_url,
        cancel_url=payload.cancel_url,
    )


@router.post("/portal")
async def create_portal(
    payload: CreatePortalRequest,
    session: SessionDep,
    user: CurrentUserDep = Depends(require_scope("billing:write")),
) -> dict:
    service = BillingService(session)
    return await service.create_portal_session(
        tenant_id=user.tenant_id,
        return_url=payload.return_url,
    )


@router.post("/webhook")
async def stripe_webhook(request: Request, session: SessionDep) -> dict[str, Any]:
    body = await request.body()
    signature = request.headers.get("Stripe-Signature", "")

    if not body or not signature:
        raise ValidationError("Missing Stripe-Signature or request body")

    from noufex_ai.settings import settings

    webhook_secret = settings.stripe_webhook_secret
    if not webhook_secret:
        raise ValidationError("Webhook secret not configured - rejecting webhook")

    secret = webhook_secret.get_secret_value()
    if not _verify_stripe_signature(body, signature, secret):
        raise ValidationError("Invalid Stripe signature")

    try:
        event = json.loads(body)
    except json.JSONDecodeError:
        raise ValidationError("Invalid JSON payload")

    event_type = event.get("type", "")
    event_data = event.get("data", {}).get("object", {})

    logger.info("Stripe webhook: type=%s id=%s", event_type, event.get("id"))

    service = BillingService(session)

    match event_type:
        case "checkout.session.completed":
            await service.handle_checkout_completed(event_data)
        case "invoice.paid":
            await service.handle_invoice_paid(event_data)
        case "invoice.payment_failed":
            logger.warning("Invoice payment failed: customer=%s", event_data.get("customer"))
        case "customer.subscription.created" | "customer.subscription.updated":
            await service.handle_subscription_updated(event_data)
        case "customer.subscription.deleted":
            await service.handle_subscription_deleted(event_data)
        case _:
            logger.info("Unhandled Stripe event: %s", event_type)

    return {"received": True, "type": event_type}
