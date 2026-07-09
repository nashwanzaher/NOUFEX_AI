from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import Column, ForeignKey, Index, Integer, String, Text
from sqlmodel import Field, Relationship

from noufex_ai.modules.audit import SoftDeleteMixin, TimestampMixin

try:
    from pgvector.sqlalchemy import Vector
except ImportError:
    Vector = None  # type: ignore[misc,assignment]

if TYPE_CHECKING:
    from noufex_ai.modules.chat.models import Conversation
    from noufex_ai.modules.tenants.models import Tenant


class Agent(TimestampMixin, SoftDeleteMixin, table=True):
    __tablename__ = "agents"
    __table_args__ = (
        Index("ix_agents_tenant_id", "tenant_id"),
        Index("ix_agents_tenant_active", "tenant_id", "is_active"),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    tenant_id: UUID = Field(
        sa_column=Column(
            ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        )
    )
    name: str = Field(sa_column=Column(String(255), nullable=False))
    description: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    system_prompt: str = Field(sa_column=Column(Text, nullable=False))
    model: str = Field(default="gpt-4o-mini", sa_column=Column(String(64), nullable=False))
    temperature: float = Field(default=0.2, sa_column=Column(nullable=False))
    max_tokens: int = Field(default=1024, sa_column=Column(Integer, nullable=False))
    is_active: bool = Field(default=True, sa_column=Column(nullable=False))
    tools: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    metadata_json: str | None = Field(default=None, sa_column=Column(Text, nullable=True))

    tenant: "Tenant" = Relationship(back_populates="agents")
    conversations: list["Conversation"] = Relationship(
        back_populates="agent",
    )


class Document(TimestampMixin, SoftDeleteMixin, table=True):
    __tablename__ = "documents"
    __table_args__ = (
        Index("ix_documents_tenant_id", "tenant_id"),
        Index("ix_documents_tenant_status", "tenant_id", "status"),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    tenant_id: UUID = Field(
        sa_column=Column(
            ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        )
    )
    filename: str = Field(sa_column=Column(String(512), nullable=False))
    original_filename: str = Field(sa_column=Column(String(512), nullable=False))
    mime_type: str = Field(sa_column=Column(String(128), nullable=False))
    file_size_bytes: int = Field(sa_column=Column(Integer, nullable=False))
    status: str = Field(
        default="pending",
        sa_column=Column(String(20), nullable=False),
    )
    chunk_count: int = Field(default=0, sa_column=Column(Integer, nullable=False))
    error_message: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    metadata_json: str | None = Field(default=None, sa_column=Column(Text, nullable=True))

    tenant: "Tenant" = Relationship(back_populates="documents")


class KnowledgeChunk(TimestampMixin, table=True):
    __tablename__ = "knowledge_chunks"
    __table_args__ = (
        Index("ix_knowledge_chunks_tenant_id", "tenant_id"),
        Index("ix_knowledge_chunks_document_id", "document_id"),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    tenant_id: UUID = Field(
        sa_column=Column(
            ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        )
    )
    document_id: UUID = Field(
        sa_column=Column(
            ForeignKey("documents.id", ondelete="CASCADE"),
            nullable=False,
        )
    )
    chunk_index: int = Field(sa_column=Column(Integer, nullable=False))
    content: str = Field(sa_column=Column(Text, nullable=False))
    embedding: list[float] | None = Field(
        default=None,
        sa_column=Column(Vector(1536), nullable=True),
    )
    token_count: int = Field(default=0, sa_column=Column(Integer, nullable=False))
    metadata_json: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
