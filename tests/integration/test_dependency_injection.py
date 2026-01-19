"""
Integration tests for dependency injection factory pattern.

Tests the DI factory implementation in app.api.dependencies, including:
- LLM adapter factory pattern (OpenAI vs Groq selection)
- API key validation for different providers
- Singleton behavior via @lru_cache
- Dependency wiring for AnalysisService
"""

import pytest

from app.adapters.groq import GroqAdapter
from app.adapters.openai import OpenAIAdapter
from app.api.dependencies import (
    get_analysis_service,
    get_llm_adapter,
    get_repository,
    get_settings,
)
from app.repositories.in_memory import InMemoryAnalysisRepository
from app.services.analysis_service import AnalysisService


@pytest.fixture(autouse=True)
def clear_all_caches():
    """Clear all LRU caches before and after each test."""
    # Clear before test
    get_settings.cache_clear()
    get_llm_adapter.cache_clear()
    get_repository.cache_clear()
    get_analysis_service.cache_clear()

    yield

    # Clear after test
    get_settings.cache_clear()
    get_llm_adapter.cache_clear()
    get_repository.cache_clear()
    get_analysis_service.cache_clear()


class TestLLMAdapterFactory:
    """Tests for LLM adapter factory pattern."""

    def test_get_llm_adapter_returns_openai_when_provider_is_openai(
        self, monkeypatch
    ):
        """Test that factory returns OpenAI adapter when provider is 'openai'."""
        # Arrange
        monkeypatch.setenv("LLM_PROVIDER", "openai")
        monkeypatch.setenv("OPENAI_API_KEY", "test-key-123")
        get_settings.cache_clear()
        get_llm_adapter.cache_clear()

        # Act
        adapter = get_llm_adapter()

        # Assert
        assert isinstance(adapter, OpenAIAdapter)
        assert adapter._client.api_key == "test-key-123"
        assert adapter._model == "gpt-4o"  # Default model from settings

    def test_get_llm_adapter_returns_groq_when_provider_is_groq(self, monkeypatch):
        """Test that factory returns Groq adapter when provider is 'groq'."""
        # Arrange
        monkeypatch.setenv("LLM_PROVIDER", "groq")
        monkeypatch.setenv("GROQ_API_KEY", "test-groq-key-456")
        get_settings.cache_clear()
        get_llm_adapter.cache_clear()

        # Act
        adapter = get_llm_adapter()

        # Assert
        assert isinstance(adapter, GroqAdapter)
        assert adapter._client.api_key == "test-groq-key-456"
        assert adapter._model == "llama-3.3-70b-versatile"  # Default Groq model

    def test_get_llm_adapter_raises_on_unsupported_provider(self, monkeypatch):
        """Test that factory raises ValidationError for unsupported provider."""
        # Arrange
        monkeypatch.setenv("LLM_PROVIDER", "unsupported_provider")
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")  # Set a key to pass validation
        get_settings.cache_clear()
        get_llm_adapter.cache_clear()

        # Act & Assert - Pydantic catches this at Settings validation level
        from pydantic import ValidationError
        with pytest.raises(ValidationError) as exc_info:
            get_llm_adapter()

        assert "Input should be 'openai' or 'groq'" in str(exc_info.value)

    def test_get_llm_adapter_falls_back_on_missing_openai_key(self, monkeypatch):
        """Test that factory falls back to Groq when OpenAI key is missing."""
        # Arrange - Set OpenAI as provider but provide only Groq key
        monkeypatch.setenv("LLM_PROVIDER", "openai")
        monkeypatch.setenv("OPENAI_API_KEY", "")  # Empty - triggers fallback
        monkeypatch.setenv("GROQ_API_KEY", "test-groq-key-12345")
        monkeypatch.setenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        get_settings.cache_clear()
        get_llm_adapter.cache_clear()

        # Act - Get adapter (should fallback to Groq)
        adapter = get_llm_adapter()

        # Assert - Should get Groq adapter due to automatic fallback
        from app.adapters.groq import GroqAdapter
        assert isinstance(adapter, GroqAdapter), "Should fallback to Groq when OpenAI key missing"

    def test_get_llm_adapter_raises_on_missing_groq_key(self, monkeypatch):
        """Test that factory raises ValueError when Groq key is missing."""
        # Arrange
        monkeypatch.setenv("LLM_PROVIDER", "groq")
        monkeypatch.setenv("GROQ_API_KEY", "")  # Empty string triggers validation
        get_settings.cache_clear()
        get_llm_adapter.cache_clear()

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            get_llm_adapter()

        # This should fail at Settings validation level
        assert "GROQ_API_KEY is required when LLM_PROVIDER=groq" in str(exc_info.value)


