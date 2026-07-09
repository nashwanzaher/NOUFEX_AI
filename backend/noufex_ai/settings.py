from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, PostgresDsn, RedisDsn, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="ignore",
    )

    env: Literal["development", "staging", "production"] = "development"
    debug: bool = False
    project_name: str = "NOUFEX AI"
    api_v1_prefix: str = "/v1"

    secret_key: SecretStr = Field(default=SecretStr("dev-insecure-change-me"))
    jwt_algorithm: Literal["EdDSA", "RS256"] = "EdDSA"
    jwt_private_key: SecretStr | None = None
    jwt_public_key: SecretStr | None = None
    access_token_ttl_minutes: int = 15
    refresh_token_ttl_days: int = 30
    argon2_time_cost: int = 3
    argon2_memory_cost: int = 65536
    argon2_parallelism: int = 4

    database_url: PostgresDsn = Field(
        default=PostgresDsn("postgresql+asyncpg://postgres:postgres@localhost:5432/noufex_ai")
    )
    database_sync_url: PostgresDsn = Field(
        default=PostgresDsn("postgresql+psycopg2://postgres:postgres@localhost:5432/noufex_ai")
    )
    database_pool_size: int = 10
    database_max_overflow: int = 20
    database_pool_timeout_seconds: int = 10

    redis_url: RedisDsn = Field(default=RedisDsn("redis://localhost:6379/0"))
    celery_broker_url: RedisDsn = Field(default=RedisDsn("redis://localhost:6379/1"))
    celery_result_backend: RedisDsn = Field(default=RedisDsn("redis://localhost:6379/2"))

    openai_api_key: SecretStr | None = None
    openai_default_model: str = "gpt-4o-mini"
    openai_embedding_model: str = "text-embedding-3-small"
    openai_embedding_dimensions: int = 1536
    openai_max_output_tokens: int = 1024
    openai_request_timeout_seconds: float = 30.0

    stripe_secret_key: SecretStr | None = None
    stripe_webhook_secret: SecretStr | None = None

    sentry_dsn: SecretStr | None = None
    sentry_traces_sample_rate: float = 0.1

    otel_service_name: str = "noufex-ai"
    otel_exporter_otlp_endpoint: str | None = None

    cors_allow_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])
    cors_allow_credentials: bool = True

    rate_limit_per_minute_per_ip: int = 60
    rate_limit_per_minute_per_user: int = 120

    file_upload_max_size_mb: int = 25
    allowed_upload_mime_types: tuple[str, ...] = (
        "application/pdf",
        "text/plain",
        "text/markdown",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "text/html",
    )

    docs_url: str | None = "/docs"
    redoc_url: str | None = "/redoc"

    enable_structured_logging: bool = True
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    # Browser automation
    browser_default_headless: bool = False
    browser_default_viewport_width: int = 1280
    browser_default_viewport_height: int = 720
    browser_cdp_port: int = 9222

    # Computer control
    computer_enable_command_execution: bool = True
    computer_screenshot_quality: int = 80
    computer_mouse_speed: float = 0.5

    # Agent skills
    agent_skills_max_iterations: int = 10
    agent_skills_auto_confirm_safe: bool = False

    # Design system
    design_default_primary_color: str = "#3B82F6"
    design_default_font_family: str = "Inter, system-ui, sans-serif"
    design_default_scheme: Literal["light", "dark", "midnight", "sunset", "pastel", "corporate", "ocean", "forest", "autumn", "spring", "sepia", "contrast"] = "light"
    design_default_output_dir: str | None = None  # e.g., "./generated"

    @field_validator("cors_allow_origins", mode="before")
    @classmethod
    def _split_cors(cls, v: object) -> object:
        if isinstance(v, str) and not v.startswith("["):
            return [s.strip() for s in v.split(",") if s.strip()]
        return v

    @property
    def async_database_url(self) -> str:
        url = str(self.database_url)
        if url.startswith("postgresql+psycopg2"):
            return url.replace("postgresql+psycopg2", "postgresql+asyncpg", 1)
        return url

    @property
    def is_production(self) -> bool:
        return self.env == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
