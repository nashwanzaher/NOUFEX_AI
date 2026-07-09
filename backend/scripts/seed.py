from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from noufex_ai.db import AsyncSessionMaker, engine
from noufex_ai.modules.agents.models import Agent
from noufex_ai.modules.tenants.models import Tenant
from noufex_ai.modules.users.models import User
from noufex_ai.modules.users.security import hash_password


async def seed():
    async with AsyncSessionMaker() as session:
        tenant = Tenant(slug="demo", name="Demo Company", plan="pro")
        session.add(tenant)
        await session.flush()

        user = User(
            tenant_id=tenant.id,
            email="admin@noufex.ai",
            password_hash=hash_password("admin123"),
            full_name="Admin User",
            role="owner",
        )
        session.add(user)
        await session.flush()

        agent = Agent(
            tenant_id=tenant.id,
            name="Customer Support Agent",
            description="A helpful customer support agent",
            system_prompt=(
                "You are a helpful customer support agent for NOUFEX. "
                "Answer questions about the product politely and professionally. "
                "If you don't know the answer, say so and offer to connect the user with a human agent."
            ),
            model="gpt-4o-mini",
            temperature=0.3,
            max_tokens=1024,
        )
        session.add(agent)

        agent2 = Agent(
            tenant_id=tenant.id,
            name="Code Assistant",
            description="An AI coding assistant",
            system_prompt=(
                "You are an expert software developer. "
                "Help users with coding questions, debugging, and code reviews. "
                "Always explain your reasoning and provide clean, well-documented code."
            ),
            model="gpt-4o",
            temperature=0.2,
            max_tokens=2048,
        )
        session.add(agent2)

        await session.commit()

        print(f"Created tenant: {tenant.slug} (id={tenant.id})")
        print(f"Created user: {user.email} (id={user.id})")
        print(f"Created agents: {agent.name}, {agent2.name}")


if __name__ == "__main__":
    asyncio.run(seed())
