from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import Column, ForeignKey, Index, Integer, String, Text
from sqlmodel import Field, Relationship

from noufex_ai.modules.audit import SoftDeleteMixin, TimestampMixin

if TYPE_CHECKING:
    from noufex_ai.modules.agents.models import Agent
    from noufex_ai.modules.tenants.models import Tenant
    from noufex_ai.modules.users.models import User


class Conversation(TimestampMixin, SoftDeleteMixin, table=True):
    __tablename__ = "conversations"
    __table_args__ = (
        Index("ix_conversations_tenant_id", "tenant_id"),
        Index("ix_conversations_user_id", "user_id"),
        Index("ix_conversations_agent_id", "agent_id"),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    tenant_id: UUID = Field(
        sa_column=Column(
            ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        )
    )
    user_id: UUID = Field(
        sa_column=Column(
            ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        )
    )
    agent_id: UUID = Field(
        sa_column=Column(
            ForeignKey("agents.id", ondelete="SET NULL"),
            nullable=True,
        )
    )
    title: str | None = Field(default=None, sa_column=Column(String(255), nullable=True))
    status: str = Field(
        default="active",
        sa_column=Column(String(20), nullable=False),
    )
    message_count: int = Field(default=0, sa_column=Column(Integer, nullable=False))
    token_usage_input: int = Field(default=0, sa_column=Column(Integer, nullable=False))
    token_usage_output: int = Field(default=0, sa_column=Column(Integer, nullable=False))

    tenant: "Tenant" = Relationship(back_populates="conversations")
    user: "User" = Relationship(back_populates="conversations")
    agent: "Agent | None" = Relationship(back_populates="conversations")
    messages: list["Message"] = Relationship(
        back_populates="conversation",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )


class Message(TimestampMixin, table=True):
    __tablename__ = "messages"
    __table_args__ = (
        Index("ix_messages_conversation_id", "conversation_id"),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    conversation_id: UUID = Field(
        sa_column=Column(
            ForeignKey("conversations.id", ondelete="CASCADE"),
            nullable=False,
        )
    )
    role: str = Field(
        sa_column=Column(String(20), nullable=False),
    )
    content: str = Field(sa_column=Column(Text, nullable=False))
    token_count: int = Field(default=0, sa_column=Column(Integer, nullable=False))
    model: str | None = Field(default=None, sa_column=Column(String(64), nullable=True))
    tool_calls_json: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    metadata_json: str | None = Field(default=None, sa_column=Column(Text, nullable=True))

    conversation: "Conversation" = Relationship(back_populates="messages")
