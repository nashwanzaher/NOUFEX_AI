from __future__ import annotations

import logging
import time
from collections import defaultdict
from dataclasses import dataclass

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
    """Rate limiter with Redis backend (falls back to in-memory).

    Tracks requests per IP and per user ID with a 60-second window.
    Uses Redis for distributed rate limiting when available.
    """

    def __init__(self, app, *, ip_limit: int = 60, user_limit: int = 120) -> None:
        super().__init__(app)
        self._ip_limit = ip_limit or settings.rate_limit_per_minute_per_ip
        self._user_limit = user_limit or settings.rate_limit_per_minute_per_user
        self._ip_windows: dict[str, _Window] = defaultdict(_Window)
        self._user_windows: dict[str, _Window] = defaultdict(_Window)
        self._last_cleanup = time.time()
        self._redis = None
        self._redis_checked = False

    def _get_redis(self):
        """Get Redis client, lazy initialization."""
        if self._redis_checked:
            return self._redis

        self._redis_checked = True
        try:
            import redis.asyncio as aioredis
            self._redis = aioredis.from_url(
                str(settings.redis_url),
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=2,
            )
            logger.info("Rate limiter using Redis backend")
        except Exception as e:
            logger.warning("Redis not available, using in-memory rate limiter: %s", e)
            self._redis = None

        return self._redis

    async def _redis_check(self, key: str, limit: int) -> tuple[bool, int, float]:
        """Check rate limit using Redis sliding window."""
        redis = self._get_redis()
        if not redis:
            return None  # Fall back to in-memory

        try:
            now = time.time()
            window_key = f"ratelimit:{key}"

            # Use Redis pipeline for atomic operations
            pipe = redis.pipeline()
            # Remove expired entries
            pipe.zremrangebyscore(window_key, 0, now - 60)
            # Count current entries
            pipe.zcard(window_key)
            # Add current request
            pipe.zadd(window_key, {f"{now}": now})
            # Set expiry on the key
            pipe.expire(window_key, 70)

            results = await pipe.execute()
            current_count = results[1]

            remaining = max(0, limit - current_count - 1)
            is_allowed = current_count < limit
            retry_after = 60.0 if not is_allowed else 0.0

            return is_allowed, remaining, retry_after
        except Exception as e:
            logger.warning("Redis rate limit check failed: %s", e)
            return None  # Fall back to in-memory

    def _cleanup(self) -> None:
        """Clean up expired in-memory windows."""
        now = time.time()
        if now - self._last_cleanup < 120:
            return
        self._last_cleanup = now
        cutoff = now - 120
        for store in (self._ip_windows, self._user_windows):
            expired = [k for k, v in store.items() if v.reset_at < cutoff]
            for k in expired:
                del store[k]

    def _memory_check(self, store: dict[str, _Window], key: str, limit: int) -> tuple[bool, int, float]:
        """Check rate limit using in-memory window."""
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

    async def _check_rate_limit(self, key: str, limit: int, store: dict[str, _Window]) -> tuple[bool, int, float]:
        """Check rate limit using Redis or in-memory fallback."""
        # Try Redis first
        result = await self._redis_check(key, limit)
        if result is not None:
            return result

        # Fall back to in-memory
        self._cleanup()
        return self._memory_check(store, key, limit)

    def _rate_limit_response(self, message: str, retry_after: float, limit: int) -> JSONResponse:
        """Create a rate limit exceeded response."""
        return JSONResponse(
            status_code=429,
            content={
                "error": {
                    "code": "rate_limited",
                    "message": message,
                    "retry_after": round(retry_after),
                }
            },
            headers={
                "Retry-After": str(int(retry_after) + 1),
                "X-RateLimit-Limit": str(limit),
                "X-RateLimit-Remaining": "0",
            },
        )

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health check
        if request.url.path in ("/health", "/"):
            return await call_next(request)

        # ── Per-IP check ──
        client_ip = request.client.host if request.client else "unknown"
        ip_ok, ip_remaining, ip_retry = await self._check_rate_limit(
            f"ip:{client_ip}", self._ip_limit, self._ip_windows
        )
        if not ip_ok:
            return self._rate_limit_response(
                f"Rate limit exceeded for IP. Try again in {ip_retry:.0f}s.",
                ip_retry,
                self._ip_limit,
            )

        # ── Per-user check (if token present) ──
        user_id = None
        auth = request.headers.get("authorization", "")
        if auth.lower().startswith("bearer "):
            try:
                import jwt as _jwt

                token = auth.split(" ", 1)[1].strip()
                if settings.jwt_algorithm == "EdDSA" and settings.jwt_public_key:
                    claims = _jwt.decode(
                        token,
                        settings.jwt_public_key.get_secret_value(),
                        algorithms=["EdDSA"],
                    )
                else:
                    claims = _jwt.decode(
                        token,
                        settings.secret_key.get_secret_value(),
                        algorithms=[settings.jwt_algorithm],
                    )
                user_id = claims.get("sub")
            except Exception:
                pass

        if user_id:
            user_ok, user_remaining, user_retry = await self._check_rate_limit(
                f"user:{user_id}", self._user_limit, self._user_windows
            )
            if not user_ok:
                return self._rate_limit_response(
                    f"Rate limit exceeded for account. Try again in {user_retry:.0f}s.",
                    user_retry,
                    self._user_limit,
                )

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(self._ip_limit)
        response.headers["X-RateLimit-Remaining"] = str(ip_remaining)
        return response
