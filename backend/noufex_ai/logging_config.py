from __future__ import annotations

import logging
import sys

from pythonjsonlogger import jsonlogger

from noufex_ai.settings import settings


class ContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.env = settings.env
        record.service = settings.project_name
        return True


def configure_logging() -> None:
    level = getattr(logging, settings.log_level)
    root = logging.getLogger()
    root.handlers.clear()

    if settings.enable_structured_logging:
        handler = logging.StreamHandler(sys.stdout)
        formatter = jsonlogger.JsonFormatter(
            "%(asctime)s %(levelname)s %(name)s %(message)s %(env)s %(service)s",
            rename_fields={"asctime": "ts", "levelname": "level", "name": "logger"},
        )
        handler.setFormatter(formatter)
    else:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(
            logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
        )

    handler.addFilter(ContextFilter())
    root.addHandler(handler)
    root.setLevel(level)

    for noisy in ("uvicorn.access", "sqlalchemy.engine", "httpx"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


def get_version() -> str:
    from noufex_ai import __version__

    return __version__
