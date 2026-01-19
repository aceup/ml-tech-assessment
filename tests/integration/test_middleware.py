"""
Integration tests for middleware components.

Tests middleware behavior through real HTTP requests using TestClient.
Verifies RequestIDMiddleware and RequestLoggingMiddleware functionality.
"""

import logging
import uuid

import pytest
from fastapi.testclient import TestClient


# ============================================================================
# RequestIDMiddleware Integration Tests
# ============================================================================


def test_request_id_middleware_generates_id_when_header_missing(client: TestClient):
    """Test that middleware generates UUID when X-Request-ID header missing."""
    # Arrange - No custom request ID header

    # Act
    response = client.get("/api/v1/health/live")

    # Assert
    assert response.status_code == 200
    assert "X-Request-ID" in response.headers

    request_id = response.headers["X-Request-ID"]
    assert len(request_id) == 36  # UUID format
    assert "-" in request_id  # UUID contains hyphens

    # Verify it's a valid UUID
    try:
        uuid.UUID(request_id)
    except ValueError:
        pytest.fail(f"Generated request ID is not a valid UUID: {request_id}")


def test_request_id_middleware_uses_custom_id_from_header(client: TestClient):
    """Test that middleware uses custom request ID from X-Request-ID header."""
    # Arrange
    custom_request_id = "custom-request-id-12345"
    headers = {"X-Request-ID": custom_request_id}

    # Act
    response = client.get("/api/v1/health/live", headers=headers)

    # Assert
    assert response.status_code == 200
    assert "X-Request-ID" in response.headers
    assert response.headers["X-Request-ID"] == custom_request_id


def test_request_id_middleware_adds_id_to_response_header(client: TestClient):
    """Test that middleware adds request ID to response headers."""
    # Arrange - Make multiple requests

    # Act
    response1 = client.get("/api/v1/health/live")
    response2 = client.get("/api/v1/health/live")

    # Assert
    assert "X-Request-ID" in response1.headers
    assert "X-Request-ID" in response2.headers

    # Each request should have different generated IDs
    request_id_1 = response1.headers["X-Request-ID"]
    request_id_2 = response2.headers["X-Request-ID"]
    assert request_id_1 != request_id_2


def test_request_id_middleware_stores_id_in_request_state(client: TestClient):
    """Test that middleware stores request ID in request.state for other middleware."""
    # Arrange
    custom_request_id = "state-storage-test-id"
    headers = {"X-Request-ID": custom_request_id}

    # Act
    response = client.get("/api/v1/health/live", headers=headers)

    # Assert - Verify ID is in response (proves it was stored in state and propagated)
    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == custom_request_id

    # Note: We can't directly access request.state in integration tests,
    # but we can verify the ID propagates to logging middleware by checking logs
    # (tested in test_logging_middleware_includes_request_id_in_logs)


# ============================================================================
# RequestLoggingMiddleware Integration Tests
# ============================================================================


def test_logging_middleware_logs_request_start_and_completion(
    client: TestClient, caplog: pytest.LogCaptureFixture
):
    """Test that logging middleware logs request lifecycle."""
    # Arrange
    caplog.set_level(logging.INFO)

    # Act
    response = client.get("/api/v1/health/live")

    # Assert
    assert response.status_code == 200

    log_messages = [record.message for record in caplog.records]
    assert any("request_started" in msg for msg in log_messages), \
        f"Expected 'request_started' in logs. Got: {log_messages}"
    assert any("request_completed" in msg for msg in log_messages), \
        f"Expected 'request_completed' in logs. Got: {log_messages}"


