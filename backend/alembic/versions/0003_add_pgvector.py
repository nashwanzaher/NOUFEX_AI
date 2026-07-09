"""Add pgvector and convert embedding column

Revision ID: 0003
Revises: 0002
Create Date: 2026-07-08

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: str | Sequence[str] | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Enable pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # Add new vector column
    op.execute(
        "ALTER TABLE knowledge_chunks "
        "ADD COLUMN embedding_vector vector(1536)"
    )

    # Migrate data from JSON text to vector
    op.execute(
        "UPDATE knowledge_chunks "
        "SET embedding_vector = embedding::vector "
        "WHERE embedding IS NOT NULL"
    )

    # Drop old text column and rename
    op.execute("ALTER TABLE knowledge_chunks DROP COLUMN embedding")
    op.execute("ALTER TABLE knowledge_chunks RENAME COLUMN embedding_vector TO embedding")

    # Create IVFFlat index for fast cosine search (requires at least 100 rows for training)
    # Using Lists=10 as default; can be tuned later
    op.execute(
        "CREATE INDEX ix_knowledge_chunks_embedding "
        "ON knowledge_chunks "
        "USING ivfflat (embedding vector_cosine_ops) "
        "WITH (lists = 10)"
    )

    # Also create a HNSW index as a fallback (better for small datasets)
    # This is created in addition to IVFFlat; the query planner will choose
    op.execute(
        "CREATE INDEX ix_knowledge_chunks_embedding_hnsw "
        "ON knowledge_chunks "
        "USING hnsw (embedding vector_cosine_ops) "
        "WITH (m = 16, ef_construction = 64)"
    )


def downgrade() -> None:
    op.drop_index("ix_knowledge_chunks_embedding_hnsw", postgresql_using="hnsw")
    op.drop_index("ix_knowledge_chunks_embedding", postgresql_using="ivfflat")

    # Add back text column
    op.execute(
        "ALTER TABLE knowledge_chunks "
        "ADD COLUMN embedding text"
    )

    # Migrate data back
    op.execute(
        "UPDATE knowledge_chunks "
        "SET embedding = embedding::text "
        "WHERE embedding IS NOT NULL"
    )

    op.execute("ALTER TABLE knowledge_chunks DROP COLUMN embedding")
