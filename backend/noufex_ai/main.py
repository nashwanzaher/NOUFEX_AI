from __future__ import annotations

import logging
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import sentry_sdk
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from noufex_ai import __version__
from noufex_ai.db import dispose_engine, healthcheck
from noufex_ai.exceptions import register_exception_handlers
from noufex_ai.logging_config import configure_logging
from noufex_ai.middleware import RateLimitMiddleware
from noufex_ai.settings import settings
from noufex_ai.telemetry import setup_telemetry

configure_logging()
logger = logging.getLogger(__name__)


class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        rid = request.headers.get("x-request-id") or str(uuid.uuid4())
        request.state.request_id = rid
        response = await call_next(request)
        response.headers["x-request-id"] = rid
        return response


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    logger.info("Starting %s v%s (env=%s)", settings.project_name, __version__, settings.env)

    if settings.sentry_dsn:
        sentry_sdk.init(
            dsn=settings.sentry_dsn.get_secret_value(),
            traces_sample_rate=settings.sentry_traces_sample_rate,
            environment=settings.env,
            release=f"noufex-ai@{__version__}",
        )

    setup_telemetry(app)

    try:
        health = await healthcheck()
        logger.info("DB healthcheck: %s", health)
    except Exception as exc:
        logger.warning("DB healthcheck failed at startup: %s", exc)

    yield

    logger.info("Shutting down %s", settings.project_name)
    try:
        from noufex_ai.modules.chat.service import _browser_service
        if _browser_service is not None:
            import asyncio
            try:
                await asyncio.wait_for(_browser_service.close_browser(), timeout=5)
            except Exception:
                pass
    except Exception:
        pass
    await dispose_engine()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.project_name,
        version=__version__,
        description="Multi-tenant AI agent platform with RAG, structured outputs, and observability built in.",
        docs_url=settings.docs_url,
        redoc_url=settings.redoc_url,
        openapi_url=f"{settings.api_v1_prefix}/openapi.json" if not settings.is_production else None,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allow_origins,
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["x-request-id"],
    )
    app.add_middleware(RequestIdMiddleware)
    app.add_middleware(RateLimitMiddleware)

    register_exception_handlers(app)

    @app.get("/health", tags=["meta"])
    async def health() -> dict:
        db_ok = True
        try:
            await healthcheck()
        except Exception:
            db_ok = False
        return {"status": "ok" if db_ok else "degraded", "db": db_ok, "version": __version__}

    @app.get("/", tags=["meta"])
    async def root() -> dict:
        return {"name": settings.project_name, "version": __version__, "env": settings.env}

    _register_routers(app)

    return app


def _register_routers(app: FastAPI) -> None:
    from noufex_ai.modules.users.router import router as users_router
    from noufex_ai.modules.tenants.router import router as tenants_router
    from noufex_ai.modules.agents.router import router as agents_router
    from noufex_ai.modules.rag.router import router as rag_router
    from noufex_ai.modules.chat.router import router as chat_router
    from noufex_ai.modules.billing.router import router as billing_router
    from noufex_ai.modules.computer.router import router as computer_router
    from noufex_ai.modules.browser.router import router as browser_router
    from noufex_ai.modules.design.router import router as design_router

    prefix = settings.api_v1_prefix
    app.include_router(users_router, prefix=f"{prefix}/users", tags=["users"])
    app.include_router(tenants_router, prefix=f"{prefix}/tenants", tags=["tenants"])
    app.include_router(agents_router, prefix=f"{prefix}/agents", tags=["agents"])
    app.include_router(rag_router, prefix=f"{prefix}/rag", tags=["rag"])
    app.include_router(chat_router, prefix=f"{prefix}/chat", tags=["chat"])
    app.include_router(billing_router, prefix=f"{prefix}/billing", tags=["billing"])
    app.include_router(computer_router, prefix=f"{prefix}/computer", tags=["computer"])
    app.include_router(browser_router, prefix=f"{prefix}/browser", tags=["browser"])
    app.include_router(design_router, prefix=f"{prefix}/design", tags=["design"])


app = create_app()
