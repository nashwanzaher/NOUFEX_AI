"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-07-08

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "citext"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "pg_trgm"')

    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'user_role') THEN
                CREATE TYPE user_role AS ENUM ('owner', 'admin', 'member');
            END IF;
        END$$;
        """
    )

    op.execute(
        """
        CREATE TABLE tenants (
            id                  uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
            slug                text NOT NULL,
            name                text NOT NULL,
            plan                text NOT NULL DEFAULT 'free' CHECK (plan IN ('free','pro','enterprise')),
            stripe_customer_id  text UNIQUE,
            created_at          timestamptz NOT NULL DEFAULT now(),
            updated_at          timestamptz NOT NULL DEFAULT now(),
            CONSTRAINT uq_tenants_slug UNIQUE (slug)
        )
        """
    )
    op.execute("CREATE INDEX ix_tenants_plan ON tenants(plan)")

    op.execute(
        """
        CREATE TABLE users (
            id              uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
            tenant_id       uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            email           citext NOT NULL,
            password_hash   text NOT NULL,
            full_name       text,
            role            user_role NOT NULL DEFAULT 'member',
            is_active       boolean NOT NULL DEFAULT true,
            last_login_at   timestamptz,
            created_at      timestamptz NOT NULL DEFAULT now(),
            updated_at      timestamptz NOT NULL DEFAULT now()
        )
        """
    )
    op.execute("CREATE INDEX ix_users_tenant_id ON users(tenant_id)")
    op.execute("CREATE INDEX ix_users_email_active ON users(email, is_active)")

    op.execute(
        """
        CREATE TABLE refresh_tokens (
            id           uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
            user_id      uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            token_hash   text NOT NULL UNIQUE,
            user_agent   text,
            ip_address   text,
            expires_at   timestamptz NOT NULL,
            revoked_at   timestamptz,
            created_at   timestamptz NOT NULL DEFAULT now(),
            updated_at   timestamptz NOT NULL DEFAULT now()
        )
        """
    )
    op.execute("CREATE INDEX ix_refresh_user_active ON refresh_tokens(user_id, revoked_at)")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS refresh_tokens")
    op.execute("DROP TABLE IF EXISTS users")
    op.execute("DROP TABLE IF EXISTS tenants")
    op.execute("DROP TYPE IF EXISTS user_role")
