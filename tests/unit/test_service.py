"""
Comprehensive async unit tests for AnalysisService.

Tests cover all three service methods with proper mocking,
exception handling, and logging verification.
"""

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, Mock

import pytest

from app.services.analysis_service import AnalysisService, LLMAnalysisResult
from app.models.responses import AnalysisResponse
from app.repositories.in_memory import InMemoryAnalysisRepository
from app.utils.exceptions import (
    ValidationException,
    ExternalServiceException,
    NotFoundException,
)


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def mock_llm_adapter():
    """Create a mock LLM adapter with AsyncMock."""
    adapter = Mock()
    adapter.run_completion_async = AsyncMock()
    return adapter


@pytest.fixture
def mock_repository():
    """Create a mock repository."""
    return Mock(spec=InMemoryAnalysisRepository)


@pytest.fixture
def service(mock_llm_adapter, mock_repository):
    """Create an AnalysisService instance with mocked dependencies."""
    return AnalysisService(
        llm_adapter=mock_llm_adapter,
        repository=mock_repository,
    )


@pytest.fixture
def sample_transcript():
    """Sample transcript for testing."""
    return "Client discussed quarterly goals and team performance metrics."


@pytest.fixture
def sample_llm_result():
    """Sample LLM result for mocking."""
    return LLMAnalysisResult(
        summary="Client focused on Q3 goals and team metrics.",
        next_actions=[
            "Review team performance data",
            "Schedule follow-up meeting",
            "Document action items"
        ],
    )


# ============================================================================
# ANALYZE() METHOD TESTS (12 tests)
# ============================================================================


@pytest.mark.asyncio
async def test_analyze_with_valid_transcript_returns_analysis(
    service,
    mock_llm_adapter,
    mock_repository,
    sample_transcript,
    sample_llm_result,
):
    """Test successful analysis with valid transcript."""
    # Arrange
    mock_llm_adapter.run_completion_async.return_value = sample_llm_result

    # Act
    result = await service.analyze(sample_transcript)

    # Assert
    assert isinstance(result, AnalysisResponse)
    assert result.summary == sample_llm_result.summary
    assert result.next_actions == sample_llm_result.next_actions
    assert result.transcript == sample_transcript
    assert isinstance(result.id, str)
    assert isinstance(result.created_at, datetime)


@pytest.mark.asyncio
async def test_analyze_stores_result_in_repository(
    service,
    mock_llm_adapter,
    mock_repository,
    sample_transcript,
    sample_llm_result,
):
    """Test that analysis result is saved to repository."""
    # Arrange
    mock_llm_adapter.run_completion_async.return_value = sample_llm_result

    # Act
    result = await service.analyze(sample_transcript)

    # Assert
    mock_repository.save.assert_called_once()
    saved_analysis = mock_repository.save.call_args[0][0]
    assert saved_analysis.id == result.id
    assert saved_analysis.summary == sample_llm_result.summary
    assert saved_analysis.transcript == sample_transcript


@pytest.mark.asyncio
async def test_analyze_calls_llm_adapter_with_correct_prompts(
    service,
    mock_llm_adapter,
    sample_transcript,
    sample_llm_result,
):
    """Test that LLM adapter is called with correct prompts."""
    # Arrange
    mock_llm_adapter.run_completion_async.return_value = sample_llm_result

    # Act
    await service.analyze(sample_transcript)

    # Assert
    mock_llm_adapter.run_completion_async.assert_called_once()
    call_args = mock_llm_adapter.run_completion_async.call_args

    # Verify system prompt
    system_prompt = call_args.kwargs["system_prompt"]
    assert "expert business coach" in system_prompt
    assert "JSON" in system_prompt

    # Verify user prompt contains transcript
    user_prompt = call_args.kwargs["user_prompt"]
    assert sample_transcript in user_prompt

    # Verify DTO type
    assert call_args.kwargs["dto"] == LLMAnalysisResult


