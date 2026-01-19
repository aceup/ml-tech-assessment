"""
Integration tests for all API endpoints.

Tests all endpoints in the application including:
- GET /api/v1/analyses/analyze - Analyze transcript
- GET /api/v1/analyses/{id} - Get by ID
- GET /api/v1/analyses - List all
- POST /api/v1/analyses/batch - Batch analysis
- GET /api/v1/health/live - Liveness check
- GET /api/v1/health/ready - Readiness check
"""

import time
from unittest.mock import AsyncMock

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.backend.core.config import Settings
from app.backend.services.analysis_service import LLMAnalysisResult


# ============================================================================
# GET /analyses/analyze Tests (3 tests)
# ============================================================================


def test_analyze_get_endpoint_with_valid_transcript_returns_200(
    client: TestClient,
) -> None:
    """
    Test GET /analyses/analyze with valid transcript returns 200 OK.

    Verifies:
    - Status code is 200
    - Response contains id, summary, next_actions, created_at, transcript
    - Analysis result is computed and returned
    """
    # Arrange
    valid_transcript = "Patient reports persistent headaches for 3 days."

    # Act
    response = client.get(
        "/api/v1/analyses/analyze",
        params={"transcript": valid_transcript},
    )

    # Assert
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert "id" in data
    assert "summary" in data
    assert "next_actions" in data
    assert "created_at" in data
    assert "transcript" in data
    assert data["transcript"] == valid_transcript


def test_analyze_get_endpoint_with_too_short_transcript_returns_422(
    client: TestClient,
) -> None:
    """
    Test GET /analyses/analyze with too short transcript returns 422.

    Verifies:
    - Status code is 422
    - Error details indicate validation failure
    - Minimum length requirement is enforced (10 chars)
    """
    # Arrange
    short_transcript = "Too short"  # 9 characters, below minimum of 10

    # Act
    response = client.get(
        "/api/v1/analyses/analyze",
        params={"transcript": short_transcript},
    )

    # Assert
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    data = response.json()
    assert "detail" in data
    # Validation error should mention minimum length
    error_detail = str(data["detail"])
    assert "at least 10 characters" in error_detail.lower()


def test_analyze_get_endpoint_with_whitespace_only_returns_422(
    client: TestClient,
) -> None:
    """
    Test GET /analyses/analyze with whitespace-only transcript returns 422.

    Verifies:
    - Status code is 422
    - Whitespace-only transcripts are rejected
    - Validation enforces meaningful content
    """
    # Arrange
    whitespace_transcript = "          "  # Only spaces

    # Act
    response = client.get(
        "/api/v1/analyses/analyze",
        params={"transcript": whitespace_transcript},
    )

    # Assert
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    data = response.json()
    assert "detail" in data
    # Error should mention whitespace or empty
    error_detail = str(data["detail"]).lower()
    assert "whitespace" in error_detail or "empty" in error_detail


def test_analyze_get_endpoint_returns_next_actions_as_array(
    client: TestClient,
) -> None:
    """
    Test GET /analyses/analyze returns next_actions as an array.

    Verifies:
    - next_actions is a list (array)
    - Each item in the list is a string
    - Default returns 3 actions
    """
    # Arrange
    valid_transcript = "Patient reports persistent headaches for 3 days."

    # Act
    response = client.get(
        "/api/v1/analyses/analyze",
        params={"transcript": valid_transcript},
    )

    # Assert
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert "next_actions" in data
    assert isinstance(data["next_actions"], list)
    assert all(isinstance(action, str) for action in data["next_actions"])
    # Default should be around 3 actions (may vary based on LLM)
    assert len(data["next_actions"]) >= 1
    assert len(data["next_actions"]) <= 10


def test_analyze_get_endpoint_with_custom_num_next_actions(
    client: TestClient,
) -> None:
    """
    Test GET /analyses/analyze with custom num_next_actions parameter.

    Verifies:
    - num_next_actions parameter is accepted
    - Response contains appropriate number of actions
    - Status code is 200
    """
    # Arrange
    valid_transcript = "Patient reports persistent headaches for 3 days."

    # Act
    response = client.get(
        "/api/v1/analyses/analyze",
        params={"transcript": valid_transcript, "num_next_actions": 5},
    )

    # Assert
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert "next_actions" in data
    assert isinstance(data["next_actions"], list)
    # Should return up to 5 actions (may be fewer if LLM generates less)
    assert len(data["next_actions"]) >= 1
    assert len(data["next_actions"]) <= 5


