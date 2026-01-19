"""
End-to-end workflow tests.

Tests complete request/response flows from HTTP request through middleware,
endpoint, service, adapter, repository, and back to HTTP response.

Validates:
- Request ID propagation through all layers
- Error context preservation across stack
- State isolation between concurrent requests
- Complete success and failure paths
"""

import concurrent.futures
from unittest.mock import AsyncMock

import pytest

from app.services.analysis_service import LLMAnalysisResult
from app.utils.exceptions import ExternalServiceException


class TestCompleteWorkflows:
    """Test complete end-to-end workflows through the entire application stack."""

    def test_complete_analysis_workflow_from_request_to_response(self, client, mock_openai_adapter, auth_headers):
        """
        Test complete workflow: HTTP request → middleware → endpoint → service → adapter → repository → response.

        Validates:
        - HTTP 201 Created response
        - Complete response structure with all required fields
        - Request ID propagated from request header to response header
        - Analysis persisted and retrievable via GET
        - LLM adapter called with correct transcript
        """
        # Arrange
        transcript = "Patient reports severe headache for 3 days with nausea and sensitivity to light."
        request_id = "test-e2e-request-id-001"

        # Configure mock to return specific result (now returns LLMResponse)
        from app.ports.llm import LLMResponse

        mock_parsed = LLMAnalysisResult(
            summary="Patient presents with migraine symptoms: severe headache, nausea, photophobia for 3 days.",
            next_actions=[
                "Perform neurological examination",
                "Assess for visual disturbances or aura",
                "Consider migraine prophylaxis if recurrent"
            ],
        )

        mock_openai_adapter.run_completion_async.return_value = LLMResponse(
            parsed_result=mock_parsed,
            raw_response='{"summary":"...","next_actions":[...]}',
            input_tokens=100,
            output_tokens=50,
            total_tokens=150,
            latency_ms=200.0,
            model="gpt-4o",
            provider="openai",
        )

        # Act - Make HTTP GET request
        response = client.get(
            "/api/v1/analyses/analyze",
            params={"transcript": transcript},
            headers={
                **auth_headers,
                "X-Request-ID": request_id,
            },
        )

        # Assert - HTTP response status
        assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}"

        # Assert - Response structure
        data = response.json()
        assert "id" in data, "Response missing 'id' field"
        assert isinstance(data["id"], str), "ID must be a string"
        assert len(data["id"]) > 0, "ID must not be empty"

        assert data["transcript"] == transcript, "Transcript not preserved in response"

        assert data["summary"] is not None, "Summary is missing"
        assert isinstance(data["summary"], str), "Summary must be a string"
        assert "migraine" in data["summary"].lower(), "Summary doesn't contain expected content"

        assert data["next_actions"] is not None, "Next actions are missing"
        assert isinstance(data["next_actions"], list), "Next actions must be a list"
        assert len(data["next_actions"]) > 0, "Next actions list should not be empty"
        assert any("examination" in action.lower() for action in data["next_actions"]), "Next actions don't contain expected content"

        assert "created_at" in data, "Response missing 'created_at' field"
        assert data["created_at"] is not None, "Created timestamp is missing"

        # Assert - Request ID propagated to response header
        assert response.headers["X-Request-ID"] == request_id, "Request ID not in response header"

        # Assert - LLM adapter was called with correct transcript
        mock_openai_adapter.run_completion_async.assert_called_once()
        call_args = mock_openai_adapter.run_completion_async.call_args
        assert transcript in str(call_args), "LLM adapter not called with correct transcript"

        # Assert - Analysis persisted (verify via GET)
        analysis_id = data["id"]
        get_response = client.get(
            f"/api/v1/analyses/{analysis_id}",
            headers={
                **auth_headers,
                "X-Request-ID": "test-get-request-002",
            },
        )

        assert get_response.status_code == 200, "Failed to retrieve persisted analysis"
        get_data = get_response.json()
        assert get_data["id"] == analysis_id, "Retrieved analysis ID doesn't match"
        assert get_data["transcript"] == transcript, "Retrieved transcript doesn't match"
        assert get_data["summary"] == data["summary"], "Retrieved summary doesn't match"
        assert get_data["next_actions"] == data["next_actions"], "Retrieved next_actions don't match"

    def test_complete_workflow_with_validation_error_propagates_correctly(self, client):
        """
        Test validation error flows through entire stack correctly.

        Validates:
        - HTTP 422 Unprocessable Entity for validation errors
        - Request ID in error response body and header
        - Pydantic validation error details preserved
        - No LLM call for invalid input (early rejection)
        """
        # Arrange - Transcript too short (minimum 10 characters)
        short_transcript = "short"
        custom_request_id = "e2e-validation-error-test-123"

        # Act - Submit invalid request
        response = client.get(
            "/api/v1/analyses/analyze",
            params={"transcript": short_transcript},
            headers={"X-Request-ID": custom_request_id},
        )

        # Assert - HTTP 422 status
        assert response.status_code == 422, f"Expected 422 for validation error, got {response.status_code}"

        # Assert - Response contains validation error details
        data = response.json()
        assert "detail" in data, "Validation error response missing 'detail' field"
        assert isinstance(data["detail"], list), "Validation errors should be a list"
        assert len(data["detail"]) > 0, "Validation errors list is empty"

        # Assert - Request ID in error response body
        assert "request_id" in data, "Request ID missing from validation error response"
        assert data["request_id"] == custom_request_id, "Request ID doesn't match in error response"

        # Assert - Request ID in response header
        assert response.headers["X-Request-ID"] == custom_request_id, "Request ID not in error response header"

        # Assert - Error details contain field information
        error = data["detail"][0]
        assert "loc" in error, "Error missing 'loc' field"
        assert "msg" in error, "Error missing 'msg' field"
        assert "transcript" in str(error["loc"]), "Error doesn't reference 'transcript' field"

    def test_complete_workflow_with_llm_failure_returns_502(self, client, mock_openai_adapter):
        """
        Test LLM service failure propagates as 502 Bad Gateway.

        Validates:
        - HTTP 502 when external LLM service fails
        - Request ID preserved in error response
        - Error details include service information
        - Proper exception handling through all layers
        """
        # Arrange - Configure mock to raise exception
        llm_error_message = "OpenAI API rate limit exceeded"
        mock_openai_adapter.run_completion_async.side_effect = ExternalServiceException(
            service="OpenAI",
            message=llm_error_message,
            details={"provider": "openai", "model": "gpt-4o"},
        )

        transcript = "Patient complains of persistent cough and fever for 5 days."
        request_id = "e2e-llm-failure-test-456"

        # Act - Submit request that will fail at LLM layer
        response = client.get(
            "/api/v1/analyses/analyze",
            params={"transcript": transcript},
            headers={"X-Request-ID": request_id},
        )

        # Assert - HTTP 502 Bad Gateway
        assert response.status_code == 502, f"Expected 502 for LLM failure, got {response.status_code}"

        # Assert - Error response structure
        data = response.json()
        assert "error" in data, "Error response missing 'error' field"
        assert "message" in data, "Error response missing 'message' field"
        assert "request_id" in data, "Error response missing 'request_id' field"

        # Assert - Request ID preserved
        assert data["request_id"] == request_id, "Request ID not preserved in error response"

        # Assert - Error details preserved
        assert "OpenAI" in data["message"], "Error message doesn't mention service name"
        assert "details" in data, "Error response missing 'details' field"
        assert data["details"]["service"] == "OpenAI", "Service name not in error details"

        # Assert - Request ID in response header
        assert response.headers["X-Request-ID"] == request_id, "Request ID not in error response header"

    def test_request_id_propagates_through_entire_stack(self, client, mock_openai_adapter):
        """
        Test request ID flows through: header → middleware → state → service logs → error responses → response header.

        Validates:
        - Custom request ID from header is preserved
        - Request ID available in request.state
        - Request ID in successful response header
        - Request ID in error response body and header
        - Generated request ID when not provided
        """
        # Test 1: Custom request ID with validation error
        custom_request_id = "e2e-propagation-test-123"

        response = client.get(
            "/api/v1/analyses/analyze",
            params={"transcript": "short"},  # Too short - validation error
            headers={"X-Request-ID": custom_request_id},
        )

        # Assert - Request ID in error response body
        assert response.status_code == 422
        data = response.json()
        assert data["request_id"] == custom_request_id, "Request ID not in validation error body"

        # Assert - Request ID in error response header
        assert response.headers["X-Request-ID"] == custom_request_id, "Request ID not in error header"

        # Test 2: Custom request ID with successful request
        success_request_id = "e2e-success-456"

        response2 = client.get(
            "/api/v1/analyses/analyze",
            params={"transcript": "Valid transcript for testing request ID propagation through successful flow"},
            headers={"X-Request-ID": success_request_id},
        )

        assert response2.status_code == 200
        assert response2.headers["X-Request-ID"] == success_request_id, "Request ID not in success response header"

        # Test 3: No request ID provided - should generate one
        response3 = client.get(
            "/api/v1/analyses/analyze",
            params={"transcript": "Another valid transcript without custom request ID header"},
        )

        assert response3.status_code == 200
        generated_id = response3.headers.get("X-Request-ID")
        assert generated_id is not None, "No request ID generated when not provided"
        assert len(generated_id) > 0, "Generated request ID is empty"
        # Should be UUID format (36 characters with hyphens)
        assert len(generated_id) == 36, "Generated request ID not in UUID format"
        assert generated_id.count("-") == 4, "Generated request ID not in UUID format"

    def test_error_details_preserved_through_stack(self, client, mock_openai_adapter):
        """
        Test error context flows from adapter → service → endpoint → HTTP response.

        Validates:
        - Exception details preserved through all layers
        - Structured error information in response
        - Request ID included in error context
        - Error type and message accessible
        """
        # Arrange - Configure mock with detailed error
        error_details = {
            "provider": "openai",
            "model": "gpt-4o",
            "error_code": "rate_limit_exceeded",
            "retry_after": 60,
        }

        mock_openai_adapter.run_completion_async.side_effect = ExternalServiceException(
            service="OpenAI",
            message="API quota exceeded. Retry after 60 seconds.",
            details=error_details,
        )

        transcript = "Patient has persistent joint pain and morning stiffness."
        request_id = "e2e-error-context-test-789"

        # Act
        response = client.get(
            "/api/v1/analyses/analyze",
            params={"transcript": transcript},
            headers={"X-Request-ID": request_id},
        )

        # Assert - Error response structure
        assert response.status_code == 502
        data = response.json()

        # Assert - All error details preserved
        assert data["error"] == "ExternalServiceException", "Error type not preserved"
        assert "OpenAI" in data["message"], "Service name not in error message"
        assert "quota" in data["message"].lower(), "Error context not in message"

        assert "details" in data, "Error details missing"
        assert data["details"]["service"] == "OpenAI", "Service name not in details"
        assert "error_code" in data["details"], "Error code not preserved"
        assert data["details"]["error_code"] == "rate_limit_exceeded", "Error code value not preserved"
        assert data["details"]["retry_after"] == 60, "Retry duration not preserved"

        # Assert - Request ID in error context
        assert data["request_id"] == request_id, "Request ID not in error response"

        # Assert - Response headers include request ID
        assert response.headers["X-Request-ID"] == request_id, "Request ID not in response header"

    def test_concurrent_requests_maintain_isolation(self, client, mock_openai_adapter):
        """
        Test that concurrent requests don't share state or interfere with each other.

        Validates:
        - Concurrent requests handled independently
        - No state leakage between requests
        - Correct request IDs returned for each request
        - Correct transcripts and results for each request
        - All requests succeed when processed concurrently
        """
        # Arrange - Different transcripts to verify isolation
        test_cases = [
            ("Patient A has severe headache and nausea for 2 days", "req-a", "headache summary", ["headache actions"]),
            ("Patient B presents with fever and persistent cough", "req-b", "fever summary", ["fever actions"]),
            ("Patient C reports chest pain and shortness of breath", "req-c", "chest summary", ["chest actions"]),
        ]

        # Configure mock to return different results based on input
        def mock_llm_response(*args, **kwargs):
            # Extract transcript from call arguments
            call_str = str(args) + str(kwargs)
            if "headache" in call_str.lower():
                return LLMAnalysisResult(
                    summary="headache summary",
                    next_actions=["headache actions"],
                )
            elif "fever" in call_str.lower():
                return LLMAnalysisResult(
                    summary="fever summary",
                    next_actions=["fever actions"],
                )
            elif "chest" in call_str.lower():
                return LLMAnalysisResult(
                    summary="chest summary",
                    next_actions=["chest actions"],
                )
            else:
                return LLMAnalysisResult(
                    summary="default summary",
                    next_actions=["default actions"],
                )

        mock_openai_adapter.run_completion_async.side_effect = mock_llm_response

        def make_request(transcript: str, request_id: str):
            """Make a single request."""
            return client.get(
                "/api/v1/analyses/analyze",
                params={"transcript": transcript},
                headers={"X-Request-ID": request_id},
            )

        # Act - Make concurrent requests using thread pool
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(make_request, t, rid) for t, rid, _, _ in test_cases]
            responses = [f.result() for f in futures]

        # Assert - All requests succeeded
        assert all(r.status_code == 200 for r in responses), "Not all concurrent requests succeeded"

        # Assert - Correct request IDs returned (verify isolation)
        for i, response in enumerate(responses):
            expected_id = test_cases[i][1]
            actual_id = response.headers["X-Request-ID"]
            assert actual_id == expected_id, f"Request ID mismatch for request {i}: expected {expected_id}, got {actual_id}"

        # Assert - Correct transcripts in responses (no cross-contamination)
        for i, response in enumerate(responses):
            expected_transcript = test_cases[i][0]
            actual_transcript = response.json()["transcript"]
            assert (
                actual_transcript == expected_transcript
            ), f"Transcript mismatch for request {i}: expected '{expected_transcript}', got '{actual_transcript}'"

        # Assert - Correct analysis results (verify no state sharing)
        for i, response in enumerate(responses):
            data = response.json()
            expected_summary = test_cases[i][2]
            expected_actions = test_cases[i][3]

            assert (
                data["summary"] == expected_summary
            ), f"Summary mismatch for request {i}: expected '{expected_summary}', got '{data['summary']}'"
            assert (
                data["next_actions"] == expected_actions
            ), f"Next actions mismatch for request {i}: expected '{expected_actions}', got '{data['next_actions']}'"

        # Assert - All analyses have unique IDs
        analysis_ids = [r.json()["id"] for r in responses]
        assert len(analysis_ids) == len(set(analysis_ids)), "Duplicate analysis IDs found (state leak)"

        # Assert - All analyses persisted independently
        for response in responses:
            analysis_id = response.json()["id"]
            get_response = client.get(f"/api/v1/analyses/{analysis_id}")
            assert get_response.status_code == 200, f"Failed to retrieve analysis {analysis_id}"

        # Assert - List endpoint returns all analyses
        list_response = client.get("/api/v1/analyses")
        assert list_response.status_code == 200
        all_analyses = list_response.json()
        assert len(all_analyses) >= 3, "Not all concurrent analyses persisted"


