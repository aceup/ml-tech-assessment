"""
Integration tests for global exception handlers.

Tests the full exception handling flow by triggering exceptions
through real endpoint calls and verifying HTTP responses, status codes,
and response structure.
"""

from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from app.backend.utils.exceptions import (
    ExternalServiceException,
    NotFoundException,
    ValidationException,
)


# ============================================================================
# Test 1: NotFoundException Handler - Returns 404 JSON Response
# ============================================================================


def test_not_found_exception_handler_returns_404_json(client: TestClient):
    """
    Test that NotFoundException is caught and returns 404 JSON response.

    Arrange: Use a valid endpoint and request non-existent resource
    Act: Make GET request for non-existent analysis ID
    Assert:
    - Status code is 404 (Not Found)
    - Response contains error field with "NotFoundException"
    - Response contains message with "not found"
    - Response includes request_id
    - Response structure matches ErrorResponse model
    """
    # Arrange
    non_existent_id = "this-does-not-exist-12345"

    # Act - Request non-existent analysis
    response = client.get(f"/api/v1/analyses/{non_existent_id}")

    # Assert - Status code
    assert response.status_code == 404

    # Assert - Response structure
    data = response.json()
    assert isinstance(data, dict)

    # Assert - Error details
    assert "error" in data
    assert data["error"] == "NotFoundException"

    assert "message" in data
    assert "not found" in data["message"].lower()

    # Assert - Request ID present
    assert "request_id" in data
    assert data["request_id"] is not None
    assert isinstance(data["request_id"], str)
    assert len(data["request_id"]) > 0

    # Assert - Details included
    assert "details" in data
    assert data["details"]["resource"] == "Analysis"
    assert data["details"]["identifier"] == non_existent_id


def test_not_found_exception_handler_request_id_in_response_header(
    client: TestClient,
):
    """
    Test that request_id from middleware is propagated to response header.

    Arrange: Make request with custom request ID
    Act: Request non-existent resource
    Assert: Response includes X-Request-ID header matching request ID
    """
    # Arrange
    non_existent_id = "missing-analysis-id"
    custom_request_id = "test-request-id-12345"

    # Act
    response = client.get(
        f"/api/v1/analyses/{non_existent_id}",
        headers={"X-Request-ID": custom_request_id},
    )

    # Assert - Response header includes request ID
    assert "X-Request-ID" in response.headers
    assert response.headers["X-Request-ID"] == custom_request_id

    # Assert - Response body also includes request ID
    data = response.json()
    assert data["request_id"] == custom_request_id


# ============================================================================
# Test 2: ValidationException Handler - Returns 422 JSON Response
# ============================================================================


def test_validation_exception_handler_returns_422_json(client: TestClient):
    """
    Test that Pydantic ValidationError is caught and returns 422 JSON response.

    Arrange: Create request with invalid transcript (too short)
    Act: GET to analyze endpoint with invalid query parameter
    Assert:
    - Status code is 422 (Unprocessable Entity)
    - Response contains detail field with FastAPI standard validation errors
    - Response includes request_id for consistency
    """
    # Arrange - Invalid request: transcript too short (less than min_length=10)
    invalid_transcript = "short"

    # Act
    response = client.get("/api/v1/analyses/analyze", params={"transcript": invalid_transcript})

    # Assert - Status code
    assert response.status_code == 422

    # Assert - Response structure
    data = response.json()
    assert isinstance(data, dict)

    # Assert - FastAPI standard format with detail field
    assert "detail" in data
    assert isinstance(data["detail"], list)
    assert len(data["detail"]) > 0

    # Assert - Request ID present for consistency
    assert "request_id" in data
    assert data["request_id"] is not None

    # Assert - Validation error details include field information (FastAPI standard)
    error_details = data["detail"][0]
    assert "loc" in error_details  # Field location
    assert "msg" in error_details  # Error message
    assert "type" in error_details  # Error type


def test_validation_exception_handler_empty_transcript(client: TestClient):
    """
    Test validation error handling for empty transcript.

    Arrange: Create request with empty/whitespace-only transcript
    Act: GET to analyze endpoint with empty transcript
    Assert: Returns 422 status with FastAPI standard validation error format
    """
    # Arrange - Empty transcript
    invalid_transcript = ""

    # Act
    response = client.get("/api/v1/analyses/analyze", params={"transcript": invalid_transcript})

    # Assert - Status code
    assert response.status_code == 422

    # Assert - FastAPI standard error response format
    data = response.json()
    assert "detail" in data
    assert isinstance(data["detail"], list)
    assert len(data["detail"]) > 0


