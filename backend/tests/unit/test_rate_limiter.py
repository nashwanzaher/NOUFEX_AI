from __future__ import annotations

import time

import pytest

from noufex_ai.middleware import RateLimitMiddleware


class FakeApp:
    async def __call__(self, scope, receive, send):
        from starlette.responses import JSONResponse
        response = JSONResponse({"ok": True})
        await response(scope, receive, send)


class FakeRequest:
    def __init__(self, ip: str = "127.0.0.1", auth: str | None = None):
        self.client = type("Client", (), {"host": ip})()
        self.headers = {}
        if auth:
            self.headers["authorization"] = auth


@pytest.fixture
def middleware():
    return RateLimitMiddleware(FakeApp(), ip_limit=5, user_limit=10)


class TestRateLimitMiddleware:
    def test_allows_requests_under_limit(self, middleware):
        mw = middleware
        for _ in range(4):
            ok, remaining, _ = mw._check(mw._ip_windows, "1.2.3.4", mw._ip_limit)
            assert ok is True
        assert remaining == 1

    def test_blocks_requests_over_limit(self, middleware):
        mw = middleware
        for _ in range(5):
            mw._check(mw._ip_windows, "1.2.3.4", mw._ip_limit)
        ok, remaining, retry = mw._check(mw._ip_windows, "1.2.3.4", mw._ip_limit)
        assert ok is False
        assert remaining == 0
        assert retry > 0

    def test_different_ips_are_independent(self, middleware):
        mw = middleware
        for _ in range(5):
            mw._check(mw._ip_windows, "1.1.1.1", mw._ip_limit)
        ok, _, _ = mw._check(mw._ip_windows, "2.2.2.2", mw._ip_limit)
        assert ok is True

    def test_window_resets(self, middleware):
        mw = middleware
        window = mw._ip_windows["test"]
        window.count = 5
        window.reset_at = time.time() - 1  # expired
        ok, remaining, _ = mw._check(mw._ip_windows, "test", mw._ip_limit)
        assert ok is True
        assert remaining == mw._ip_limit - 1

    def test_cleanup_removes_expired(self, middleware):
        mw = middleware
        mw._ip_windows["old"] = mw._ip_windows["old"].__class__(count=1, reset_at=time.time() - 200)
        mw._last_cleanup = 0
        mw._cleanup()
        assert "old" not in mw._ip_windows

    def test_user_limit_independent_of_ip(self, middleware):
        mw = middleware
        for _ in range(5):
            mw._check(mw._user_windows, "user-1", mw._user_limit)
        # IP limit not affected
        ok, _, _ = mw._check(mw._ip_windows, "1.2.3.4", mw._ip_limit)
        assert ok is True
