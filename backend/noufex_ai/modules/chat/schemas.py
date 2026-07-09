from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=10000)
    agent_id: UUID | None = None
    conversation_id: UUID | None = None
    use_rag: bool = Field(default=True)
    rag_top_k: int = Field(default=5, ge=1, le=20)
    use_tools: bool = Field(default=True, description="Enable autonomous skill/tool execution")
    tool_auto_confirm: bool = Field(default=False, description="Auto-confirm safe tool executions")


class MessageRead(BaseModel):
    id: UUID
    conversation_id: UUID
    role: str
    content: str
    token_count: int
    model: str | None
    created_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class ConversationRead(BaseModel):
    id: UUID
    tenant_id: UUID
    user_id: UUID
    agent_id: UUID | None
    title: str | None
    status: str
    message_count: int
    token_usage_input: int
    token_usage_output: int
    created_at: datetime | None
    updated_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class ConversationList(BaseModel):
    items: list[ConversationRead]
    total: int


class ConversationMessages(BaseModel):
    conversation: ConversationRead
    messages: list[MessageRead]


class ChatResponse(BaseModel):
    conversation_id: UUID
    message: MessageRead
    tokens_used: int
    model: str
    rag_context_used: bool
    tool_calls_executed: list[dict] | None = None
    tool_results: list[str] | None = None
