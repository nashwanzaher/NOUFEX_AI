"""add agents, documents, knowledge_chunks, conversations, messages tables

Revision ID: 0002
Revises: 0001
Create Date: 2026-07-08

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: str | Sequence[str] | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE agents (
            id              uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
            tenant_id       uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            name            text NOT NULL,
            description     text,
            system_prompt   text NOT NULL,
            model           text NOT NULL DEFAULT 'gpt-4o-mini',
            temperature     double precision NOT NULL DEFAULT 0.2,
            max_tokens      integer NOT NULL DEFAULT 1024,
            is_active       boolean NOT NULL DEFAULT true,
            tools           text,
            metadata_json   text,
            deleted_at      timestamptz,
            created_at      timestamptz NOT NULL DEFAULT now(),
            updated_at      timestamptz NOT NULL DEFAULT now()
        )
        """
    )
    op.execute("CREATE INDEX ix_agents_tenant_id ON agents(tenant_id)")
    op.execute("CREATE INDEX ix_agents_tenant_active ON agents(tenant_id, is_active)")

    op.execute(
        """
        CREATE TABLE documents (
            id                  uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
            tenant_id           uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            filename            text NOT NULL,
            original_filename   text NOT NULL,
            mime_type           text NOT NULL,
            file_size_bytes     integer NOT NULL,
            status              text NOT NULL DEFAULT 'pending',
            chunk_count         integer NOT NULL DEFAULT 0,
            error_message       text,
            metadata_json       text,
            deleted_at          timestamptz,
            created_at          timestamptz NOT NULL DEFAULT now(),
            updated_at          timestamptz NOT NULL DEFAULT now()
        )
        """
    )
    op.execute("CREATE INDEX ix_documents_tenant_id ON documents(tenant_id)")
    op.execute("CREATE INDEX ix_documents_tenant_status ON documents(tenant_id, status)")

    op.execute(
        """
        CREATE TABLE knowledge_chunks (
            id              uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
            tenant_id       uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            document_id     uuid NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
            chunk_index     integer NOT NULL,
            content         text NOT NULL,
            embedding       text,
            token_count     integer NOT NULL DEFAULT 0,
            metadata_json   text,
            created_at      timestamptz NOT NULL DEFAULT now(),
            updated_at      timestamptz NOT NULL DEFAULT now()
        )
        """
    )
    op.execute("CREATE INDEX ix_knowledge_chunks_tenant_id ON knowledge_chunks(tenant_id)")
    op.execute("CREATE INDEX ix_knowledge_chunks_document_id ON knowledge_chunks(document_id)")

    op.execute(
        """
        CREATE TABLE conversations (
            id                  uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
            tenant_id           uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            user_id             uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            agent_id            uuid REFERENCES agents(id) ON DELETE SET NULL,
            title               text,
            status              text NOT NULL DEFAULT 'active',
            message_count       integer NOT NULL DEFAULT 0,
            token_usage_input   integer NOT NULL DEFAULT 0,
            token_usage_output  integer NOT NULL DEFAULT 0,
            deleted_at          timestamptz,
            created_at          timestamptz NOT NULL DEFAULT now(),
            updated_at          timestamptz NOT NULL DEFAULT now()
        )
        """
    )
    op.execute("CREATE INDEX ix_conversations_tenant_id ON conversations(tenant_id)")
    op.execute("CREATE INDEX ix_conversations_user_id ON conversations(user_id)")
    op.execute("CREATE INDEX ix_conversations_agent_id ON conversations(agent_id)")

    op.execute(
        """
        CREATE TABLE messages (
            id                  uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
            conversation_id     uuid NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
            role                text NOT NULL,
            content             text NOT NULL,
            token_count         integer NOT NULL DEFAULT 0,
            model               text,
            tool_calls_json     text,
            metadata_json       text,
            created_at          timestamptz NOT NULL DEFAULT now(),
            updated_at          timestamptz NOT NULL DEFAULT now()
        )
        """
    )
    op.execute("CREATE INDEX ix_messages_conversation_id ON messages(conversation_id)")

    op.execute(
        """
        ALTER TABLE conversations
        ADD CONSTRAINT chk_conversations_status
        CHECK (status IN ('active', 'archived', 'deleted'))
        """
    )

    op.execute(
        """
        ALTER TABLE documents
        ADD CONSTRAINT chk_documents_status
        CHECK (status IN ('pending', 'processing', 'ready', 'failed'))
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS messages")
    op.execute("DROP TABLE IF EXISTS conversations")
    op.execute("DROP TABLE IF EXISTS knowledge_chunks")
    op.execute("DROP TABLE IF EXISTS documents")
    op.execute("DROP TABLE IF EXISTS agents")
