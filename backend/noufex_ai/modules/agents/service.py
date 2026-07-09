from __future__ import annotations

from uuid import UUID

from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from noufex_ai.exceptions import NotFoundError
from noufex_ai.modules.agents.models import Agent
from noufex_ai.modules.agents.schemas import AgentCreate, AgentUpdate


class AgentService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, *, tenant_id: UUID, payload: AgentCreate) -> Agent:
        agent = Agent(
            tenant_id=tenant_id,
            name=payload.name,
            description=payload.description,
            system_prompt=payload.system_prompt,
            model=payload.model,
            temperature=payload.temperature,
            max_tokens=payload.max_tokens,
            tools=",".join(payload.tools) if payload.tools else None,
        )
        self.session.add(agent)
        await self.session.flush()
        return agent

    async def get_by_id(self, *, tenant_id: UUID, agent_id: UUID) -> Agent:
        result = await self.session.execute(
            select(Agent).where(
                Agent.id == agent_id,
                Agent.tenant_id == tenant_id,
                Agent.deleted_at.is_(None),
            )
        )
        agent = result.scalar_one_or_none()
        if agent is None:
            raise NotFoundError(f"Agent {agent_id} not found")
        return agent

    async def list_agents(
        self, *, tenant_id: UUID, offset: int = 0, limit: int = 20
    ) -> tuple[list[Agent], int]:
        base = select(Agent).where(
            Agent.tenant_id == tenant_id,
            Agent.deleted_at.is_(None),
        )
        count_q = select(func.count()).select_from(base.subquery())
        count_result = await self.session.execute(count_q)
        total = count_result.scalar_one()

        q = base.order_by(Agent.created_at.desc()).offset(offset).limit(limit)
        result = await self.session.execute(q)
        return list(result.scalars().all()), total

    async def update(
        self, *, tenant_id: UUID, agent_id: UUID, payload: AgentUpdate
    ) -> Agent:
        agent = await self.get_by_id(tenant_id=tenant_id, agent_id=agent_id)
        update_data = payload.model_dump(exclude_unset=True)
        if "tools" in update_data and update_data["tools"] is not None:
            update_data["tools"] = ",".join(update_data["tools"])
        for field, value in update_data.items():
            setattr(agent, field, value)
        self.session.add(agent)
        await self.session.flush()
        return agent

    async def delete(self, *, tenant_id: UUID, agent_id: UUID) -> None:
        agent = await self.get_by_id(tenant_id=tenant_id, agent_id=agent_id)
        agent.soft_delete()
        self.session.add(agent)
        await self.session.flush()
