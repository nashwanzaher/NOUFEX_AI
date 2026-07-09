from __future__ import annotations

import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from noufex_ai.settings import settings

logger = logging.getLogger(__name__)


@dataclass
class _Window:
    count: int = 0
    reset_at: float = 0.0


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Sliding-window rate limiter (in-memory).
    
    Tracks requests per IP and per user ID with a 60-second window.
    """

    def __init__(self, app, *, ip_limit: int = 60, user_limit: int = 120) -> None:
        super().__init__(app)
        self._ip_limit = ip_limit or settings.rate_limit_per_minute_per_ip
        self._user_limit = user_limit or settings.rate_limit_per_minute_per_user
        self._ip_windows: dict[str, _Window] = defaultdict(_Window)
        self._user_windows: dict[str, _Window] = defaultdict(_Window)
        self._last_cleanup = time.time()

    def _cleanup(self) -> None:
        now = time.time()
        if now - self._last_cleanup < 120:
            return
        self._last_cleanup = now
        cutoff = now - 120
        for store in (self._ip_windows, self._user_windows):
            expired = [k for k, v in store.items() if v.reset_at < cutoff]
            for k in expired:
                del store[k]

    def _check(self, store: dict[str, _Window], key: str, limit: int) -> tuple[bool, int, float]:
        now = time.time()
        window = store[key]
        if now > window.reset_at:
            window.count = 1
            window.reset_at = now + 60
            return True, limit, window.reset_at - now
        window.count += 1
        remaining = max(0, limit - window.count)
        retry_after = max(0.0, window.reset_at - now)
        return window.count <= limit, remaining, retry_after

    async def dispatch(self, request: Request, call_next):
        self._cleanup()

        # ── Per-IP check ──
        client_ip = request.client.host if request.client else "unknown"
        ip_ok, ip_remaining, ip_retry = self._check(self._ip_windows, client_ip, self._ip_limit)
        if not ip_ok:
            return JSONResponse(
                status_code=429,
                content={
                    "error": {
                        "code": "rate_limited",
                        "message": f"Rate limit exceeded for IP. Try again in {ip_retry:.0f}s.",
                        "retry_after": round(ip_retry),
                    }
                },
                headers={"Retry-After": str(int(ip_retry) + 1), "X-RateLimit-Limit": str(self._ip_limit), "X-RateLimit-Remaining": "0"},
            )

        # ── Per-user check (if token present) ──
        user_id = None
        auth = request.headers.get("authorization", "")
        if auth.lower().startswith("bearer "):
            try:
                import jwt as _jwt
                token = auth.split(" ", 1)[1].strip()
                if settings.jwt_algorithm == "EdDSA" and settings.jwt_public_key:
                    claims = _jwt.decode(token, settings.jwt_public_key.get_secret_value(), algorithms=["EdDSA"])
                else:
                    claims = _jwt.decode(token, settings.secret_key.get_secret_value(), algorithms=[settings.jwt_algorithm])
                user_id = claims.get("sub")
            except Exception:
                pass

        if user_id:
            user_ok, user_remaining, user_retry = self._check(self._user_windows, user_id, self._user_limit)
            if not user_ok:
                return JSONResponse(
                    status_code=429,
                    content={
                        "error": {
                            "code": "rate_limited",
                            "message": f"Rate limit exceeded for account. Try again in {user_retry:.0f}s.",
                            "retry_after": round(user_retry),
                        }
                    },
                    headers={"Retry-After": str(int(user_retry) + 1), "X-RateLimit-Limit": str(self._user_limit), "X-RateLimit-Remaining": "0"},
                )

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(self._ip_limit)
        response.headers["X-RateLimit-Remaining"] = str(ip_remaining)
        return response
