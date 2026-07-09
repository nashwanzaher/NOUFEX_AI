from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class DocumentRead(BaseModel):
    id: UUID
    tenant_id: UUID
    filename: str
    original_filename: str
    mime_type: str
    file_size_bytes: int
    status: str
    chunk_count: int
    error_message: str | None
    created_at: datetime | None
    updated_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class DocumentList(BaseModel):
    items: list[DocumentRead]
    total: int


class RAGSearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    agent_id: UUID | None = None
    top_k: int = Field(default=5, ge=1, le=20)
    score_threshold: float = Field(default=0.7, ge=0, le=1)


class RAGChunkResult(BaseModel):
    id: UUID
    document_id: UUID
    content: str
    score: float
    metadata: dict | None = None


class RAGSearchResponse(BaseModel):
    query: str
    results: list[RAGChunkResult]
    total: int
