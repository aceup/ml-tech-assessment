"""
Integration tests for human-in-the-loop evaluation system.

Tests verify:
- Evaluation submission workflow
- Evaluation retrieval
- Repository storage (in-memory and Redis)
- Integration with analytics
"""

import pytest
import uuid
from datetime import UTC, datetime

from app.models.evaluation import AnalysisEvaluation, EvaluationRequest
from app.repositories.in_memory import InMemoryAnalysisRepository
from app.models.responses import AnalysisResponse


class TestEvaluationWorkflow:
    """Test evaluation submission and retrieval workflow."""

    def test_save_and_retrieve_evaluation(self) -> None:
        """Test saving and retrieving evaluations."""
        repository = InMemoryAnalysisRepository()

        # Create evaluation
        evaluation = AnalysisEvaluation(
            id=str(uuid.uuid4()),
            analysis_id="test-analysis-123",
            score=5,
            is_hallucination=False,
            comment="Excellent summary!",
            evaluated_at=datetime.now(UTC),
        )

        # Save
        saved = repository.save_evaluation(evaluation)

        # Verify saved successfully
        assert saved.id == evaluation.id
        assert saved.analysis_id == "test-analysis-123"

        # Retrieve
        retrieved = repository.get_evaluation("test-analysis-123")

        # Verify retrieval
        assert retrieved is not None
        assert retrieved.id == evaluation.id
        assert retrieved.score == 5
        assert retrieved.is_hallucination is False
        assert retrieved.comment == "Excellent summary!"

    def test_evaluation_per_analysis(self) -> None:
        """Test that only one evaluation exists per analysis."""
        repository = InMemoryAnalysisRepository()

        analysis_id = "test-analysis-456"

        # Create first evaluation
        eval1 = AnalysisEvaluation(
            id=str(uuid.uuid4()),
            analysis_id=analysis_id,
            score=3,
            is_hallucination=False,
            comment="First evaluation",
            evaluated_at=datetime.now(UTC),
        )
        repository.save_evaluation(eval1)

        # Create second evaluation for same analysis (should overwrite)
        eval2 = AnalysisEvaluation(
            id=str(uuid.uuid4()),
            analysis_id=analysis_id,
            score=5,
            is_hallucination=False,
            comment="Updated evaluation",
            evaluated_at=datetime.now(UTC),
        )
        repository.save_evaluation(eval2)

        # Retrieve - should get the latest one
        retrieved = repository.get_evaluation(analysis_id)

        assert retrieved is not None
        assert retrieved.id == eval2.id
        assert retrieved.score == 5
        assert retrieved.comment == "Updated evaluation"

    def test_list_all_evaluations(self) -> None:
        """Test listing all evaluations across analyses."""
        repository = InMemoryAnalysisRepository()

        # Create multiple evaluations
        evals = [
            AnalysisEvaluation(
                id=str(uuid.uuid4()),
                analysis_id=f"analysis-{i}",
                score=i,
                is_hallucination=False,
                comment=f"Evaluation {i}",
                evaluated_at=datetime.now(UTC),
            )
            for i in range(1, 6)
        ]

        for eval in evals:
            repository.save_evaluation(eval)

        # List all
        all_evals = repository.list_evaluations()

        # Verify count
        assert len(all_evals) == 5

        # Verify content
        scores = {e.score for e in all_evals}
        assert scores == {1, 2, 3, 4, 5}

    def test_get_nonexistent_evaluation_returns_none(self) -> None:
        """Test that retrieving non-existent evaluation returns None."""
        repository = InMemoryAnalysisRepository()

        result = repository.get_evaluation("nonexistent-analysis")

        assert result is None


class TestEvaluationValidation:
    """Test evaluation request validation."""

    def test_evaluation_request_with_valid_score(self) -> None:
        """Test valid evaluation request."""
        request = EvaluationRequest(
            score=4,
            is_hallucination=False,
            comment="Good analysis",
        )

        assert request.score == 4
        assert request.is_hallucination is False
        assert request.comment == "Good analysis"

    def test_evaluation_request_score_bounds(self) -> None:
        """Test score must be between 1 and 5."""
        from pydantic import ValidationError

        # Score too low
        with pytest.raises(ValidationError) as exc_info:
            EvaluationRequest(score=0, is_hallucination=False)
        assert "greater than or equal to 1" in str(exc_info.value)

        # Score too high
        with pytest.raises(ValidationError) as exc_info:
            EvaluationRequest(score=6, is_hallucination=False)
        assert "less than or equal to 5" in str(exc_info.value)

        # Valid boundaries
        EvaluationRequest(score=1, is_hallucination=False)  # Min valid
        EvaluationRequest(score=5, is_hallucination=False)  # Max valid

    def test_evaluation_request_with_optional_comment(self) -> None:
        """Test that comment is optional."""
        request = EvaluationRequest(
            score=3,
            is_hallucination=True,
            # comment omitted
        )

        assert request.score == 3
        assert request.is_hallucination is True
        assert request.comment is None

    def test_evaluation_request_comment_max_length(self) -> None:
        """Test comment has maximum length."""
        from pydantic import ValidationError

        # Valid long comment (1000 chars)
        long_comment = "a" * 1000
        request = EvaluationRequest(
            score=4,
            is_hallucination=False,
            comment=long_comment,
        )
        assert len(request.comment) == 1000

        # Too long comment (1001 chars)
        with pytest.raises(ValidationError) as exc_info:
            EvaluationRequest(
                score=4,
                is_hallucination=False,
                comment="a" * 1001,
            )
        assert "at most 1000 characters" in str(exc_info.value)


class TestHallucination Flags:
    """Test hallucination flagging functionality."""

    def test_flag_hallucination(self) -> None:
        """Test flagging analysis as hallucination."""
        repository = InMemoryAnalysisRepository()

        # Submit evaluation flagging hallucination
        evaluation = AnalysisEvaluation(
            id=str(uuid.uuid4()),
            analysis_id="analysis-with-hallucination",
            score=1,  # Low score because it hallucinated
            is_hallucination=True,
            comment="AI made up patient name not in transcript",
            evaluated_at=datetime.now(UTC),
        )

        repository.save_evaluation(evaluation)
        retrieved = repository.get_evaluation("analysis-with-hallucination")

        assert retrieved is not None
        assert retrieved.is_hallucination is True
        assert retrieved.score == 1
        assert "made up" in retrieved.comment

    def test_default_no_hallucination(self) -> None:
        """Test hallucination flag defaults to False."""
        request = EvaluationRequest(
            score=5,
            # is_hallucination omitted (defaults to False)
        )

        assert request.is_hallucination is False