def test_logging_middleware_includes_request_id_in_logs(
    client: TestClient, caplog: pytest.LogCaptureFixture
):
    """Test that logging middleware includes request ID in log entries."""
    # Arrange
    caplog.set_level(logging.INFO)
    custom_request_id = "logging-test-request-id"
    headers = {"X-Request-ID": custom_request_id}

    # Act
    response = client.get("/api/v1/health/live", headers=headers)

    # Assert
    assert response.status_code == 200

    # Check that request ID appears in log messages
    log_messages = [record.message for record in caplog.records]
    assert any(custom_request_id in msg for msg in log_messages), \
        f"Expected request ID '{custom_request_id}' in logs. Got: {log_messages}"

    # Verify request ID is in structured log context (JSON logs)
    import json
    logs_with_request_id = []
    for record in caplog.records:
        try:
            log_data = json.loads(record.message)
            if log_data.get("request_id") == custom_request_id:
                logs_with_request_id.append(log_data)
        except json.JSONDecodeError:
            # Skip non-JSON log records (like httpx logs)
            pass

    assert len(logs_with_request_id) > 0, \
        "Request ID should be in structured log context"


def test_logging_middleware_measures_duration(
    client: TestClient, caplog: pytest.LogCaptureFixture
):
    """Test that logging middleware measures and logs request duration."""
    # Arrange
    caplog.set_level(logging.INFO)

    # Act
    response = client.get("/api/v1/health/live")

    # Assert
    assert response.status_code == 200

    # Check that duration_ms appears in completion log
    import json
    log_messages = [record.message for record in caplog.records]
    completion_logs = [msg for msg in log_messages if "request_completed" in msg]
    assert len(completion_logs) > 0, "Should have request_completed log"

    # Verify duration_ms is in structured log data (parse JSON)
    completion_events = []
    for record in caplog.records:
        try:
            log_data = json.loads(record.message)
            if log_data.get("event") == "request_completed":
                completion_events.append(log_data)
        except json.JSONDecodeError:
            pass

    assert len(completion_events) > 0, "Should have completion log record"

    # Check that duration_ms field exists and is reasonable
    completion_event = completion_events[0]
    assert "duration_ms" in completion_event, \
        "Completion log should have duration_ms field"

    duration_ms = completion_event["duration_ms"]
    assert isinstance(duration_ms, (int, float)), \
        f"duration_ms should be numeric, got {type(duration_ms)}"
    assert duration_ms >= 0, f"duration_ms should be non-negative, got {duration_ms}"
    assert duration_ms < 5000, \
        f"duration_ms should be reasonable for health check (<5s), got {duration_ms}"


# ============================================================================
# Middleware Order and Interaction Tests
# ============================================================================


def test_middleware_order_ensures_request_id_before_logging(
    client: TestClient, caplog: pytest.LogCaptureFixture
):
    """Test that RequestIDMiddleware runs before RequestLoggingMiddleware.

    Verifies middleware execution order by checking that:
    1. Request ID is generated/extracted first
    2. Logging middleware has access to request ID in request.state
    3. All log entries include the request ID
    """
    # Arrange
    caplog.set_level(logging.INFO)
    custom_request_id = "middleware-order-test-id"
    headers = {"X-Request-ID": custom_request_id}

    # Act
    response = client.get("/api/v1/health/live", headers=headers)

    # Assert
    assert response.status_code == 200

    # Verify request ID is in response (from RequestIDMiddleware)
    assert response.headers["X-Request-ID"] == custom_request_id

    # Verify ALL log entries from RequestLoggingMiddleware include the request ID (JSON logs)
    import json
    middleware_logs = []
    for record in caplog.records:
        try:
            log_data = json.loads(record.message)
            if "event" in log_data and log_data["event"] in ["request_started", "request_completed"]:
                middleware_logs.append(log_data)
        except json.JSONDecodeError:
            pass

    assert len(middleware_logs) >= 2, "Should have at least start and completion logs"

    for log_data in middleware_logs:
        # Each log should have request_id in structured context
        assert "request_id" in log_data, \
            f"Log entry missing request_id: {log_data}"
        assert log_data["request_id"] == custom_request_id, \
            f"Log entry has wrong request_id: expected {custom_request_id}, got {log_data['request_id']}"

    # Verify request_started comes before request_completed
    log_messages = [record.message for record in caplog.records]
    start_index = next(i for i, msg in enumerate(log_messages) if "request_started" in msg)
    completion_index = next(i for i, msg in enumerate(log_messages) if "request_completed" in msg)
    assert start_index < completion_index, \
        "request_started should be logged before request_completed"
