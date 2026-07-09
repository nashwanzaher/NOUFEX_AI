from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AgentCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    system_prompt: str = Field(min_length=1, max_length=10000)
    model: str = Field(default="gpt-4o-mini", max_length=64)
    temperature: float = Field(default=0.2, ge=0, le=2)
    max_tokens: int = Field(default=1024, ge=1, le=128000)
    tools: list[str] | None = Field(default=None)


class AgentUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    system_prompt: str | None = Field(default=None, min_length=1, max_length=10000)
    model: str | None = Field(default=None, max_length=64)
    temperature: float | None = Field(default=None, ge=0, le=2)
    max_tokens: int | None = Field(default=None, ge=1, le=128000)
    is_active: bool | None = None
    tools: list[str] | None = None


class AgentRead(BaseModel):
    id: UUID
    tenant_id: UUID
    name: str
    description: str | None
    system_prompt: str
    model: str
    temperature: float
    max_tokens: int
    is_active: bool
    created_at: datetime | None
    updated_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class AgentList(BaseModel):
    items: list[AgentRead]
    total: int