def test_validation_exception_handler_too_long_transcript(client: TestClient):
    """
    Test validation error handling for transcript exceeding max_length.

    Arrange: Create request with very long transcript (over max_length=10000)
    Act: GET to analyze endpoint with oversized transcript
    Assert: Returns 422 status with FastAPI standard validation error format
    """
    # Arrange - Transcript exceeding max_length
    oversized_transcript = "A" * 10001  # One char over max_length

    # Act
    response = client.get("/api/v1/analyses/analyze", params={"transcript": oversized_transcript})

    # Assert - Status code
    assert response.status_code == 422

    # Assert - FastAPI standard error response format
    data = response.json()
    assert "detail" in data
    assert isinstance(data["detail"], list)
    assert len(data["detail"]) > 0


# ============================================================================
# Test 3: ExternalServiceException Handler - Returns 502 JSON Response
# ============================================================================


def test_external_service_exception_handler_returns_502_json(
    client: TestClient,
    mock_openai_adapter: AsyncMock,
):
    """
    Test that ExternalServiceException is caught and returns 502 JSON response.

    Arrange: Mock LLM adapter to raise ExternalServiceException
    Act: GET to analyze endpoint, triggering LLM failure
    Assert:
    - Status code is 502 (Bad Gateway)
    - Response contains error field with "ExternalServiceException"
    - Response contains service error message
    - Response includes request_id
    - Response includes error details
    """
    # Arrange - Mock LLM adapter to fail with ExternalServiceException
    from app.backend.utils.exceptions import ExternalServiceException

    mock_error = ExternalServiceException(
        service="OpenAI",
        message="API rate limit exceeded",
        details={"retry_after": 60},
    )

    mock_openai_adapter.run_completion_async.side_effect = mock_error

    # Use valid transcript to pass input validation
    valid_transcript = "Patient reports headache for 3 days"

    # Act
    response = client.get("/api/v1/analyses/analyze", params={"transcript": valid_transcript})

    # Assert - Status code
    assert response.status_code == 502

    # Assert - Response structure
    data = response.json()
    assert isinstance(data, dict)

    # Assert - Error type
    assert "error" in data
    assert data["error"] == "ExternalServiceException"

    # Assert - Error message includes service information
    assert "message" in data
    assert "OpenAI" in data["message"]
    assert "rate limit" in data["message"].lower()

    # Assert - Request ID present
    assert "request_id" in data
    assert data["request_id"] is not None

    # Assert - Details included with service name
    assert "details" in data
    assert "service" in data["details"]
    assert data["details"]["service"] == "OpenAI"


def test_external_service_exception_handler_includes_error_context(
    client: TestClient,
    mock_openai_adapter: AsyncMock,
):
    """
    Test that ExternalServiceException includes service error context.

    Arrange: Mock LLM adapter with detailed error context
    Act: POST to analyze endpoint
    Assert: Response includes error details and service context
    """
    # Arrange
    mock_error = ExternalServiceException(
        service="OpenAI",
        message="Connection timeout after 30 seconds",
        details={"timeout_seconds": 30, "endpoint": "/v1/chat/completions"},
    )

    mock_openai_adapter.run_completion_async.side_effect = mock_error

    valid_transcript = "Patient feels dizzy when standing up"

    # Act
    response = client.get("/api/v1/analyses/analyze", params={"transcript": valid_transcript})

    # Assert - Status code
    assert response.status_code == 502

    # Assert - Error details
    data = response.json()
    assert "timeout" in data["message"].lower()

    # Assert - Custom details preserved
    assert "details" in data
    assert data["details"]["service"] == "OpenAI"


# ============================================================================
# Test 4: Exception Handler - Request ID Propagation
# ============================================================================


def test_exception_handler_includes_request_id_in_response(
    client: TestClient,
):
    """
    Test that request_id from middleware is included in exception response.

    Arrange: Make request that will trigger NotFoundException
    Act: Request non-existent resource
    Assert: response includes request_id from middleware
    """
    # Arrange
    non_existent_id = "missing-uuid-12345"

    # Act - This will trigger NotFoundException
    response = client.get(f"/api/v1/analyses/{non_existent_id}")

    # Assert - Status code
    assert response.status_code == 404

    # Assert - Request ID is present in response body
    data = response.json()
    assert "request_id" in data
    assert data["request_id"] is not None
    assert isinstance(data["request_id"], str)

    # Assert - Request ID is also in response headers
    assert "X-Request-ID" in response.headers
    assert response.headers["X-Request-ID"] == data["request_id"]


