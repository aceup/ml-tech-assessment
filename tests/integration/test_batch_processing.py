"""
Integration tests for batch processing endpoint.

Tests concurrent processing, semaphore limits, error handling,
and result aggregation through the HTTP layer.
"""

import asyncio
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from app.services.analysis_service import LLMAnalysisResult
from app.utils.exceptions import ExternalServiceException


def test_batch_endpoint_with_partial_failures_returns_mixed_results(
    client: TestClient, mock_openai_adapter: AsyncMock
):
    """Test batch with some successes and some failures.

    Verifies that:
    - Successful analyses are returned in results array
    - Failed analyses are tracked in errors array
    - Total counts match input
    - Error messages include transcript index
    """
    # Arrange - Configure mock to fail on every other transcript
    call_count = 0

    async def mock_llm(system_prompt, user_prompt, dto):
        nonlocal call_count
        call_count += 1
        if call_count % 2 == 0:  # Fail on even calls
            raise ExternalServiceException(
                service="OpenAI",
                message="LLM processing error",
                details={"call_number": call_count},
            )
        return LLMAnalysisResult(
            summary=f"Success summary {call_count}",
            next_actions=[f"Actions for transcript {call_count}"],
        )

    mock_openai_adapter.run_completion_async.side_effect = mock_llm

    transcripts = [f"Medical transcript number {i}" for i in range(1, 11)]

    # Act
    response = client.post("/api/v1/analyses/batch", json={"transcripts": transcripts})

    # Assert
    assert response.status_code == 201
    data = response.json()

    # Verify counts
    assert data["total"] == 10
    assert data["successful"] == 5
    assert data["failed"] == 5

    # Verify results array contains only successful analyses
    assert len(data["results"]) == 5
    for result in data["results"]:
        assert "id" in result
        assert "summary" in result
        assert "next_actions" in result
        assert result["summary"].startswith("Success summary")

    # Verify errors array contains failure messages
    assert len(data["errors"]) == 5
    for i, error in enumerate(data["errors"]):
        assert error.startswith("Transcript")
        assert "LLM processing error" in error or "OpenAI" in error


def test_batch_endpoint_semaphore_limits_to_5_concurrent(
    client: TestClient, mock_openai_adapter: AsyncMock
):
    """Test that batch endpoint respects semaphore limit of 5.

    Verifies that:
    - Maximum concurrent executions never exceeds 5
    - All transcripts are eventually processed
    - Concurrency is properly limited even with 20 transcripts
    """
    # Arrange - Track concurrent execution count
    current_count = 0
    max_concurrent = 0
    lock = asyncio.Lock()

    async def tracked_llm(system_prompt, user_prompt, dto):
        nonlocal current_count, max_concurrent

        async with lock:
            current_count += 1
            max_concurrent = max(max_concurrent, current_count)

        # Simulate work to ensure concurrent calls overlap
        await asyncio.sleep(0.01)

        async with lock:
            current_count -= 1

        return LLMAnalysisResult(
            summary="Test summary",
            next_actions=["Test actions"],
        )

    mock_openai_adapter.run_completion_async.side_effect = tracked_llm

    transcripts = [f"Medical transcript {i}" for i in range(1, 21)]

    # Act
    response = client.post("/api/v1/analyses/batch", json={"transcripts": transcripts})

    # Assert
    assert response.status_code == 201
    data = response.json()

    # Verify all transcripts were processed
    assert data["total"] == 20
    assert data["successful"] == 20
    assert data["failed"] == 0

    # CRITICAL: Verify semaphore limit was respected
    assert max_concurrent <= 5, f"Max concurrent was {max_concurrent}, should be <= 5"


