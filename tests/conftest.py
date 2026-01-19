"""
Global test configuration and fixtures.

Provides test fixtures for FastAPI testing with dependency overrides,
mock LLM adapters, and test data generation.
"""

import asyncio
import os
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import (
    get_analysis_service,
    get_llm_adapter,
    get_repository,
    get_settings,
)
from app.core.config import Settings
from app.main import create_app
from app.repositories.in_memory import InMemoryAnalysisRepository
from app.services.analysis_service import AnalysisService, LLMAnalysisResult


# ============================================================================
# Test Environment Setup
# ============================================================================

# Set test API key for all tests
# This ensures tests don't use production API key from .env
os.environ["API_KEY"] = "test-api-key-12345"


# ============================================================================
# Pytest Configuration
# ============================================================================


def pytest_configure(config):
    """Configure pytest with async support and custom markers."""
    config.addinivalue_line("markers", "asyncio: mark test as async")
    config.addinivalue_line("markers", "integration: mark test as integration test (requires external services)")
    config.addinivalue_line("markers", "security: mark test as security-focused test")
    config.addinivalue_line("markers", "slow: mark test as slow running")
    config.addinivalue_line("markers", "pii: mark test as requiring spaCy model (382MB)")


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ============================================================================
# Settings & Configuration Fixtures
# ============================================================================


@pytest.fixture
def test_settings() -> Settings:
    """
    Create test settings with test API key.

    Uses the test API key from environment for consistent authentication.
    """
    # Create settings with test configuration
    # API key will be read from environment (set at line 34)
    settings = Settings(
        environment="development",
        debug=True,
        llm_provider="openai",
        openai_api_key="test-key-12345",  # Dummy key for testing
        openai_model="gpt-4o",
        groq_api_key="test-groq-key-12345",  # Dummy key for testing
        groq_model="llama-3.3-70b-versatile",
        log_level="DEBUG",
        log_format="colored",
        enable_docs=True,
        enable_request_logging=False,  # Disable for cleaner test output
        enable_gzip=False,  # Disable compression in tests
        # api_key will be read from environment variable (test-api-key-12345)
    )
    return settings


@pytest.fixture(autouse=True)
def reset_lru_caches():
    """
    Reset all @lru_cache decorated functions between tests.

    CRITICAL: This prevents test pollution from singleton pattern.
    Runs automatically before each test.
    """
    # Clear all LRU caches before each test
    get_settings.cache_clear()
    get_repository.cache_clear()
    get_llm_adapter.cache_clear()
    get_analysis_service.cache_clear()

    yield

    # Clear again after test
    get_settings.cache_clear()
    get_repository.cache_clear()
    get_llm_adapter.cache_clear()
    get_analysis_service.cache_clear()


# ============================================================================
# Mock LLM Adapters
# ============================================================================


@pytest.fixture
def mock_openai_adapter() -> AsyncMock:
    """
    Create mock OpenAI adapter for testing.

    Returns AsyncMock with proper async behavior and default responses.
    """
    from app.ports.llm import LLMResponse

    mock = AsyncMock()
    mock_parsed = LLMAnalysisResult(
        summary="Test summary from OpenAI",
        next_actions=["Action one", "Action two", "Action three"],
    )
    mock_llm_response = LLMResponse(
        parsed_result=mock_parsed,
        raw_response='{"summary":"Test summary from OpenAI","next_actions":["Action one","Action two","Action three"]}',
        input_tokens=100,
        output_tokens=50,
        total_tokens=150,
        latency_ms=200.0,
        model="gpt-4o",
        provider="openai",
    )
    mock.run_completion_async = AsyncMock(return_value=mock_llm_response)
    mock.run_completion = MagicMock(return_value=mock_parsed)  # Sync version still returns parsed result
    return mock


