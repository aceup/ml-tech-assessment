"""
Dependency injection factories.

Provides singleton instances for services, adapters, and security components.
"""

from functools import lru_cache

from app.backend.adapters.groq import GroqAdapter
from app.backend.adapters.openai import OpenAIAdapter
from app.backend.core.config import Settings, get_settings
from app.backend.core.logging import get_logger
from app.backend.ports.llm import LLm
from app.backend.ports.repository import AnalysisRepository
from app.backend.repositories.in_memory import InMemoryAnalysisRepository
from app.backend.services.analysis_service import AnalysisService
from app.backend.services.guardrails_service import GuardrailsService
from app.backend.services.pii_service import PIIService

logger = get_logger(__name__)


@lru_cache
def get_pii_service() -> PIIService:
    """
    Get singleton PII detection service.

    Returns:
        PII service (enabled/disabled based on config)
    """
    settings = get_settings()
    return PIIService(enabled=settings.enable_pii_detection)


@lru_cache
def get_guardrails_service() -> GuardrailsService:
    """
    Get singleton guardrails service for input/output validation.

    Returns:
        Guardrails service configured with token limits
    """
    settings = get_settings()
    return GuardrailsService(
        max_input_tokens=settings.max_input_tokens,
        max_output_tokens=settings.max_output_tokens,
    )


@lru_cache
def get_repository() -> AnalysisRepository:
    """
    Get singleton repository instance (in-memory or Redis based on config).

    Returns:
        Analysis repository (type depends on REPOSITORY_BACKEND setting)

    Raises:
        ValueError: If unsupported backend is configured
    """
    settings = get_settings()

    if settings.repository_backend == "memory":
        logger.info(
            "repository_memory",
            message="Using in-memory repository (not persistent)",
        )
        return InMemoryAnalysisRepository()

    elif settings.repository_backend == "redis":
        try:
            from app.backend.infrastructure.redis_client import get_redis_sync_client
            from app.backend.repositories.redis_sync import RedisSyncRepository

            redis_client_wrapper = get_redis_sync_client()
            redis_client = redis_client_wrapper.get_client()

            repo = RedisSyncRepository(
                redis_client=redis_client,
                environment=settings.environment,
                ttl_seconds=settings.redis_ttl_seconds,
            )

            logger.info(
                "repository_redis",
                message="Using synchronous Redis repository (persistent)",
                environment=settings.environment,
                ttl_seconds=settings.redis_ttl_seconds,
            )

            return repo

        except Exception as e:
            logger.error(
                "repository_redis_failed",
                message="Failed to initialize Redis repository, falling back to memory",
                error=str(e),
            )
            # Fall back to in-memory
            return InMemoryAnalysisRepository()

    else:
        raise ValueError(
            f"Unsupported repository backend: {settings.repository_backend}"
        )


@lru_cache
def get_llm_adapter() -> LLm:
    """
    Get LLM adapter based on configuration with security enhancements.

    Factory pattern - selects adapter based on LLM_PROVIDER environment variable.
    Includes token limits, timeouts, and content moderation.

    Returns:
        Configured LLM adapter (OpenAI or Groq)

    Raises:
        ValueError: If unsupported LLM provider is specified
    """
    settings = get_settings()

    # Factory pattern - select adapter based on provider
    if settings.llm_provider == "openai":
        if not settings.openai_api_key:
            raise ValueError("OpenAI API key is required when using OpenAI provider")
        return OpenAIAdapter(
            api_key=settings.openai_api_key,
            model=settings.openai_model,
            timeout=settings.openai_timeout,
            max_retries=settings.openai_max_retries,
            max_tokens=settings.max_output_tokens,
            enable_moderation=settings.enable_output_moderation,
        )
    elif settings.llm_provider == "groq":
        if not settings.groq_api_key:
            raise ValueError("Groq API key is required when using Groq provider")
        return GroqAdapter(
            api_key=settings.groq_api_key,
            model=settings.groq_model,
            timeout=30,  # Groq doesn't have config yet, use default
            max_retries=3,
            max_tokens=settings.max_output_tokens,
        )
    else:
        raise ValueError(f"Unsupported LLM provider: {settings.llm_provider}")


@lru_cache
def get_analysis_service() -> AnalysisService:
    """
    Get singleton analysis service instance with security layers.

    Returns:
        Configured analysis service with LLM adapter, repository, and security services
    """
    settings = get_settings()
    llm_adapter = get_llm_adapter()
    repository = get_repository()
    pii_service = get_pii_service()
    guardrails_service = get_guardrails_service()

    return AnalysisService(
        llm_adapter=llm_adapter,
        repository=repository,
        pii_service=pii_service,
        guardrails_service=guardrails_service,
        enable_moderation=settings.enable_output_moderation,
    )