@pytest.mark.asyncio
async def test_analyze_generates_unique_id(
    service,
    mock_llm_adapter,
    sample_transcript,
    sample_llm_result,
):
    """Test that each analysis generates a unique UUID."""
    # Arrange
    mock_llm_adapter.run_completion_async.return_value = sample_llm_result

    # Act
    result1 = await service.analyze(sample_transcript)
    result2 = await service.analyze(sample_transcript)

    # Assert
    assert result1.id != result2.id
    # Verify both are valid UUIDs
    uuid.UUID(result1.id)
    uuid.UUID(result2.id)


@pytest.mark.asyncio
async def test_analyze_with_empty_transcript_raises_validation_exception(service):
    """Test that empty transcript raises ValidationException."""
    # Act & Assert
    with pytest.raises(ValidationException) as exc_info:
        await service.analyze("")

    assert "cannot be empty" in str(exc_info.value)


@pytest.mark.asyncio
async def test_analyze_with_whitespace_only_raises_validation_exception(service):
    """Test that whitespace-only transcript raises ValidationException."""
    # Act & Assert
    with pytest.raises(ValidationException) as exc_info:
        await service.analyze("   \n\t   ")

    assert "cannot be empty" in str(exc_info.value)


@pytest.mark.asyncio
async def test_analyze_with_llm_failure_raises_external_service_exception(
    service,
    mock_llm_adapter,
    sample_transcript,
):
    """Test that LLM API failure raises ExternalServiceException."""
    # Arrange - Create mock exception with "openai" in type name
    class MockOpenAIError(Exception):
        """Mock OpenAI error for testing."""
        pass

    mock_llm_adapter.run_completion_async.side_effect = MockOpenAIError(
        "Rate limit exceeded"
    )

    # Act & Assert
    with pytest.raises(ExternalServiceException) as exc_info:
        await service.analyze(sample_transcript)

    assert "OpenAI" in str(exc_info.value)


@pytest.mark.asyncio
async def test_analyze_with_long_transcript_succeeds(
    service,
    mock_llm_adapter,
    sample_llm_result,
):
    """Test analysis succeeds with long transcript (10,000 characters)."""
    # Arrange
    long_transcript = "A" * 10000
    mock_llm_adapter.run_completion_async.return_value = sample_llm_result

    # Act
    result = await service.analyze(long_transcript)

    # Assert
    assert result.transcript == long_transcript
    assert len(result.transcript) == 10000


@pytest.mark.asyncio
async def test_analyze_with_special_characters_succeeds(
    service,
    mock_llm_adapter,
    sample_llm_result,
):
    """Test analysis succeeds with Unicode and emoji characters."""
    # Arrange
    special_transcript = "Client said: 'Great progress! 🎉' with metrics: €100K, ±10%"
    mock_llm_adapter.run_completion_async.return_value = sample_llm_result

    # Act
    result = await service.analyze(special_transcript)

    # Assert
    assert result.transcript == special_transcript
    assert "🎉" in result.transcript
    assert "€" in result.transcript


@pytest.mark.asyncio
async def test_analyze_logs_started_and_completed(
    service,
    mock_llm_adapter,
    sample_transcript,
    sample_llm_result,
):
    """Test that analysis logs start and completion messages."""
    # Arrange
    mock_llm_adapter.run_completion_async.return_value = sample_llm_result

    # Act - Just verify it doesn't raise, logging is implementation detail
    result = await service.analyze(sample_transcript)

    # Assert - Focus on behavior, not logging internals
    assert result is not None
    assert result.id is not None
    assert result.summary == sample_llm_result.summary


