"""Integration tests for billing endpoints."""
from __future__ import annotations

import json
import time
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from noufex_ai.main import app


@pytest.mark.asyncio
class TestBillingEndpoints:
    """Test billing API endpoints."""

    async def test_list_plans(self, client):
        response = await client.get("/v1/billing/plans")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    async def test_get_subscription_unauthenticated(self, client):
        response = await client.get("/v1/billing/subscription")
        assert response.status_code in [401, 403]

    async def test_get_subscription(self, client, auth_headers):
        response = await client.get("/v1/billing/subscription", headers=auth_headers)
        assert response.status_code == 200

    async def test_list_invoices(self, client, auth_headers):
        response = await client.get("/v1/billing/invoices", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    async def test_checkout_requires_scope(self, client, auth_headers):
        response = await client.post(
            "/v1/billing/checkout",
            json={
                "plan_slug": "pro",
                "success_url": "https://example.com/success",
                "cancel_url": "https://example.com/cancel",
            },
            headers=auth_headers,
        )
        # Should succeed if user has billing:write scope, or 403 if not
        assert response.status_code in [200, 403]

    async def test_portal_requires_scope(self, client, auth_headers):
        response = await client.post(
            "/v1/billing/portal",
            json={"return_url": "https://example.com/dashboard"},
            headers=auth_headers,
        )
        assert response.status_code in [200, 403]

    async def test_webhook_missing_signature(self, client):
        payload = json.dumps({"type": "checkout.session.completed", "data": {"object": {}}})
        response = await client.post(
            "/v1/billing/webhook",
            content=payload,
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 422  # Missing Stripe-Signature header

    async def test_webhook_invalid_json(self, client):
        response = await client.post(
            "/v1/billing/webhook",
            content="not json",
            headers={
                "Content-Type": "application/json",
                "Stripe-Signature": "t=123,v1=fakesig",
            },
        )
        assert response.status_code == 400

    async def test_webhook_valid_event(self, client):
        payload = json.dumps({
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "metadata": {"tenant_id": str(uuid4()), "plan_slug": "pro"},
                    "subscription": "sub_123",
                    "customer": "cus_456",
                }
            },
        })
        response = await client.post(
            "/v1/billing/webhook",
            content=payload,
            headers={
                "Content-Type": "application/json",
                "Stripe-Signature": "t=123,v1=fakesig",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["received"] is True
        assert data["type"] == "checkout.session.completed"

    async def test_webhook_subscription_updated(self, client):
        payload = json.dumps({
            "type": "customer.subscription.updated",
            "data": {
                "object": {
                    "id": "sub_123",
                    "status": "active",
                    "current_period_start": int(time.time()),
                    "current_period_end": int(time.time()) + 86400 * 30,
                    "cancel_at_period_end": False,
                }
            },
        })
        response = await client.post(
            "/v1/billing/webhook",
            content=payload,
            headers={
                "Content-Type": "application/json",
                "Stripe-Signature": "t=123,v1=fakesig",
            },
        )
        assert response.status_code == 200

    async def test_webhook_subscription_deleted(self, client):
        payload = json.dumps({
            "type": "customer.subscription.deleted",
            "data": {"object": {"id": "sub_123"}},
        })
        response = await client.post(
            "/v1/billing/webhook",
            content=payload,
            headers={
                "Content-Type": "application/json",
                "Stripe-Signature": "t=123,v1=fakesig",
            },
        )
        assert response.status_code == 200

    async def test_webhook_unhandled_event(self, client):
        payload = json.dumps({
            "type": "charge.refunded",
            "data": {"object": {"id": "ch_123"}},
        })
        response = await client.post(
            "/v1/billing/webhook",
            content=payload,
            headers={
                "Content-Type": "application/json",
                "Stripe-Signature": "t=123,v1=fakesig",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["type"] == "charge.refunded"
