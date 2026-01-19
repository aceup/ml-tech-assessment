"""
Integration tests for analytics endpoint.

Tests verify:
- Cost calculation across different models
- Token usage aggregation
- Latency percentile calculations
- Quality metrics from human evaluations
- Provider breakdown
"""

import pytest
from unittest.mock import Mock
import uuid
from datetime import UTC, datetime

from app.backend.api.v1.endpoints.analytics import calculate_cost
from app.backend.models.evaluation import AnalysisEvaluation
from app.backend.models.observability import ObservabilityMetadata
from app.backend.models.responses import AnalysisResponse
from app.backend.repositories.in_memory import InMemoryAnalysisRepository
from app.backend.services.analysis_service import AnalysisService


class TestCostCalculation:
    """Test cost calculation for different models."""

    def test_calculate_cost_gpt_4o(self) -> None:
        """Test cost calculation for GPT-4o."""
        # GPT-4o: $2.50 per 1M input, $10.00 per 1M output
        cost = calculate_cost("gpt-4o", input_tokens=1000, output_tokens=500)

        # Expected: (1000/1M * 2.50) + (500/1M * 10.00)
        expected = (1000 / 1_000_000 * 2.50) + (500 / 1_000_000 * 10.00)
        assert cost == pytest.approx(expected, rel=1e-6)
        assert cost == pytest.approx(0.0075, rel=1e-6)  # $0.0075

    def test_calculate_cost_gpt_4o_mini(self) -> None:
        """Test cost calculation for GPT-4o-mini."""
        # GPT-4o-mini: $0.15 per 1M input, $0.60 per 1M output
        cost = calculate_cost("gpt-4o-mini", input_tokens=10000, output_tokens=5000)

        expected = (10000 / 1_000_000 * 0.15) + (5000 / 1_000_000 * 0.60)
        assert cost == pytest.approx(expected, rel=1e-6)
        assert cost == pytest.approx(0.0045, rel=1e-6)  # $0.0045

    def test_calculate_cost_llama(self) -> None:
        """Test cost calculation for Llama model."""
        # llama-3.3-70b-versatile: $0.59 per 1M input, $0.79 per 1M output
        cost = calculate_cost("llama-3.3-70b-versatile", input_tokens=5000, output_tokens=2000)

        expected = (5000 / 1_000_000 * 0.59) + (2000 / 1_000_000 * 0.79)
        assert cost == pytest.approx(expected, rel=1e-6)
        assert cost == pytest.approx(0.00453, rel=1e-6)

    def test_calculate_cost_unknown_model_uses_default(self) -> None:
        """Test unknown model defaults to most expensive pricing."""
        # Unknown model should default to gpt-4o pricing
        cost = calculate_cost("unknown-model-xyz", input_tokens=1000, output_tokens=500)

        # Should use GPT-4o pricing
        expected_gpt4o = (1000 / 1_000_000 * 2.50) + (500 / 1_000_000 * 10.00)
        assert cost == pytest.approx(expected_gpt4o, rel=1e-6)