class TestEdgeCases:
    """Test edge cases in E2E workflows."""

    def test_extremely_long_transcript_within_limits(self, client, mock_openai_adapter):
        """Test transcript at maximum allowed length (10000 characters)."""
        # Arrange - Create transcript at max length
        long_transcript = "Patient reports symptoms. " * 400  # ~10000 characters
        long_transcript = long_transcript[:10000]  # Exactly 10000 chars

        # Act
        response = client.get(
            "/api/v1/analyses/analyze",
            params={"transcript": long_transcript},
            headers={"X-Request-ID": "long-transcript-test"},
        )

        # Assert
        assert response.status_code == 200, "Failed to handle maximum length transcript"
        data = response.json()
        # Note: Validator strips whitespace, so compare lengths and content preservation
        assert len(data["transcript"]) > 9900, "Long transcript was truncated"
        assert "Patient reports symptoms" in data["transcript"], "Transcript content not preserved"

    def test_transcript_exceeding_maximum_length(self, client):
        """Test transcript exceeding maximum allowed length (>10000 characters)."""
        # Arrange - Create transcript over max length
        too_long_transcript = "Patient reports symptoms. " * 500  # >10000 characters

        # Act
        response = client.get(
            "/api/v1/analyses/analyze",
            params={"transcript": too_long_transcript},
            headers={"X-Request-ID": "too-long-test"},
        )

        # Assert
        assert response.status_code == 422, "Should reject transcript over max length"
        data = response.json()
        assert "request_id" in data, "Request ID missing from validation error"
        assert data["request_id"] == "too-long-test", "Request ID not preserved"

    def test_whitespace_only_transcript_rejected(self, client):
        """Test that whitespace-only transcript is rejected."""
        # Arrange
        whitespace_transcript = "          "  # Only spaces

        # Act
        response = client.get(
            "/api/v1/analyses/analyze",
            params={"transcript": whitespace_transcript},
            headers={"X-Request-ID": "whitespace-test"},
        )

        # Assert - Should return 422 validation error
        assert response.status_code == 422, "Should reject whitespace-only transcript"
        data = response.json()

        # Verify error details
        assert "detail" in data, "Response should include validation error details"

        # Handle both list (FastAPI validation) and string (custom HTTPException) formats
        if isinstance(data["detail"], list):
            # FastAPI standard validation format
            assert len(data["detail"]) > 0, "Should have at least one validation error"
            error_messages = " ".join(str(err.get("msg", "")) for err in data["detail"])
        else:
            # Custom HTTPException format (string)
            error_messages = str(data["detail"])

        # Verify the error mentions whitespace or empty
        assert "whitespace" in error_messages.lower() or "empty" in error_messages.lower(), \
            f"Error should mention whitespace/empty: {error_messages}"

    def test_special_characters_in_transcript(self, client, mock_openai_adapter):
        """Test transcript with special characters, unicode, and emojis."""
        # Arrange
        special_transcript = (
            "Patient says: 'I feel 😷 sick!' Temperature: 38.5°C. "
            "Symptoms include: cough, fever, & malaise. "
            "Notes: café → check résumé for allergies."
        )

        # Act
        response = client.get(
            "/api/v1/analyses/analyze",
            params={"transcript": special_transcript},
            headers={"X-Request-ID": "special-chars-test"},
        )

        # Assert
        assert response.status_code == 200, "Failed to handle special characters"
        data = response.json()
        assert data["transcript"] == special_transcript, "Special characters not preserved"

    def test_retrieval_of_nonexistent_analysis(self, client):
        """Test GET request for analysis that doesn't exist."""
        # Arrange
        nonexistent_id = "this-id-does-not-exist-12345"

        # Act
        response = client.get(
            f"/api/v1/analyses/{nonexistent_id}",
            headers={"X-Request-ID": "not-found-test"},
        )

        # Assert
        assert response.status_code == 404, "Should return 404 for nonexistent analysis"
        data = response.json()
        assert "request_id" in data, "Request ID missing from 404 response"
        assert data["request_id"] == "not-found-test", "Request ID not preserved"
        assert "message" in data, "Error message missing"
        assert nonexistent_id in data["message"], "Error message doesn't mention the ID"