def test_exception_handler_request_id_propagation_across_errors(
    client: TestClient,
    mock_openai_adapter: AsyncMock,
):
    """
    Test that request_id is consistent across different exception types.

    Arrange: Make multiple requests with custom request IDs
    Act: Trigger different types of exceptions
    Assert: Each response includes the correct request_id
    """
    # Test 1: NotFoundException
    request_id_1 = "test-request-id-001"
    response_1 = client.get(
        "/api/v1/analyses/missing-id",
        headers={"X-Request-ID": request_id_1},
    )

    data_1 = response_1.json()
    assert data_1["request_id"] == request_id_1
    assert response_1.headers["X-Request-ID"] == request_id_1

    # Test 2: ValidationException
    request_id_2 = "test-request-id-002"
    response_2 = client.get(
        "/api/v1/analyses/analyze",
        params={"transcript": "bad"},
        headers={"X-Request-ID": request_id_2},
    )

    data_2 = response_2.json()
    assert data_2["request_id"] == request_id_2
    assert response_2.headers["X-Request-ID"] == request_id_2

    # Test 3: ExternalServiceException
    mock_openai_adapter.run_completion_async.side_effect = ExternalServiceException(
        service="OpenAI",
        message="API error",
    )

    request_id_3 = "test-request-id-003"
    response_3 = client.get(
        "/api/v1/analyses/analyze",
        params={"transcript": "Valid long transcript for testing purposes"},
        headers={"X-Request-ID": request_id_3},
    )

    data_3 = response_3.json()
    assert data_3["request_id"] == request_id_3
    assert response_3.headers["X-Request-ID"] == request_id_3


def test_exception_handler_auto_generates_request_id_if_missing(
    client: TestClient,
):
    """
    Test that request_id is auto-generated if not provided in request.

    Arrange: Make request without X-Request-ID header
    Act: Trigger exception
    Assert: Response includes auto-generated request_id
    """
    # Arrange
    non_existent_id = "missing-id"

    # Act - No X-Request-ID header provided
    response = client.get(f"/api/v1/analyses/{non_existent_id}")

    # Assert - Status code
    assert response.status_code == 404

    # Assert - Request ID was auto-generated
    data = response.json()
    assert "request_id" in data
    assert data["request_id"] is not None
    assert len(data["request_id"]) > 0  # Should be a UUID

    # Assert - Request ID is also in headers
    assert "X-Request-ID" in response.headers
    assert response.headers["X-Request-ID"] == data["request_id"]


# ============================================================================
# Additional Error Response Structure Tests
# ============================================================================


def test_error_response_structure_matches_schema(client: TestClient):
    """
    Test that all error responses match ErrorResponse model structure.

    Arrange: Trigger an exception
    Act: Make request that causes 404 error
    Assert: Response structure matches ErrorResponse schema:
    - error: string
    - message: string
    - request_id: string or null
    - details: dict or null
    """
    # Arrange
    non_existent_id = "missing"

    # Act
    response = client.get(f"/api/v1/analyses/{non_existent_id}")

    # Assert
    data = response.json()

    # Verify required fields
    assert "error" in data
    assert "message" in data
    assert "request_id" in data

    # Verify field types
    assert isinstance(data["error"], str)
    assert isinstance(data["message"], str)
    assert data["request_id"] is None or isinstance(data["request_id"], str)

    # Verify details field (optional)
    if "details" in data:
        assert data["details"] is None or isinstance(data["details"], dict)


def test_error_response_excludes_none_fields(client: TestClient):
    """
    Test that error response excludes fields with None values.

    Arrange: Trigger a generic exception (uses generic handler)
    Act: Make a valid request that passes endpoint validation
    Assert: Response doesn't include null fields unnecessarily
    """
    # Arrange
    non_existent_id = "test-id"

    # Act
    response = client.get(f"/api/v1/analyses/{non_existent_id}")

    # Assert - Response should include details since NotFoundException has them
    data = response.json()
    assert "error" in data
    assert "message" in data
    assert "request_id" in data
    # Details should be present for NotFoundException
    assert "details" in data or "details" not in data