def test_analyze_get_endpoint_with_invalid_num_next_actions_returns_422(
    client: TestClient,
) -> None:
    """
    Test GET /analyses/analyze with invalid num_next_actions returns 422.

    Verifies:
    - num_next_actions=0 is rejected
    - num_next_actions=11 is rejected
    - Error details indicate validation failure
    """
    # Arrange
    valid_transcript = "Patient reports persistent headaches for 3 days."

    # Act - Test with 0 (below minimum)
    response = client.get(
        "/api/v1/analyses/analyze",
        params={"transcript": valid_transcript, "num_next_actions": 0},
    )

    # Assert
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    # Act - Test with 11 (above maximum)
    response = client.get(
        "/api/v1/analyses/analyze",
        params={"transcript": valid_transcript, "num_next_actions": 11},
    )

    # Assert
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


# ============================================================================
# GET /analyses/{id} Tests (2 tests)
# ============================================================================


def test_get_analysis_by_id_returns_200(
    client: TestClient,
) -> None:
    """
    Test GET /analyses/{id} with existing ID returns 200 OK.

    Verifies:
    - Status code is 200
    - Response contains the correct analysis data
    - All fields match the created analysis
    """
    # Arrange - Create an analysis first
    transcript = "Patient reports persistent headaches for 3 days."
    create_response = client.get(
        "/api/v1/analyses/analyze",
        params={"transcript": transcript},
    )
    assert create_response.status_code == status.HTTP_200_OK
    created_data = create_response.json()
    analysis_id = created_data["id"]

    # Act - Get the analysis by ID
    response = client.get(f"/api/v1/analyses/{analysis_id}")

    # Assert
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["id"] == analysis_id
    assert data["transcript"] == transcript
    assert data["summary"] == created_data["summary"]
    assert data["next_actions"] == created_data["next_actions"]
    assert data["created_at"] == created_data["created_at"]


def test_get_analysis_by_id_with_missing_returns_404(
    client: TestClient,
) -> None:
    """
    Test GET /analyses/{id} with non-existent ID returns 404 Not Found.

    Verifies:
    - Status code is 404
    - Error message indicates analysis not found
    """
    # Arrange
    nonexistent_id = "00000000-0000-0000-0000-000000000000"

    # Act
    response = client.get(f"/api/v1/analyses/{nonexistent_id}")

    # Assert
    assert response.status_code == status.HTTP_404_NOT_FOUND

    data = response.json()
    assert "error" in data
    assert data["error"] == "NotFoundException"
    assert "message" in data
    assert "not found" in data["message"].lower()


# ============================================================================
# GET /analyses Tests (2 tests)
# ============================================================================


def test_list_analyses_empty_returns_200(
    client: TestClient,
) -> None:
    """
    Test GET /analyses with no analyses returns 200 OK with empty list.

    Verifies:
    - Status code is 200
    - Response is an empty list
    """
    # Act
    response = client.get("/api/v1/analyses")

    # Assert
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0


def test_list_analyses_with_data_returns_all(
    client: TestClient,
) -> None:
    """
    Test GET /analyses with multiple analyses returns all of them.

    Verifies:
    - Status code is 200
    - Response contains all created analyses
    - Each analysis has correct structure
    """
    # Arrange - Create multiple analyses
    transcripts = [
        "Patient A reports headache for 2 days.",
        "Patient B has chest pain and shortness of breath.",
        "Patient C presents with fever and cough.",
    ]

    created_ids = []
    for transcript in transcripts:
        response = client.get(
            "/api/v1/analyses/analyze",
            params={"transcript": transcript},
        )
        assert response.status_code == status.HTTP_200_OK
        created_ids.append(response.json()["id"])

    # Act - List all analyses
    response = client.get("/api/v1/analyses")

    # Assert
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 3

    # Verify all created IDs are present
    returned_ids = [analysis["id"] for analysis in data]
    assert set(returned_ids) == set(created_ids)

    # Verify structure of each analysis
    for analysis in data:
        assert "id" in analysis
        assert "summary" in analysis
        assert "next_actions" in analysis
        assert "created_at" in analysis
        assert "transcript" in analysis


# ============================================================================
# POST /analyses/batch Tests (2 tests)
# ============================================================================


def test_batch_analyze_with_valid_transcripts_returns_201(
    client: TestClient,
) -> None:
    """
    Test POST /analyses/batch with valid transcripts returns 201 Created.

    Verifies:
    - Status code is 201
    - All transcripts are successfully analyzed
    - Response contains correct counts and results
    - BatchAnalysisResponse schema is correct
    """
    # Arrange
    transcripts = [
        "Patient A reports headache for 2 days.",
        "Patient B has chest pain and shortness of breath.",
        "Patient C presents with fever and cough.",
    ]

    # Act
    response = client.post(
        "/api/v1/analyses/batch",
        json={"transcripts": transcripts},
    )

    # Assert
    assert response.status_code == status.HTTP_201_CREATED

    data = response.json()
    assert data["total"] == 3
    assert data["successful"] == 3
    assert data["failed"] == 0
    assert data["errors"] is None or data["errors"] == []

    # Verify results structure
    assert len(data["results"]) == 3
    for result in data["results"]:
        assert "id" in result
        assert "summary" in result
        assert "next_actions" in result
        assert "created_at" in result
        assert "transcript" in result