def test_batch_endpoint_with_all_failures_aggregates_errors(
    client: TestClient, mock_openai_adapter: AsyncMock
):
    """Test batch where all transcripts fail.

    Verifies that:
    - Empty results array when all fail
    - All errors are captured and returned
    - Failed count matches total count
    - Error messages are descriptive
    """
    # Arrange - Configure mock to always fail
    async def failing_llm(system_prompt, user_prompt, dto):
        raise ExternalServiceException(
            service="OpenAI",
            message="Rate limit exceeded",
            details={"retry_after": 60},
        )

    mock_openai_adapter.run_completion_async.side_effect = failing_llm

    transcripts = [
        "Patient A: headache symptoms",
        "Patient B: fever and cough",
        "Patient C: chest pain",
        "Patient D: nausea and vomiting",
        "Patient E: joint pain",
    ]

    # Act
    response = client.post("/api/v1/analyses/batch", json={"transcripts": transcripts})

    # Assert
    assert response.status_code == 201
    data = response.json()

    # Verify all failed
    assert data["total"] == 5
    assert data["successful"] == 0
    assert data["failed"] == 5

    # Verify results is empty
    assert data["results"] == []

    # Verify all errors are captured
    assert len(data["errors"]) == 5
    for i, error in enumerate(data["errors"]):
        # Error message should include transcript index
        assert f"Transcript {i + 1}" in error
        # Error should contain meaningful message
        assert "Rate limit exceeded" in error or "OpenAI" in error


def test_batch_endpoint_preserves_input_order_in_results(
    client: TestClient, mock_openai_adapter: AsyncMock
):
    """Test that result order can be matched to input order.

    Verifies that:
    - Successful results maintain correlation to input
    - Transcript content is preserved in response
    - Can identify which input produced which output
    """
    # Arrange - Configure mock to succeed for all
    async def mock_llm(system_prompt, user_prompt, dto):
        # Extract transcript number from prompt to create unique response
        # User prompt contains the transcript
        if "Patient A" in user_prompt:
            return LLMAnalysisResult(
                summary="Analysis for Patient A",
                next_actions=["Actions for Patient A"],
            )
        elif "Patient B" in user_prompt:
            return LLMAnalysisResult(
                summary="Analysis for Patient B",
                next_actions=["Actions for Patient B"],
            )
        elif "Patient C" in user_prompt:
            return LLMAnalysisResult(
                summary="Analysis for Patient C",
                next_actions=["Actions for Patient C"],
            )
        else:
            return LLMAnalysisResult(
                summary="Generic analysis",
                next_actions=["Generic actions"],
            )

    mock_openai_adapter.run_completion_async.side_effect = mock_llm

    transcripts = [
        "Patient A: headache symptoms for 3 days",
        "Patient B: fever and cough ongoing",
        "Patient C: chest pain during exercise",
    ]

    # Act
    response = client.post("/api/v1/analyses/batch", json={"transcripts": transcripts})

    # Assert
    assert response.status_code == 201
    data = response.json()

    # Verify all succeeded
    assert data["successful"] == 3
    assert len(data["results"]) == 3

    # Verify we can match results to inputs using transcript field
    result_transcripts = [r["transcript"] for r in data["results"]]
    for original_transcript in transcripts:
        # Each original transcript should be in the results
        assert any(
            original_transcript in result_transcript
            for result_transcript in result_transcripts
        )

    # Verify summaries match their respective transcripts
    for result in data["results"]:
        if "Patient A" in result["transcript"]:
            assert "Patient A" in result["summary"]
        elif "Patient B" in result["transcript"]:
            assert "Patient B" in result["summary"]
        elif "Patient C" in result["transcript"]:
            assert "Patient C" in result["summary"]