class TestSingletonBehavior:
    """Tests for singleton pattern via @lru_cache."""

    def test_get_repository_returns_same_instance_on_multiple_calls(self):
        """Test that get_repository returns the same instance (singleton)."""
        # Arrange & Act
        repo1 = get_repository()
        repo2 = get_repository()
        repo3 = get_repository()

        # Assert
        assert isinstance(repo1, InMemoryAnalysisRepository)
        assert repo1 is repo2
        assert repo2 is repo3
        assert id(repo1) == id(repo2) == id(repo3)

    def test_cache_clear_returns_new_instances(self, monkeypatch):
        """Test that clearing LRU cache creates new instances."""
        # Arrange
        monkeypatch.setenv("LLM_PROVIDER", "openai")
        monkeypatch.setenv("OPENAI_API_KEY", "test-key-123")
        get_settings.cache_clear()
        get_repository.cache_clear()
        get_llm_adapter.cache_clear()
        get_analysis_service.cache_clear()

        # Act - Get first set of instances
        repo1 = get_repository()
        adapter1 = get_llm_adapter()
        service1 = get_analysis_service()

        # Clear caches
        get_repository.cache_clear()
        get_llm_adapter.cache_clear()
        get_analysis_service.cache_clear()
        get_settings.cache_clear()

        # Get new instances after cache clear
        repo2 = get_repository()
        adapter2 = get_llm_adapter()
        service2 = get_analysis_service()

        # Assert - New instances should be different objects
        assert isinstance(repo1, InMemoryAnalysisRepository)
        assert isinstance(repo2, InMemoryAnalysisRepository)
        assert repo1 is not repo2
        assert id(repo1) != id(repo2)

        assert isinstance(adapter1, OpenAIAdapter)
        assert isinstance(adapter2, OpenAIAdapter)
        assert adapter1 is not adapter2
        assert id(adapter1) != id(adapter2)

        assert isinstance(service1, AnalysisService)
        assert isinstance(service2, AnalysisService)
        assert service1 is not service2
        assert id(service1) != id(service2)


class TestDependencyWiring:
    """Tests for dependency injection wiring in AnalysisService."""

    def test_get_analysis_service_wires_dependencies_correctly(self, monkeypatch):
        """Test that AnalysisService is correctly wired with LLM adapter and repository."""
        # Arrange
        monkeypatch.setenv("LLM_PROVIDER", "openai")
        monkeypatch.setenv("OPENAI_API_KEY", "test-key-789")
        get_settings.cache_clear()
        get_llm_adapter.cache_clear()
        get_repository.cache_clear()
        get_analysis_service.cache_clear()

        # Act
        service = get_analysis_service()

        # Assert - Check service type
        assert isinstance(service, AnalysisService)

        # Assert - Check that service has correct dependencies
        assert hasattr(service, "llm_adapter")
        assert hasattr(service, "repository")

        # Assert - Check dependency types
        assert isinstance(service.llm_adapter, OpenAIAdapter)
        assert isinstance(service.repository, InMemoryAnalysisRepository)

        # Assert - Verify dependencies are the same singletons
        assert service.llm_adapter is get_llm_adapter()
        assert service.repository is get_repository()

    def test_get_analysis_service_with_groq_adapter(self, monkeypatch):
        """Test that AnalysisService works with Groq adapter."""
        # Arrange
        monkeypatch.setenv("LLM_PROVIDER", "groq")
        monkeypatch.setenv("GROQ_API_KEY", "test-groq-key-999")
        get_settings.cache_clear()
        get_llm_adapter.cache_clear()
        get_repository.cache_clear()
        get_analysis_service.cache_clear()

        # Act
        service = get_analysis_service()

        # Assert - Check service type
        assert isinstance(service, AnalysisService)

        # Assert - Check that Groq adapter is wired
        assert isinstance(service.llm_adapter, GroqAdapter)
        assert isinstance(service.repository, InMemoryAnalysisRepository)

        # Assert - Verify it's using the Groq singleton
        assert service.llm_adapter is get_llm_adapter()
        assert service.repository is get_repository()


class TestFactoryErrorHandling:
    """Tests for error handling in factory functions."""

    def test_openai_adapter_with_custom_model(self, monkeypatch):
        """Test that OpenAI adapter respects custom model configuration."""
        # Arrange
        monkeypatch.setenv("LLM_PROVIDER", "openai")
        monkeypatch.setenv("OPENAI_API_KEY", "test-key-custom")
        monkeypatch.setenv("OPENAI_MODEL", "gpt-4-turbo")
        get_settings.cache_clear()
        get_llm_adapter.cache_clear()

        # Act
        adapter = get_llm_adapter()

        # Assert
        assert isinstance(adapter, OpenAIAdapter)
        assert adapter._model == "gpt-4-turbo"

    def test_groq_adapter_with_custom_model(self, monkeypatch):
        """Test that Groq adapter respects custom model configuration."""
        # Arrange
        monkeypatch.setenv("LLM_PROVIDER", "groq")
        monkeypatch.setenv("GROQ_API_KEY", "test-groq-custom")
        monkeypatch.setenv("GROQ_MODEL", "llama-3.1-8b-instant")
        get_settings.cache_clear()
        get_llm_adapter.cache_clear()

        # Act
        adapter = get_llm_adapter()

        # Assert
        assert isinstance(adapter, GroqAdapter)
        assert adapter._model == "llama-3.1-8b-instant"

    def test_settings_validation_prevents_invalid_provider(self, monkeypatch):
        """Test that Settings validation catches invalid provider values."""
        # Arrange
        monkeypatch.setenv("LLM_PROVIDER", "invalid_llm")
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        get_settings.cache_clear()

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            get_settings()

        # Pydantic validation should catch this at Settings level
        assert "llm_provider" in str(exc_info.value).lower()
