from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from noufex_ai.exceptions import (
    AppError,
    ConflictError,
    ForbiddenError,
    NotFoundError,
    UnauthorizedError,
    register_exception_handlers,
)


def _build_app() -> FastAPI:
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/raise/{kind}")
    def raise_(kind: str):
        cls = {
            "not_found": NotFoundError("missing"),
            "unauth":    UnauthorizedError("bad creds"),
            "forbid":    ForbiddenError("denied"),
            "conflict":  ConflictError("dup"),
            "plain":     AppError("oops"),
        }[kind]
        raise cls("a message")

    return app


def test_handler_not_found():
    app = _build_app()
    client = TestClient(app)
    r = client.get("/raise/not_found")
    assert r.status_code == 404
    body = r.json()
    assert body["error"]["code"] == "not_found"
    assert body["error"]["message"] == "a message"


def test_handler_unauthorized():
    app = _build_app()
    client = TestClient(app)
    r = client.get("/raise/unauth")
    assert r.status_code == 401


def test_handler_unknown_returns_500():
    app = _build_app()
    client = TestClient(app)
    r = client.get("/raise/unknown")
    assert r.status_code == 422  # Pydantic Route validation
