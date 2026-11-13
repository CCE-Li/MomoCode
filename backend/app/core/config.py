from functools import lru_cache
from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_DEV_SESSION_SECRET = "dev-only-change-me"  # noqa: S105


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "MomoCode API"
    environment: str = "development"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"

    database_url: str = "postgresql+asyncpg://momocode:momocode_dev@localhost:5432/momocode"
    redis_url: str = "redis://localhost:6379/0"

    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173"])
    # Dev-only fallback; production startup rejects this value.
    session_secret: str = _DEV_SESSION_SECRET
    session_cookie_name: str = "momo_session"
    csrf_cookie_name: str = "momo_csrf"
    session_cookie_secure: bool = False
    session_ttl_days: int = 30
    rate_limit_enabled: bool = True
    log_level: str = "INFO"

    app_base_url: str = "http://localhost:5173"
    email_backend: Literal["console", "smtp"] = "console"
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_from: str = "no-reply@momocode.local"
    smtp_use_tls: bool = True

    judge_docker_image: str = "momocode-judge:latest"
    judge_timeout_seconds: int = 20
    judge_memory_mb: int = 256

    llm_base_url: str = "https://api.openai.com/v1"
    llm_api_key: str | None = None
    llm_model: str = "gpt-4o-mini"
    llm_timeout_seconds: int = 60

    @model_validator(mode="after")
    def validate_production_security(self) -> "Settings":
        if self.session_ttl_days <= 0:
            raise ValueError("SESSION_TTL_DAYS must be positive")
        if self.environment == "production":
            if self.session_secret == _DEV_SESSION_SECRET:
                raise ValueError("SESSION_SECRET must be set in production")
            if not self.session_cookie_secure:
                raise ValueError("SESSION_COOKIE_SECURE must be true in production")
            if self.email_backend != "smtp":
                raise ValueError("EMAIL_BACKEND must be smtp in production")
            if not self.smtp_host:
                raise ValueError("SMTP_HOST must be set in production")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
