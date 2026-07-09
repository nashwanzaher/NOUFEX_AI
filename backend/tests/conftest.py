from __future__ import annotations

import asyncio
import os
from typing import AsyncIterator
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

os.environ.setdefault("ENV", "development")
os.environ.setdefault("DEBUG", "false")
os.environ.setdefault("SECRET_KEY", "test-secret-key-do-not-use-in-production-please")
os.environ.setdefault("ARGON2_TIME_COST", "1")
os.environ.setdefault("ARGON2_MEMORY_COST", "1024")
os.environ.setdefault("ARGON2_PARALLELISM", "1")
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/noufex_ai_test")

from noufex_ai.db import AsyncSessionMaker
from noufex_ai.settings import get_settings
from noufex_ai.main import create_app

get_settings.__wrapped__.__defaults__ = ()  # type: ignore[attr-defined]
get_settings.cache_clear()  # type: ignore[attr-defined]


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def _setup_db():
    """Create test database tables (session-scoped, runs once)."""
    from noufex_ai.db import metadata
    from sqlalchemy import text

    engine = create_async_engine(
        os.environ["DATABASE_URL"],
        pool_pre_ping=True,
    )
    async with engine.begin() as conn:
        await conn.execute(text("CREATE SCHEMA IF NOT EXISTS public"))
        await conn.run_sync(metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(_setup_db) -> AsyncIterator[AsyncSession]:
    """Provide a transactional database session that rolls back after each test."""
    session_factory = async_sessionmaker(_setup_db, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client(_setup_db) -> AsyncIterator[AsyncClient]:
    """Provide an async HTTP test client."""
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def tenant_id() -> uuid4:
    return uuid4()


@pytest.fixture
def user_id() -> uuid4:
    return uuid4()


@pytest.fixture
def mock_openai_embeddings(monkeypatch):
    """Mock OpenAI embeddings API to avoid real API calls."""
    class FakeEmbedding:
        def __init__(self, text: str):
            self.text = text
            self.embedding = [0.1] * 1536

    class FakeResponse:
        data = [FakeEmbedding("test")]

    async def fake_create(**kwargs):
        return FakeResponse()

    from noufex_ai.modules.rag import service as rag_service
    monkeypatch.setattr(rag_service, "_get_embeddings", fake_create)
