"""
Settings management using Pydantic Settings.

Provides type-safe configuration with validation and environment variable support.
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Environment
    environment: Literal["development", "staging", "production"] = Field(
        default="development",
        description="Deployment environment",
    )
    debug: bool = Field(
        default=False,
        description="Enable debug mode (not allowed in production)",
    )

    # API Configuration
    api_title: str = Field(
        default="Transcript Analysis API",
        description="API title for documentation",
    )
    api_version: str = Field(
        default="1.0.0",
        description="API version",
    )
    api_prefix: str = Field(
        default="/api/v1",
        description="API route prefix",
    )
    api_key: str | None = Field(
        default=None,
        description="API key for authentication (optional - if not set, no auth required)",
    )

    # LLM Provider Selection
    llm_provider: Literal["openai", "groq"] = Field(
        default="openai",
        description="LLM provider to use (openai or groq)",
    )

    # OpenAI Configuration
    openai_api_key: str | None = Field(
        default=None,
        description="OpenAI API key (required if llm_provider=openai)",
    )
    openai_model: str = Field(
        default="gpt-4o",
        description="OpenAI model to use",
    )
    openai_timeout: int = Field(
        default=30,
        ge=1,
        le=120,
        description="OpenAI API timeout in seconds",
    )
    openai_max_retries: int = Field(
        default=3,
        ge=0,
        le=10,
        description="Maximum retry attempts for OpenAI API calls",
    )

    # Groq Configuration
    groq_api_key: str | None = Field(
        default=None,
        description="Groq API key (required if llm_provider=groq)",
    )
    groq_model: str = Field(
        default="llama-3.3-70b-versatile",
        description="Groq model to use",
    )

    # CORS Configuration
    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        description="Allowed CORS origins",
    )
    cors_allow_credentials: bool = Field(
        default=True,
        description="Allow credentials in CORS requests",
    )
    cors_allow_methods: list[str] = Field(
        default=["*"],
        description="Allowed HTTP methods for CORS",
    )
    cors_allow_headers: list[str] = Field(
        default=["*"],
        description="Allowed headers for CORS",
    )

    # Logging Configuration
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Logging level",
    )
    log_format: Literal["json", "colored"] = Field(
        default="json",
        description="Log output format (json for production, colored for dev)",
    )

    # Server Configuration
    host: str = Field(
        default="0.0.0.0",
        description="Server host",
    )
    port: int = Field(
        default=8000,
        ge=1,
        le=65535,
        description="Server port",
    )
    workers: int = Field(
        default=1,
        ge=1,
        description="Number of worker processes",
    )

    # Feature Flags
    enable_docs: bool = Field(
        default=True,
        description="Enable OpenAPI documentation endpoints",
    )
    enable_request_logging: bool = Field(
        default=True,
        description="Enable request/response logging middleware",
    )
    enable_gzip: bool = Field(
        default=True,
        description="Enable GZip compression middleware",
    )

    # Security Configuration
    enable_pii_detection: bool = Field(
        default=True,
        description="Enable PII detection and masking for transcripts",
    )
    enable_rate_limiting: bool = Field(
        default=True,
        description="Enable rate limiting middleware",
    )
    rate_limit_default: str = Field(
        default="20/minute",
        description="Default rate limit (format: requests/period)",
    )
    max_input_tokens: int = Field(
        default=100000,
        ge=1000,
        description="Maximum tokens allowed in input transcript",
    )
    max_output_tokens: int = Field(
        default=4000,
        ge=100,
        description="Maximum tokens allowed in LLM output",
    )
    enable_output_moderation: bool = Field(
        default=True,
        description="Enable OpenAI moderation API for output validation",
    )

    # Repository Backend
    repository_backend: Literal["memory", "redis"] = Field(
        default="memory",
        description="Storage backend for analysis results (memory or redis)",
    )

    # Redis Configuration
    redis_host: str = Field(
        default="localhost",
        description="Redis server host",
    )
    redis_port: int = Field(
        default=6379,
        ge=1,
        le=65535,
        description="Redis server port",
    )
    redis_db: int = Field(
        default=0,
        ge=0,
        le=15,
        description="Redis database number",
    )
    redis_password: str | None = Field(
        default=None,
        description="Redis password (optional)",
    )
    redis_max_connections: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Maximum Redis connection pool size",
    )
    redis_ttl_seconds: int | None = Field(
        default=None,
        description="TTL for Redis keys in seconds (None = no expiration)",
    )
    redis_fallback_ip: str | None = Field(
        default=None,
        description="Fallback IP address for Redis when DNS resolution fails",
    )

    @field_validator("debug")
    @classmethod
    def no_debug_in_production(cls, v: bool, info) -> bool:
        """Ensure debug mode is disabled in production."""
        environment = info.data.get("environment")
        if v and environment == "production":
            raise ValueError("Debug mode is not allowed in production environment")
        return v

    @model_validator(mode="after")
    def auto_select_provider_and_validate(self) -> "Settings":
        """
        Auto-select LLM provider based on available API keys.

        If llm_provider is 'openai' but OPENAI_API_KEY is not set,
        automatically fallback to 'groq' if GROQ_API_KEY is available.

        This runs after all fields are set, allowing us to check all keys.
        """
        from app.core.logging import get_logger

        # If OpenAI is selected but key is missing, try Groq fallback
        if self.llm_provider == "openai" and not self.openai_api_key:
            if self.groq_api_key:
                logger = get_logger(__name__)
                logger.warning(
                    "llm_provider_fallback",
                    message="OpenAI API key not found, falling back to Groq",
                    original_provider="openai",
                    fallback_provider="groq",
                )
                self.llm_provider = "groq"
            else:
                raise ValueError(
                    "OPENAI_API_KEY is required when LLM_PROVIDER=openai, "
                    "or provide GROQ_API_KEY for automatic fallback"
                )

        # Validate that the selected provider has a key
        if self.llm_provider == "openai" and not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required when LLM_PROVIDER=openai")

        if self.llm_provider == "groq" and not self.groq_api_key:
            raise ValueError("GROQ_API_KEY is required when LLM_PROVIDER=groq")

        return self

    @field_validator("log_format")
    @classmethod
    def json_logs_in_production(cls, v: str, info) -> str:
        """Ensure JSON logging is used in production."""
        environment = info.data.get("environment")
        if environment == "production" and v != "json":
            raise ValueError("Production environment must use JSON log format")
        return v

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v) -> list[str]:
        """Parse CORS origins from comma-separated string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment == "development"

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == "production"

    @property
    def docs_url(self) -> str | None:
        """Get OpenAPI docs URL or None if disabled."""
        return "/docs" if self.enable_docs else None

    @property
    def redoc_url(self) -> str | None:
        """Get ReDoc URL or None if disabled."""
        return "/redoc" if self.enable_docs else None

    @property
    def redis_url(self) -> str:
        """
        Build Redis connection URL.

        Returns:
            str: Redis connection URL with optional password
        """
        if self.redis_password:
            return (
                f"redis://:{self.redis_password}@{self.redis_host}:"
                f"{self.redis_port}/{self.redis_db}"
            )
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"


@lru_cache
def get_settings() -> Settings:
    """
    Get cached settings instance.

    Uses lru_cache to ensure settings are loaded only once and reused.
    This is the recommended pattern for FastAPI dependency injection.

    Returns:
        Settings: Validated settings instance
    """
    return Settings()
