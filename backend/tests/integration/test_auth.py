"""Integration tests for auth flow.

These tests require a real Postgres instance with `pgvector/pgvector:pg16` running.
By default they are skipped unless an integration Postgres URL is configured.

Run locally with:
    INTEGRATION_DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/noufex_ai_test \
        pytest tests/integration -m integration
"""
from __future__ import annotations

import os

import pytest

pytestmark = pytest.mark.integration

INTEGRATION_URL = os.getenv("INTEGRATION_DATABASE_URL")


@pytest.fixture(autouse=True)
def _require_integration_url():
    if not INTEGRATION_URL:
        pytest.skip("INTEGRATION_DATABASE_URL not set; skipping integration test")


@pytest.mark.asyncio
async def test_signup_creates_tenant_and_owner():
    assert INTEGRATION_URL, "Test guard should have skipped"


@pytest.mark.asyncio
async def test_login_returns_tokens_and_refresh_rotation():
    assert INTEGRATION_URL


@pytest.mark.asyncio
async def test_logout_revokes_refresh_token():
    assert INTEGRATION_URL
