from __future__ import annotations

import pytest
from uuid import uuid4

from noufex_ai.modules.agents.schemas import AgentCreate, AgentUpdate
from noufex_ai.modules.agents.service import AgentService
from noufex_ai.modules.chat.schemas import ChatRequest
from noufex_ai.modules.rag.schemas import RAGSearchRequest


def test_agent_create_schema():
    agent = AgentCreate(
        name="Test Agent",
        description="A test agent",
        system_prompt="You are a helpful assistant.",
        model="gpt-4o-mini",
        temperature=0.5,
        max_tokens=512,
        tools=["search_docs", "create_ticket"],
    )
    assert agent.name == "Test Agent"
    assert agent.model == "gpt-4o-mini"
    assert agent.temperature == 0.5
    assert len(agent.tools) == 2


def test_agent_update_schema_partial():
    update = AgentUpdate(name="Updated Name")
    data = update.model_dump(exclude_unset=True)
    assert "name" in data
    assert "model" not in data


def test_chat_request_schema():
    request = ChatRequest(
        message="Hello, how are you?",
        agent_id=uuid4(),
        use_rag=True,
        rag_top_k=3,
    )
    assert request.message == "Hello, how are you?"
    assert request.use_rag is True
    assert request.rag_top_k == 3


def test_rag_search_request_schema():
    request = RAGSearchRequest(
        query="What is the refund policy?",
        top_k=10,
        score_threshold=0.8,
    )
    assert request.query == "What is the refund policy?"
    assert request.top_k == 10
    assert request.score_threshold == 0.8


def test_agent_create_schema_validation():
    with pytest.raises(Exception):
        AgentCreate(
            name="",
            system_prompt="test",
        )

    with pytest.raises(Exception):
        AgentCreate(
            name="Test",
            system_prompt="test",
            temperature=5.0,
        )