@pytest.fixture
def mock_groq_adapter() -> AsyncMock:
    """
    Create mock Groq adapter for testing.

    Returns AsyncMock with proper async behavior and default responses.
    """
    from app.ports.llm import LLMResponse

    mock = AsyncMock()
    mock_parsed = LLMAnalysisResult(
        summary="Test summary from Groq",
        next_actions=["Groq action one", "Groq action two"],
    )
    mock_llm_response = LLMResponse(
        parsed_result=mock_parsed,
        raw_response='{"summary":"Test summary from Groq","next_actions":["Groq action one","Groq action two"]}',
        input_tokens=120,
        output_tokens=60,
        total_tokens=180,
        latency_ms=150.0,
        model="llama-3.3-70b-versatile",
        provider="groq",
    )
    mock.run_completion_async = AsyncMock(return_value=mock_llm_response)
    mock.run_completion = MagicMock(return_value=mock_parsed)  # Sync version still returns parsed result
    return mock


# ============================================================================
# Repository Fixtures
# ============================================================================


@pytest.fixture
def repository() -> Generator[InMemoryAnalysisRepository, None, None]:
    """
    Create fresh repository instance with automatic cleanup.

    Yields a clean repository and clears it after test completes.
    """
    repo = InMemoryAnalysisRepository()
    yield repo
    # Cleanup: clear all data after test
    repo.clear()


# ============================================================================
# Service Fixtures
# ============================================================================


@pytest.fixture
def analysis_service(
    mock_openai_adapter: AsyncMock,
    repository: InMemoryAnalysisRepository,
) -> AnalysisService:
    """
    Create analysis service with mocked dependencies.

    Uses mock LLM adapter and clean repository.
    """
    return AnalysisService(
        llm_adapter=mock_openai_adapter,
        repository=repository,
    )


# ============================================================================
# FastAPI Test Client Fixtures
# ============================================================================


@pytest.fixture
def client(
    test_settings: Settings,
    mock_openai_adapter: AsyncMock,
    repository: InMemoryAnalysisRepository,
) -> Generator[TestClient, None, None]:
    """
    Create FastAPI TestClient with dependency overrides.

    Overrides:
    - Settings: Use test configuration (with API key disabled)
    - LLM adapter: Use mock adapter (no real API calls)
    - Repository: Use clean repository instance
    """

    # Create analysis service with mocked dependencies
    service = AnalysisService(
        llm_adapter=mock_openai_adapter,
        repository=repository,
    )

    # Override get_settings BEFORE creating app so api_key=None is used
    from app.core import config as config_module

    original_get_settings = config_module.get_settings
    get_settings.cache_clear()

    # Temporarily override the function
    config_module.get_settings = lambda: test_settings

    # Create app with test settings already in place
    fastapi_app = create_app()

    # Restore original and set overrides
    config_module.get_settings = original_get_settings
    fastapi_app.dependency_overrides[get_settings] = lambda: test_settings
    fastapi_app.dependency_overrides[get_llm_adapter] = lambda: mock_openai_adapter
    fastapi_app.dependency_overrides[get_repository] = lambda: repository
    fastapi_app.dependency_overrides[get_analysis_service] = lambda: service

    with TestClient(fastapi_app) as test_client:
        yield test_client

    # Cleanup: clear overrides after test
    fastapi_app.dependency_overrides.clear()


@pytest.fixture
def auth_headers() -> dict[str, str]:
    """Get authentication headers for test requests."""
    return {"X-API-Key": "test-api-key-12345"}


@pytest.fixture
async def async_client(
    test_settings: Settings,
    mock_openai_adapter: AsyncMock,
    repository: InMemoryAnalysisRepository,
) -> AsyncGenerator[TestClient, None]:
    """
    Create async FastAPI TestClient for async endpoint testing.

    Similar to client fixture but supports async context.
    """
    service = AnalysisService(
        llm_adapter=mock_openai_adapter,
        repository=repository,
    )

    app = create_app()
    app.dependency_overrides[get_settings] = lambda: test_settings
    app.dependency_overrides[get_llm_adapter] = lambda: mock_openai_adapter
    app.dependency_overrides[get_repository] = lambda: repository
    app.dependency_overrides[get_analysis_service] = lambda: service

    async with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


