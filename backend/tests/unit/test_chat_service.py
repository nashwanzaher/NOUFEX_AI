from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest


def test_chunk_text():
    from noufex_ai.modules.rag.service import _chunk_text

    text = "This is a test sentence. " * 100
    chunks = _chunk_text(text, chunk_size=200, overlap=50)
    assert len(chunks) > 0
    for chunk in chunks:
        assert len(chunk) > 0


def test_chunk_text_short():
    from noufex_ai.modules.rag.service import _chunk_text

    text = "Short text"
    chunks = _chunk_text(text, chunk_size=1000, overlap=200)
    assert len(chunks) == 1
    assert chunks[0] == "Short text"


def test_cosine_similarity():
    from noufex_ai.modules.rag.service import _cosine_similarity

    a = [1.0, 0.0, 0.0]
    b = [1.0, 0.0, 0.0]
    assert _cosine_similarity(a, b) == pytest.approx(1.0)

    c = [0.0, 1.0, 0.0]
    assert _cosine_similarity(a, c) == pytest.approx(0.0)

    d = [0.5, 0.5, 0.0]
    assert 0 < _cosine_similarity(a, d) < 1


def test_cosine_similarity_zero_vector():
    from noufex_ai.modules.rag.service import _cosine_similarity

    a = [0.0, 0.0, 0.0]
    b = [1.0, 0.0, 0.0]
    assert _cosine_similarity(a, b) == 0.0


def test_hash_refresh_token_deterministic():
    from noufex_ai.modules.users.security import hash_refresh_token

    token = "test-token-123"
    h1 = hash_refresh_token(token)
    h2 = hash_refresh_token(token)
    assert h1 == h2
    assert len(h1) == 64


def test_password_hash_and_verify():
    from noufex_ai.modules.users.security import hash_password, verify_password

    password = "my-secure-password-123"
    hashed = hash_password(password)
    assert verify_password(password, hashed)
    assert not verify_password("wrong-password", hashed)