class TestAnalyticsAggregation:
    """Test analytics aggregation across multiple analyses."""

    def create_mock_analysis(
        self,
        model: str,
        provider: str,
        input_tokens: int,
        output_tokens: int,
        latency_ms: float,
    ) -> AnalysisResponse:
        """Helper to create analysis with observability."""
        observability = ObservabilityMetadata(
            prompt_version="v1.0",
            raw_system_prompt="System prompt",
            raw_user_prompt="User prompt",
            raw_llm_response="Response",
            request_id=None,
            latency_ms=latency_ms,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
            llm_provider=provider,
            llm_model=model,
            retry_count=0,
            validation_failures=[],
            pii_detected=False,
        )

        return AnalysisResponse(
            id=str(uuid.uuid4()),
            summary="Test summary",
            next_actions=["Test action"],
            created_at=datetime.now(UTC),
            transcript="Test transcript",
            observability=observability,
        )

    def test_analytics_with_multiple_analyses(self) -> None:
        """Test analytics aggregation with multiple analyses."""
        repository = InMemoryAnalysisRepository()

        # Create mock adapter and service
        mock_adapter = Mock()
        service = AnalysisService(
            llm_adapter=mock_adapter,
            repository=repository,
            pii_service=None,
            guardrails_service=None,
            enable_moderation=False,
        )

        # Add multiple analyses
        analyses = [
            self.create_mock_analysis("gpt-4o", "openai", 100, 50, 200.0),
            self.create_mock_analysis("gpt-4o", "openai", 150, 75, 250.0),
            self.create_mock_analysis("gpt-4o-mini", "openai", 200, 100, 180.0),
            self.create_mock_analysis("llama-3.3-70b-versatile", "groq", 120, 60, 150.0),
        ]

        for analysis in analyses:
            repository.save(analysis)

        # Get all analyses
        all_analyses = service.list_all()

        # Verify counts
        assert len(all_analyses) == 4

        # Verify token aggregation
        total_input = sum(a.observability.input_tokens for a in all_analyses if a.observability)
        total_output = sum(a.observability.output_tokens for a in all_analyses if a.observability)
        assert total_input == 570  # 100 + 150 + 200 + 120
        assert total_output == 285  # 50 + 75 + 100 + 60

        # Verify provider breakdown
        openai_count = sum(
            1 for a in all_analyses if a.observability and a.observability.llm_provider == "openai"
        )
        groq_count = sum(
            1 for a in all_analyses if a.observability and a.observability.llm_provider == "groq"
        )
        assert openai_count == 3
        assert groq_count == 1

    def test_analytics_with_evaluations(self) -> None:
        """Test analytics includes evaluation quality metrics."""
        repository = InMemoryAnalysisRepository()

        # Create analyses
        analysis1 = self.create_mock_analysis("gpt-4o", "openai", 100, 50, 200.0)
        analysis2 = self.create_mock_analysis("gpt-4o", "openai", 150, 75, 250.0)
        analysis3 = self.create_mock_analysis("gpt-4o-mini", "openai", 200, 100, 180.0)

        repository.save(analysis1)
        repository.save(analysis2)
        repository.save(analysis3)

        # Add evaluations
        eval1 = AnalysisEvaluation(
            id=str(uuid.uuid4()),
            analysis_id=analysis1.id,
            score=5,
            is_hallucination=False,
            comment="Excellent",
            evaluated_at=datetime.now(UTC),
        )
        eval2 = AnalysisEvaluation(
            id=str(uuid.uuid4()),
            analysis_id=analysis2.id,
            score=4,
            is_hallucination=False,
            comment="Very good",
            evaluated_at=datetime.now(UTC),
        )
        eval3 = AnalysisEvaluation(
            id=str(uuid.uuid4()),
            analysis_id=analysis3.id,
            score=2,
            is_hallucination=True,
            comment="Hallucinated info",
            evaluated_at=datetime.now(UTC),
        )

        repository.save_evaluation(eval1)
        repository.save_evaluation(eval2)
        repository.save_evaluation(eval3)

        # Get evaluations
        evaluations = repository.list_evaluations()

        # Verify counts
        assert len(evaluations) == 3

        # Verify average score
        avg_score = sum(e.score for e in evaluations) / len(evaluations)
        assert avg_score == pytest.approx(3.67, rel=0.01)  # (5 + 4 + 2) / 3

        # Verify hallucination rate
        hallucination_count = sum(1 for e in evaluations if e.is_hallucination)
        hallucination_rate = (hallucination_count / len(evaluations)) * 100
        assert hallucination_rate == pytest.approx(33.33, rel=0.01)  # 1/3 * 100

    def test_analytics_without_observability_data(self) -> None:
        """Test analytics handles analyses without observability."""
        repository = InMemoryAnalysisRepository()

        # Create analysis without observability (legacy data)
        legacy_analysis = AnalysisResponse(
            id=str(uuid.uuid4()),
            summary="Legacy summary",
            next_actions=["Legacy action"],
            created_at=datetime.now(UTC),
            transcript="Legacy transcript",
            observability=None,  # No observability data
        )

        repository.save(legacy_analysis)

        # Get all analyses
        all_analyses = repository.list_all()
        assert len(all_analyses) == 1

        # Filter for observability
        obs_analyses = [a for a in all_analyses if a.observability]
        assert len(obs_analyses) == 0  # No analyses with observability


class TestLatencyPercentiles:
    """Test latency percentile calculations."""

    def test_latency_percentiles_calculation(self) -> None:
        """Test p50, p95, p99 percentile calculations."""
        import statistics

        # Create latency data
        latencies = [100, 150, 200, 250, 300, 350, 400, 450, 500, 550]

        # Calculate percentiles
        sorted_latencies = sorted(latencies)
        p50 = statistics.median(sorted_latencies)
        p95 = statistics.quantiles(sorted_latencies, n=20)[18]
        p99 = statistics.quantiles(sorted_latencies, n=100)[98]

        # Verify calculations
        assert p50 == 325.0  # Median of 10 values (average of 300 and 350)
        assert p95 > p50  # 95th should be higher than median
        assert p99 > p95  # 99th should be higher than 95th
        # Note: p99 may be extrapolated beyond max with small sample sizes