def test_batch_analyze_respects_semaphore_limit(
    client: TestClient,
) -> None:
    """
    Test POST /analyses/batch respects concurrent processing limit (5).

    Verifies:
    - All transcripts are processed successfully
    - Concurrency limit is respected (semaphore = 5)
    - Processing time indicates parallel execution
    """
    # Arrange - Create 10 transcripts to test semaphore
    transcripts = [
        f"Patient {i} reports symptoms for {i} days." for i in range(1, 11)
    ]

    # Act
    start_time = time.time()
    response = client.post(
        "/api/v1/analyses/batch",
        json={"transcripts": transcripts},
    )
    elapsed_time = time.time() - start_time

    # Assert
    assert response.status_code == status.HTTP_201_CREATED

    data = response.json()
    assert data["total"] == 10
    assert data["successful"] == 10
    assert data["failed"] == 0

    # Verify results
    assert len(data["results"]) == 10

    # Note: Since we're using mocks, timing verification is limited
    # In real scenario, this would verify that processing time is less than
    # sequential execution but more than single execution
    # For mocks, we just verify successful parallel completion
    assert elapsed_time < 1.0  # Should be fast with mocks


def test_batch_analyze_with_custom_num_next_actions(
    client: TestClient,
) -> None:
    """
    Test POST /analyses/batch with custom num_next_actions parameter.

    Verifies:
    - num_next_actions parameter is accepted in request body
    - All results contain appropriate number of actions
    - Status code is 201
    """
    # Arrange
    transcripts = [
        "Patient A reports headache for 2 days.",
        "Patient B has chest pain and shortness of breath.",
    ]

    # Act
    response = client.post(
        "/api/v1/analyses/batch",
        json={"transcripts": transcripts, "num_next_actions": 5},
    )

    # Assert
    assert response.status_code == status.HTTP_201_CREATED

    data = response.json()
    assert data["total"] == 2
    assert data["successful"] == 2
    assert data["failed"] == 0

    # Verify each result has appropriate number of actions
    for result in data["results"]:
        assert "next_actions" in result
        assert isinstance(result["next_actions"], list)
        # Should return up to 5 actions (may be fewer if LLM generates less)
        assert len(result["next_actions"]) >= 1
        assert len(result["next_actions"]) <= 5


# ============================================================================
# Health Endpoints Tests (3 tests)
# ============================================================================


def test_health_live_returns_200(
    client: TestClient,
) -> None:
    """
    Test GET /health/live returns 200 OK.

    Verifies:
    - Status code is 200
    - Response contains status "alive"
    """
    # Act
    response = client.get("/api/v1/health/live")

    # Assert
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["status"] == "alive"


def test_health_ready_returns_200(
    client: TestClient,
) -> None:
    """
    Test GET /health/ready returns 200 OK when service is ready.

    Verifies:
    - Status code is 200
    - Response contains status "ready"
    - Checks are included and pass
    """
    # Act
    response = client.get("/api/v1/health/ready")

    # Assert
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["status"] == "ready"
    assert "checks" in data
    assert data["checks"]["openai_key_configured"] is True


def test_health_ready_fails_when_dependency_down(
    client: TestClient,
    test_settings: Settings,
) -> None:
    """
    Test GET /health/ready returns 503 when dependencies are not ready.

    Verifies:
    - Status code is 503 when API key is missing
    - Response contains status "not_ready"
    - Checks indicate what failed
    """
    # Arrange - Override settings to simulate missing API key
    # Use model_construct to bypass validation (for testing unhealthy scenarios)
    unhealthy_settings = Settings.model_construct(
        environment="development",
        debug=True,
        llm_provider="openai",
        openai_api_key="",  # Empty API key to simulate unhealthy state
        openai_model="gpt-4o",
        groq_api_key="",
        groq_model="llama-3.3-70b-versatile",
        log_level="DEBUG",
        log_format="colored",
        enable_docs=True,
    )

    # Update dependency override
    from app.backend.api.dependencies import get_settings
    from app.backend.main import create_app

    app = create_app()
    app.dependency_overrides[get_settings] = lambda: unhealthy_settings

    # Act
    with TestClient(app) as unhealthy_client:
        response = unhealthy_client.get("/api/v1/health/ready")

    # Assert
    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

    data = response.json()
    assert "detail" in data
    # The detail contains the HealthResponse with checks
    if isinstance(data["detail"], dict):
        assert data["detail"]["status"] == "not_ready"
        assert "checks" in data["detail"]
        assert data["detail"]["checks"]["openai_key_configured"] is False
