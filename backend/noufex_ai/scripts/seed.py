"""Seed script – run with: python -m noufex_ai.scripts.seed"""
from __future__ import annotations

import asyncio
import sys
from uuid import uuid4

from sqlmodel import select

from noufex_ai.db import session_scope, healthcheck
from noufex_ai.modules.users.models import User
from noufex_ai.modules.users.security import hash_password
from noufex_ai.modules.tenants.models import Tenant
from noufex_ai.modules.agents.models import Agent


DEMO_EMAIL = "admin@noufex.ai"
DEMO_PASSWORD = "Admin123!"
DEMO_TENANT = "NOUFEX Demo"
DEMO_AGENT_NAME = "NOUFEX Assistant"


async def seed() -> None:
    try:
        await healthcheck()
        print("[seed] Database connection OK")
    except Exception as exc:
        print(f"[seed] Database connection FAILED: {exc}", file=sys.stderr)
        sys.exit(1)

    async with session_scope() as session:
        # ── Tenant ──────────────────────────────────────────────────────
        result = await session.execute(
            select(Tenant).where(Tenant.name == DEMO_TENANT)
        )
        tenant = result.scalar_one_or_none()
        if not tenant:
            tenant = Tenant(name=DEMO_TENANT, slug="noufex-demo", plan="pro")
            session.add(tenant)
            await session.flush()
            print(f"[seed] Created tenant: {DEMO_TENANT} ({tenant.id})")
        else:
            print(f"[seed] Tenant already exists: {DEMO_TENANT}")

        # ── User ────────────────────────────────────────────────────────
        result = await session.execute(
            select(User).where(User.email == DEMO_EMAIL)
        )
        user = result.scalar_one_or_none()
        if not user:
            user = User(
                email=DEMO_EMAIL,
                password_hash=hash_password(DEMO_PASSWORD),
                full_name="Admin",
                role="owner",
                tenant_id=tenant.id,
            )
            session.add(user)
            await session.flush()
            print(f"[seed] Created user: {DEMO_EMAIL} ({user.id})")
        else:
            print(f"[seed] User already exists: {DEMO_EMAIL}")

        # ── Agent ───────────────────────────────────────────────────────
        result = await session.execute(
            select(Agent).where(
                Agent.name == DEMO_AGENT_NAME,
                Agent.tenant_id == tenant.id,
            )
        )
        agent = result.scalar_one_or_none()
        if not agent:
            agent = Agent(
                name=DEMO_AGENT_NAME,
                description="Default NOUFEX AI agent with computer, browser, and design skills.",
                model="gpt-4o-mini",
                temperature=0.2,
                max_tokens=4096,
                system_prompt=(
                    "You are NOUFEX AI assistant. You are a powerful autonomous agent with access to "
                    "computer control, web browsing, UI/UX design, and knowledge retrieval capabilities."
                ),
                tenant_id=tenant.id,
            )
            session.add(agent)
            await session.flush()
            print(f"[seed] Created agent: {DEMO_AGENT_NAME} ({agent.id})")
        else:
            print(f"[seed] Agent already exists: {DEMO_AGENT_NAME}")

        await session.commit()

    print("[seed] Done.")
    print()
    print(f"  Email:    {DEMO_EMAIL}")
    print(f"  Password: {DEMO_PASSWORD}")
    print()


if __name__ == "__main__":
    asyncio.run(seed())