# ============================================================================
# Security Service Fixtures
# ============================================================================


@pytest.fixture
def pii_service_enabled():
    """Create PII service with detection enabled."""
    from app.services.pii_service import PIIService

    return PIIService(enabled=True)


@pytest.fixture
def pii_service_disabled():
    """Create PII service with detection disabled."""
    from app.services.pii_service import PIIService

    return PIIService(enabled=False)


@pytest.fixture
def guardrails_service():
    """Create guardrails service with standard limits."""
    from app.services.guardrails_service import GuardrailsService

    return GuardrailsService(
        max_input_tokens=10000,
        max_output_tokens=2000,
    )


@pytest.fixture
def strict_guardrails_service():
    """Create guardrails service with strict limits for testing."""
    from app.services.guardrails_service import GuardrailsService

    return GuardrailsService(
        max_input_tokens=100,
        max_output_tokens=50,
    )


# ============================================================================
# Synthetic Test Data Fixtures
# ============================================================================


@pytest.fixture
def synthetic_pii_samples():
    """Load synthetic PII samples for testing."""
    from tests.fixtures.synthetic_pii import (
        BUSINESS_TRANSCRIPT_WITH_PII,
        CLEAN_COACHING_TRANSCRIPT,
        HEAVY_PII_TRANSCRIPT,
        MEDICAL_TRANSCRIPT_WITH_PII,
        MINIMAL_PII_TRANSCRIPT,
    )

    return {
        "medical": MEDICAL_TRANSCRIPT_WITH_PII,
        "business": BUSINESS_TRANSCRIPT_WITH_PII,
        "minimal": MINIMAL_PII_TRANSCRIPT,
        "heavy": HEAVY_PII_TRANSCRIPT,
        "clean": CLEAN_COACHING_TRANSCRIPT,
    }


@pytest.fixture
def prompt_injection_samples():
    """Load prompt injection attack samples."""
    from tests.fixtures.prompt_injection_samples import (
        ALL_ATTACK_SAMPLES,
        BASIC_INJECTIONS,
        JAILBREAK_ATTEMPTS,
        LEGITIMATE_CONTENT_WITH_KEYWORDS,
    )

    return {
        "all": ALL_ATTACK_SAMPLES,
        "basic": BASIC_INJECTIONS,
        "jailbreak": JAILBREAK_ATTEMPTS,
        "legitimate": LEGITIMATE_CONTENT_WITH_KEYWORDS,
    }


# ============================================================================
# Redis Integration Test Fixtures
# ============================================================================


@pytest.fixture
async def redis_client():
    """
    Create Redis client for testing.

    Uses DB 15 to avoid conflicts with development data.
    Skips tests if Redis is not available.
    """
    from redis.asyncio import Redis
    from redis.exceptions import ConnectionError as RedisConnectionError

    client = Redis(
        host="localhost",
        port=6379,
        db=15,  # Separate DB for tests
        decode_responses=False,
    )

    # Test connection
    try:
        await client.ping()
    except RedisConnectionError:
        pytest.skip("Redis not available for testing")

    yield client

    # Cleanup: flush test database
    await client.flushdb()
    await client.aclose()


# ============================================================================
# Pytest Command Line Options
# ============================================================================


def pytest_addoption(parser):
    """Add custom command line options."""
    parser.addoption(
        "--integration",
        action="store_true",
        default=False,
        help="Run integration tests (requires external services like Redis)",
    )


def pytest_collection_modifyitems(config, items):
    """
    Modify test collection to handle integration tests.

    Skip integration tests unless --integration flag is provided.
    """
    skip_integration = pytest.mark.skip(reason="Run with --integration to execute")
    run_integration = config.getoption("--integration", default=False)

    for item in items:
        # Skip integration tests unless flag is set
        if "integration" in item.keywords and not run_integration:
            item.add_marker(skip_integration)
