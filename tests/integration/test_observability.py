"""
Integration tests for observability features.

Tests verify end-to-end observability metadata capture including:
- Prompt versioning and raw exchange storage
- Token usage tracking
- Latency measurement
- PII detection logging
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch

from app.adapters.openai import OpenAIAdapter
from app.models.responses import AnalysisResult
from app.ports.llm import LLMResponse
from app.repositories.in_memory import InMemoryAnalysisRepository
from app.services.analysis_service import AnalysisService, LLMAnalysisResult
from app.services.pii_service import PIIService


class TestObservabilityCapture:
    """Test observability metadata capture in analysis workflow."""

    @pytest.mark.asyncio
    async def test_analysis_includes_observability_metadata(self) -> None:
        """Test that analysis captures complete observability metadata."""
        # Setup repository
        repository = InMemoryAnalysisRepository()

        # Mock LLM adapter to return LLMResponse with observability
        mock_adapter = Mock(spec=OpenAIAdapter)
        mock_parsed = LLMAnalysisResult(
            summary="Test summary", next_actions=["Action 1", "Action 2"]
        )
        mock_llm_response = LLMResponse(
            parsed_result=mock_parsed,
            raw_response='{"summary":"Test summary","next_actions":["Action 1","Action 2"]}',
            input_tokens=100,
            output_tokens=50,
            total_tokens=150,
            latency_ms=250.5,
            model="gpt-4o",
            provider="openai",
        )
        mock_adapter.run_completion_async = AsyncMock(return_value=mock_llm_response)

        # Create service with PII detection disabled for simplicity
        service = AnalysisService(
            llm_adapter=mock_adapter,
            repository=repository,
            pii_service=None,
            guardrails_service=None,
            enable_moderation=False,
        )

        # Execute analysis
        result = await service.analyze("Test transcript for analysis", num_next_actions=2)

        # Verify observability metadata is captured
        assert result.observability is not None
        obs = result.observability

        # Pillar A: Traceability
        assert obs.prompt_version == "v1.0"
        assert obs.raw_system_prompt is not None
        assert "business coach" in obs.raw_system_prompt.lower()
        assert obs.raw_user_prompt is not None
        assert "Test transcript for analysis" in obs.raw_user_prompt
        assert obs.raw_llm_response == mock_llm_response.raw_response

        # Pillar B: Performance
        assert obs.latency_ms == 250.5
        assert obs.input_tokens == 100
        assert obs.output_tokens == 50
        assert obs.total_tokens == 150
        assert obs.llm_provider == "openai"
        assert obs.llm_model == "gpt-4o"

        # Pillar C: Semantic Logging
        assert obs.retry_count == 0
        assert obs.validation_failures == []
        assert obs.pii_detected is False

    @pytest.mark.asyncio
    async def test_observability_includes_pii_detection_flag(self) -> None:
        """Test that PII detection is logged in observability."""
        repository = InMemoryAnalysisRepository()

        # Mock LLM adapter
        mock_adapter = Mock(spec=OpenAIAdapter)
        mock_parsed = LLMAnalysisResult(
            summary="Test summary", next_actions=["Action 1"]
        )
        mock_llm_response = LLMResponse(
            parsed_result=mock_parsed,
            raw_response='{"summary":"Test summary","next_actions":["Action 1"]}',
            input_tokens=80,
            output_tokens=40,
            total_tokens=120,
            latency_ms=200.0,
            model="gpt-4o",
            provider="openai",
        )
        mock_adapter.run_completion_async = AsyncMock(return_value=mock_llm_response)

        # Enable PII service
        pii_service = PIIService(enabled=True)

        service = AnalysisService(
            llm_adapter=mock_adapter,
            repository=repository,
            pii_service=pii_service,
            guardrails_service=None,
            enable_moderation=False,
        )

        # Analyze transcript with PII
        result = await service.analyze(
            "Patient John Smith (john@example.com) discussed symptoms",
            num_next_actions=1,
        )

        # Verify PII detection is logged
        assert result.observability is not None
        assert result.observability.pii_detected is True

    @pytest.mark.asyncio
    async def test_observability_stored_in_repository(self) -> None:
        """Test that observability metadata persists in repository."""
        repository = InMemoryAnalysisRepository()

        # Mock LLM adapter
        mock_adapter = Mock(spec=OpenAIAdapter)
        mock_parsed = LLMAnalysisResult(
            summary="Stored test", next_actions=["Store action"]
        )
        mock_llm_response = LLMResponse(
            parsed_result=mock_parsed,
            raw_response='{"summary":"Stored test","next_actions":["Store action"]}',
            input_tokens=75,
            output_tokens=35,
            total_tokens=110,
            latency_ms=180.0,
            model="gpt-4o-mini",
            provider="openai",
        )
        mock_adapter.run_completion_async = AsyncMock(return_value=mock_llm_response)

        service = AnalysisService(
            llm_adapter=mock_adapter,
            repository=repository,
            pii_service=None,
            guardrails_service=None,
            enable_moderation=False,
        )

        # Create analysis
        result = await service.analyze("Test persistence", num_next_actions=1)
        analysis_id = result.id

        # Retrieve from repository
        retrieved = repository.get_by_id(analysis_id)

        # Verify observability metadata is intact
        assert retrieved.observability is not None
        assert retrieved.observability.latency_ms == 180.0
        assert retrieved.observability.total_tokens == 110
        assert retrieved.observability.llm_model == "gpt-4o-mini"


class TestBackwardCompatibility:
    """Test backward compatibility of observability field."""

    def test_analysis_response_without_observability_is_valid(self) -> None:
        """Test that AnalysisResponse works without observability (old data)."""
        from datetime import datetime, UTC
        from app.models.responses import AnalysisResponse

        # Create response without observability (simulates old data)
        response = AnalysisResponse(
            id="test-id",
            summary="Test summary",
            next_actions=["Action 1"],
            created_at=datetime.now(UTC),
            transcript="Test transcript",
            # observability field omitted (defaults to None)
        )

        # Verify it's valid and observability is None
        assert response.observability is None
        assert response.summary == "Test summary"

    def test_repository_handles_none_observability(self) -> None:
        """Test that repository can save/load analyses without observability."""
        from datetime import datetime, UTC
        from app.models.responses import AnalysisResponse

        repository = InMemoryAnalysisRepository()

        # Create analysis without observability
        analysis = AnalysisResponse(
            id="legacy-id",
            summary="Legacy analysis",
            next_actions=["Legacy action"],
            created_at=datetime.now(UTC),
            transcript="Legacy transcript",
            observability=None,
        )

        # Save and retrieve
        repository.save(analysis)
        retrieved = repository.get_by_id("legacy-id")

        # Verify it works
        assert retrieved.observability is None
        assert retrieved.summary == "Legacy analysis"
