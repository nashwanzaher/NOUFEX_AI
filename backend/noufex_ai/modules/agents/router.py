from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from noufex_ai.deps import CurrentUserDep, SessionDep, require_scope
from noufex_ai.modules.agents.schemas import AgentCreate, AgentList, AgentRead, AgentUpdate
from noufex_ai.modules.agents.service import AgentService

router = APIRouter()


@router.get("/", response_model=AgentList)
async def list_agents(
    session: SessionDep,
    user: CurrentUserDep,
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
) -> AgentList:
    service = AgentService(session)
    items, total = await service.list_agents(
        tenant_id=user.tenant_id, offset=offset, limit=limit
    )
    return AgentList(
        items=[AgentRead.model_validate(a) for a in items],
        total=total,
    )


@router.post("/", response_model=AgentRead, status_code=status.HTTP_201_CREATED)
async def create_agent(
    payload: AgentCreate,
    session: SessionDep,
    user: CurrentUserDep = Depends(require_scope("agents:write")),
) -> AgentRead:
    service = AgentService(session)
    agent = await service.create(tenant_id=user.tenant_id, payload=payload)
    return AgentRead.model_validate(agent)


@router.get("/{agent_id}", response_model=AgentRead)
async def get_agent(
    agent_id: UUID,
    session: SessionDep,
    user: CurrentUserDep,
) -> AgentRead:
    service = AgentService(session)
    agent = await service.get_by_id(tenant_id=user.tenant_id, agent_id=agent_id)
    return AgentRead.model_validate(agent)


@router.patch("/{agent_id}", response_model=AgentRead)
async def update_agent(
    agent_id: UUID,
    payload: AgentUpdate,
    session: SessionDep,
    user: CurrentUserDep = Depends(require_scope("agents:write")),
) -> AgentRead:
    service = AgentService(session)
    agent = await service.update(
        tenant_id=user.tenant_id, agent_id=agent_id, payload=payload
    )
    return AgentRead.model_validate(agent)


@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent(
    agent_id: UUID,
    session: SessionDep,
    user: CurrentUserDep = Depends(require_scope("agents:write")),
) -> None:
    service = AgentService(session)
    await service.delete(tenant_id=user.tenant_id, agent_id=agent_id)
