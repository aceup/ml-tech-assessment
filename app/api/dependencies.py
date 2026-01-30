"""FastAPI dependency injection configuration."""

from functools import lru_cache

from app.adapters.in_memory_repo import InMemoryTranscriptRepository
from app.adapters.openai import OpenAIAdapter
from app.application.services import TranscriptService
from app.configurations import EnvConfigs
from app.ports.repository import TranscriptRepository


@lru_cache
def get_settings() -> EnvConfigs:
    """Get cached application settings."""
    return EnvConfigs()


@lru_cache
def get_repository() -> TranscriptRepository:
    """Get singleton repository instance."""
    return InMemoryTranscriptRepository()


def get_transcript_service() -> TranscriptService:
    """Create and return the transcript service with dependencies."""
    settings = get_settings()
    llm = OpenAIAdapter(
        api_key=settings.OPENAI_API_KEY,
        model=settings.OPENAI_MODEL,
    )
    repository = get_repository()
    return TranscriptService(llm=llm, repository=repository)