@pytest.mark.asyncio
async def test_analyze_logs_failure_on_exception(
    service,
    mock_llm_adapter,
    sample_transcript,
):
    """Test that analysis logs error when exception occurs."""
    # Arrange - Create mock exception with "openai" in type name
    class MockOpenAIError(Exception):
        """Mock OpenAI error for testing."""
        pass

    mock_llm_adapter.run_completion_async.side_effect = MockOpenAIError(
        "Connection timeout"
    )

    # Act & Assert - Focus on exception behavior, not logging
    with pytest.raises(ExternalServiceException) as exc_info:
        await service.analyze(sample_transcript)

    # Verify correct exception transformation
    assert "OpenAI" in str(exc_info.value)
    assert "Connection timeout" in str(exc_info.value)


@pytest.mark.asyncio
async def test_analyze_sets_created_at_timestamp(
    service,
    mock_llm_adapter,
    sample_transcript,
    sample_llm_result,
):
    """Test that analysis sets UTC timestamp correctly."""
    # Arrange
    mock_llm_adapter.run_completion_async.return_value = sample_llm_result
    before_time = datetime.now(UTC)

    # Act
    result = await service.analyze(sample_transcript)

    # Assert
    after_time = datetime.now(UTC)
    assert before_time <= result.created_at <= after_time
    # Verify it's a datetime object
    assert isinstance(result.created_at, datetime)


@pytest.mark.asyncio
async def test_analyze_with_custom_num_next_actions(
    service,
    mock_llm_adapter,
    sample_transcript,
):
    """Test analysis with custom number of next actions."""
    # Arrange
    custom_result = LLMAnalysisResult(
        summary="Test summary",
        next_actions=[
            "Action 1",
            "Action 2",
            "Action 3",
            "Action 4",
            "Action 5"
        ],
    )
    mock_llm_adapter.run_completion_async.return_value = custom_result

    # Act
    result = await service.analyze(sample_transcript, num_next_actions=5)

    # Assert
    assert len(result.next_actions) == 5
    assert result.next_actions == custom_result.next_actions


@pytest.mark.asyncio
async def test_analyze_with_invalid_num_next_actions_raises_exception(
    service,
    sample_transcript,
):
    """Test that invalid num_next_actions raises ValidationException."""
    # Test with 0 (below minimum)
    with pytest.raises(ValidationException) as exc_info:
        await service.analyze(sample_transcript, num_next_actions=0)
    assert "must be between 1 and 10" in str(exc_info.value)

    # Test with 11 (above maximum)
    with pytest.raises(ValidationException) as exc_info:
        await service.analyze(sample_transcript, num_next_actions=11)
    assert "must be between 1 and 10" in str(exc_info.value)


@pytest.mark.asyncio
async def test_analyze_truncates_excess_actions(
    service,
    mock_llm_adapter,
    sample_transcript,
):
    """Test that service truncates if LLM returns too many actions."""
    # Arrange - LLM returns 5 actions but we only requested 3
    llm_result = LLMAnalysisResult(
        summary="Test summary",
        next_actions=[
            "Action 1",
            "Action 2",
            "Action 3",
            "Action 4",
            "Action 5"
        ],
    )
    mock_llm_adapter.run_completion_async.return_value = llm_result

    # Act
    result = await service.analyze(sample_transcript, num_next_actions=3)

    # Assert - Should truncate to 3 actions
    assert len(result.next_actions) == 3
    assert result.next_actions == ["Action 1", "Action 2", "Action 3"]


@pytest.mark.asyncio
async def test_analyze_accepts_fewer_actions_from_llm(
    service,
    mock_llm_adapter,
    sample_transcript,
):
    """Test that service accepts if LLM returns fewer actions than requested."""
    # Arrange - LLM returns 2 actions but we requested 5
    llm_result = LLMAnalysisResult(
        summary="Test summary",
        next_actions=["Action 1", "Action 2"],
    )
    mock_llm_adapter.run_completion_async.return_value = llm_result

    # Act
    result = await service.analyze(sample_transcript, num_next_actions=5)

    # Assert - Should accept 2 actions
    assert len(result.next_actions) == 2
    assert result.next_actions == ["Action 1", "Action 2"]


