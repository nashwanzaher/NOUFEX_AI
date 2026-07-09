from __future__ import annotations

import logging

from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from noufex_ai.db import engine
from noufex_ai.settings import settings

logger = logging.getLogger(__name__)


def setup_telemetry(app: FastAPI) -> None:
    resource = Resource.create(
        {
            "service.name": settings.otel_service_name,
            "service.version": "1.0.0",
            "deployment.environment": settings.env,
        }
    )
    provider = TracerProvider(resource=resource)

    if settings.otel_exporter_otlp_endpoint:
        exporter = OTLPSpanExporter(endpoint=settings.otel_exporter_otlp_endpoint)
        provider.add_span_processor(BatchSpanProcessor(exporter))
        logger.info("OTel OTLP exporter enabled: %s", settings.otel_exporter_otlp_endpoint)
    else:
        logger.info("OTel running without exporter (dev mode)")

    trace.set_tracer_provider(provider)

    FastAPIInstrumentor.instrument_app(app)

    if engine is not None:
        try:
            SQLAlchemyInstrumentor().instrument(engine=engine.sync_engine)
        except Exception as exc:
            logger.warning("SQLAlchemy instrumentation failed: %s", exc)


def get_tracer(name: str):
    return trace.get_tracer(name)
