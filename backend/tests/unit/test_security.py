from __future__ import annotations

import pytest
from jwt.exceptions import InvalidTokenError

from noufex_ai.modules.users.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    hash_refresh_token,
    needs_rehash,
    verify_password,
)


def test_password_hash_and_verify():
    plain = "super-secret-password"
    hashed = hash_password(plain)
    assert hashed != plain
    assert verify_password(plain, hashed)
    assert not verify_password("wrong-password", hashed)
    assert needs_rehash(hashed) is False


def test_refresh_token_hash_is_deterministic():
    raw = create_refresh_token()[0]
    h1 = hash_refresh_token(raw)
    h2 = hash_refresh_token(raw)
    assert h1 == h2
    assert len(h1) == 64


def test_access_token_decode():
    token, expires_in = create_access_token(
        sub="user-1",
        tenant_id="tenant-1",
        email="a@b.com",
        role="owner",
        scopes=["chat:read", "agents:manage"],
    )
    assert expires_in > 0
    assert isinstance(token, str)
    assert token.count(".") == 2  # 2-part EdDSA or HS256 token