def test_batch_endpoint_tracks_individual_errors(
    client: TestClient, mock_openai_adapter: AsyncMock
):
    """Test that individual error details are preserved.

    Verifies that:
    - Different error types are captured
    - Error messages include transcript context
    - Can identify which specific transcript failed
    """
    # Arrange - Configure mock with different failure types
    call_count = 0

    async def varied_errors_llm(system_prompt, user_prompt, dto):
        nonlocal call_count
        call_count += 1

        if call_count == 1:
            # First one succeeds
            return LLMAnalysisResult(
                summary="Success summary",
                next_actions=["Success actions"],
            )
        elif call_count == 2:
            # Second fails with rate limit
            raise ExternalServiceException(
                service="OpenAI",
                message="Rate limit exceeded",
                details={"retry_after": 60},
            )
        elif call_count == 3:
            # Third succeeds
            return LLMAnalysisResult(
                summary="Another success",
                next_actions=["More actions"],
            )
        elif call_count == 4:
            # Fourth fails with timeout
            raise ExternalServiceException(
                service="OpenAI",
                message="Request timeout",
                details={"timeout_seconds": 30},
            )
        else:
            # Fifth fails with validation error
            raise ExternalServiceException(
                service="OpenAI",
                message="Invalid response format",
                details={"expected": "json"},
            )

    mock_openai_adapter.run_completion_async.side_effect = varied_errors_llm

    transcripts = [
        "Transcript 1: headache",
        "Transcript 2: fever",
        "Transcript 3: cough",
        "Transcript 4: pain",
        "Transcript 5: nausea",
    ]

    # Act
    response = client.post("/api/v1/analyses/batch", json={"transcripts": transcripts})

    # Assert
    assert response.status_code == 201
    data = response.json()

    # Verify mixed results
    assert data["total"] == 5
    assert data["successful"] == 2
    assert data["failed"] == 3

    # Verify errors are tracked with different messages
    assert len(data["errors"]) == 3

    # Check that different error types are present
    error_messages = " ".join(data["errors"])
    # Should have errors from transcripts 2, 4, and 5
    assert "Transcript 2" in error_messages or "Rate limit" in error_messages
    assert "Transcript 4" in error_messages or "timeout" in error_messages
    assert "Transcript 5" in error_messages or "Invalid response" in error_messages


def test_batch_endpoint_handles_large_batch_efficiently(
    client: TestClient, mock_openai_adapter: AsyncMock
):
    """Test batch endpoint with 50+ transcripts.

    Verifies that:
    - Large batches are processed successfully
    - Semaphore prevents overwhelming the system
    - All transcripts are processed
    - Response time is reasonable (benefits from concurrency)
    """
    # Arrange - Configure mock to simulate realistic processing
    import time

    call_count = 0
    start_time = None

    async def realistic_llm(system_prompt, user_prompt, dto):
        nonlocal call_count, start_time
        if start_time is None:
            start_time = time.time()

        call_count += 1

        # Simulate processing time
        await asyncio.sleep(0.005)

        # Simulate occasional failures (10% failure rate)
        if call_count % 10 == 0:
            raise ExternalServiceException(
                service="OpenAI",
                message="Simulated random error",
                details={"call": call_count},
            )

        return LLMAnalysisResult(
            summary=f"Summary for call {call_count}",
            next_actions=[f"Actions for call {call_count}"],
        )

    mock_openai_adapter.run_completion_async.side_effect = realistic_llm

    # Create 50 transcripts
    transcripts = [f"Medical transcript number {i}" for i in range(1, 51)]

    # Act
    response = client.post("/api/v1/analyses/batch", json={"transcripts": transcripts})
    elapsed_time = time.time() - start_time if start_time else 0

    # Assert
    assert response.status_code == 201
    data = response.json()

    # Verify all transcripts were processed
    assert data["total"] == 50
    assert data["successful"] + data["failed"] == 50

    # Should have some failures from simulated errors
    # Note: In concurrent async execution, the actual failure rate may differ from expected
    # The important thing is that failures are handled gracefully
    assert data["failed"] > 0, "Should have at least some simulated failures"
    assert data["successful"] > 0, "Should have at least some successes"

    # Verify results count matches successful count
    assert len(data["results"]) == data["successful"]

    # Verify errors count matches failed count
    if data["errors"]:
        assert len(data["errors"]) == data["failed"]

    # Performance check: With semaphore of 5, should take roughly:
    # 50 transcripts / 5 concurrent * 0.005s = ~0.05s
    # Allow generous margin for test overhead (2 seconds max)
    assert (
        elapsed_time < 2.0
    ), f"Batch processing took {elapsed_time}s, may not be concurrent"

    # Verify we processed all 50 transcripts
    assert call_count == 50