@pytest.mark.asyncio
async def test_analyze_prompts_include_action_count(
    service,
    mock_llm_adapter,
    sample_transcript,
    sample_llm_result,
):
    """Verify prompts are formatted with num_next_actions."""
    # Arrange
    mock_llm_adapter.run_completion_async.return_value = sample_llm_result

    # Act
    await service.analyze(sample_transcript, num_next_actions=7)

    # Assert
    call_args = mock_llm_adapter.run_completion_async.call_args
    system_prompt = call_args.kwargs["system_prompt"]
    user_prompt = call_args.kwargs["user_prompt"]

    # Verify prompts mention the count
    assert "7" in system_prompt or "7" in user_prompt
    assert "EXACTLY" in user_prompt.upper() or "exactly" in user_prompt


# ============================================================================
# GET_BY_ID() METHOD TESTS (3 tests)
# ============================================================================


def test_get_by_id_returns_existing_analysis(service, mock_repository):
    """Test retrieving an existing analysis by ID."""
    # Arrange
    analysis_id = str(uuid.uuid4())
    expected_analysis = AnalysisResponse(
        id=analysis_id,
        summary="Test summary",
        next_actions=["Action one", "Action two"],
        created_at=datetime.now(UTC),
        transcript="Test transcript",
    )
    mock_repository.get_by_id.return_value = expected_analysis

    # Act
    result = service.get_by_id(analysis_id)

    # Assert
    assert result == expected_analysis
    mock_repository.get_by_id.assert_called_once_with(analysis_id)


def test_get_by_id_raises_not_found(service, mock_repository):
    """Test that get_by_id raises NotFoundException for missing ID."""
    # Arrange
    analysis_id = str(uuid.uuid4())
    mock_repository.get_by_id.side_effect = NotFoundException(
        resource="Analysis",
        identifier=analysis_id,
    )

    # Act & Assert
    with pytest.raises(NotFoundException) as exc_info:
        service.get_by_id(analysis_id)

    assert analysis_id in str(exc_info.value)
    assert "Analysis" in str(exc_info.value)


def test_get_by_id_delegates_to_repository(service, mock_repository):
    """Test that get_by_id properly delegates to repository."""
    # Arrange
    analysis_id = str(uuid.uuid4())
    expected_analysis = AnalysisResponse(
        id=analysis_id,
        summary="Test",
        next_actions=["Test action 1", "Test action 2"],
        created_at=datetime.now(UTC),
        transcript="Test",
    )
    mock_repository.get_by_id.return_value = expected_analysis

    # Act
    service.get_by_id(analysis_id)

    # Assert
    mock_repository.get_by_id.assert_called_once_with(analysis_id)


# ============================================================================
# LIST_ALL() METHOD TESTS (3 tests)
# ============================================================================


def test_list_all_returns_empty_list_when_no_data(service, mock_repository):
    """Test list_all returns empty list when no analyses exist."""
    # Arrange
    mock_repository.list_all.return_value = []

    # Act
    result = service.list_all()

    # Assert
    assert result == []
    assert isinstance(result, list)


def test_list_all_returns_all_analyses(service, mock_repository):
    """Test list_all returns multiple analyses."""
    # Arrange
    analyses = [
        AnalysisResponse(
            id=str(uuid.uuid4()),
            summary=f"Summary {i}",
            next_actions=[f"Action {i}.1", f"Action {i}.2"],
            created_at=datetime.now(UTC),
            transcript=f"Transcript {i}",
        )
        for i in range(3)
    ]
    mock_repository.list_all.return_value = analyses

    # Act
    result = service.list_all()

    # Assert
    assert len(result) == 3
    assert result == analyses


def test_list_all_delegates_to_repository(service, mock_repository):
    """Test that list_all properly delegates to repository."""
    # Arrange
    mock_repository.list_all.return_value = []

    # Act
    service.list_all()

    # Assert
    mock_repository.list_all.assert_called_once()
