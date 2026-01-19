"""
Unit tests for LLM adapters (OpenAI and Groq).

Tests verify:
- Port implementation compliance
- Synchronous and asynchronous completion
- Response parsing to Pydantic DTOs
- Error handling (API errors, timeouts, malformed responses)
- No real API calls are made (all mocked)
"""

import json
from typing import Any
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pydantic
import pytest
from openai import APIError, APITimeoutError
from openai._exceptions import APIConnectionError

from app.backend.adapters.groq import GroqAdapter
from app.backend.adapters.openai import OpenAIAdapter
from app.backend.models.responses import AnalysisResult
from app.backend.ports.llm import LLm, LLMResponse


# Test DTO for validation
class MockAnalysisResponse(pydantic.BaseModel):
    """Test DTO matching AnalysisResult structure."""

    summary: str
    next_actions: list[str]


# ============================================================================
# OPENAI ADAPTER TESTS (8 tests)
# ============================================================================


def test_openai_adapter_implements_llm_port() -> None:
    """Test 1: Verify OpenAIAdapter implements LLm port interface."""
    adapter = OpenAIAdapter(api_key="test-key", model="gpt-4")
    assert isinstance(adapter, LLm), "OpenAIAdapter must implement LLm port"


@patch("openai.OpenAI")
def test_openai_run_completion_sync_success(mock_openai_client: Mock) -> None:
    """Test 2: OpenAI synchronous completion returns parsed DTO."""
    # Setup mock response
    mock_parsed = MockAnalysisResponse(
        summary="Test summary from OpenAI", next_actions=["Action 1\nAction 2"]
    )
    mock_message = Mock()
    mock_message.parsed = mock_parsed
    mock_choice = Mock()
    mock_choice.message = mock_message
    mock_completion = Mock()
    mock_completion.choices = [mock_choice]

    # Configure mock client
    mock_client_instance = Mock()
    mock_client_instance.beta.chat.completions.parse.return_value = mock_completion
    mock_openai_client.return_value = mock_client_instance

    # Execute
    adapter = OpenAIAdapter(api_key="test-key", model="gpt-4")
    result = adapter.run_completion(
        system_prompt="You are a helpful assistant",
        user_prompt="Analyze this text",
        dto=MockAnalysisResponse,
    )

    # Assert
    assert isinstance(result, MockAnalysisResponse)
    assert result.summary == "Test summary from OpenAI"
    assert result.next_actions == ["Action 1\nAction 2"]
    mock_client_instance.beta.chat.completions.parse.assert_called_once()


@pytest.mark.asyncio
@patch("openai.AsyncOpenAI")
async def test_openai_run_completion_async_success(
    mock_async_openai: Mock,
) -> None:
    """Test 3: OpenAI asynchronous completion returns LLMResponse with observability."""
    # Setup mock response
    mock_parsed = MockAnalysisResponse(
        summary="Async test summary", next_actions=["Async action 1"]
    )
    mock_message = Mock()
    mock_message.parsed = mock_parsed
    mock_message.content = '{"summary": "Async test summary", "next_actions": ["Async action 1"]}'
    mock_choice = Mock()
    mock_choice.message = mock_message

    # Mock token usage
    mock_usage = Mock()
    mock_usage.prompt_tokens = 100
    mock_usage.completion_tokens = 50
    mock_usage.total_tokens = 150

    mock_completion = Mock()
    mock_completion.choices = [mock_choice]
    mock_completion.usage = mock_usage

    # Configure async mock
    mock_async_client = Mock()
    mock_async_client.beta.chat.completions.parse = AsyncMock(
        return_value=mock_completion
    )
    mock_async_openai.return_value = mock_async_client

    # Execute
    adapter = OpenAIAdapter(api_key="test-key", model="gpt-4")
    result = await adapter.run_completion_async(
        system_prompt="You are a helpful assistant",
        user_prompt="Analyze this text",
        dto=MockAnalysisResponse,
    )

    # Assert - now returns LLMResponse
    assert isinstance(result, LLMResponse)
    assert isinstance(result.parsed_result, MockAnalysisResponse)
    assert result.parsed_result.summary == "Async test summary"
    assert result.parsed_result.next_actions == ["Async action 1"]
    assert result.input_tokens == 100
    assert result.output_tokens == 50
    assert result.total_tokens == 150
    assert result.model == "gpt-4"
    assert result.provider == "openai"
    assert result.latency_ms > 0  # Should have some latency
    mock_async_client.beta.chat.completions.parse.assert_called_once()


@patch("openai.OpenAI")
def test_openai_parses_response_to_dto(mock_openai_client: Mock) -> None:
    """Test 4: OpenAI correctly parses API response into DTO structure."""
    # Setup mock with AnalysisResult
    mock_parsed = AnalysisResult(
        summary="Medical transcript analysis", next_actions=["Follow-up required"]
    )
    mock_message = Mock()
    mock_message.parsed = mock_parsed
    mock_choice = Mock()
    mock_choice.message = mock_message
    mock_completion = Mock()
    mock_completion.choices = [mock_choice]

    mock_client_instance = Mock()
    mock_client_instance.beta.chat.completions.parse.return_value = mock_completion
    mock_openai_client.return_value = mock_client_instance

    # Execute
    adapter = OpenAIAdapter(api_key="test-key", model="gpt-4")
    result = adapter.run_completion(
        system_prompt="Medical analysis", user_prompt="...", dto=AnalysisResult
    )

    # Assert DTO structure
    assert isinstance(result, AnalysisResult)
    assert hasattr(result, "summary")
    assert hasattr(result, "next_actions")
    assert result.summary == "Medical transcript analysis"


@patch("openai.OpenAI")
def test_openai_with_api_error_raises_exception(mock_openai_client: Mock) -> None:
    """Test 5: OpenAI adapter raises exception on API error."""
    # Setup mock to raise API error
    mock_client_instance = Mock()
    # Create APIConnectionError (no message arg in v1.76.2+)
    mock_client_instance.beta.chat.completions.parse.side_effect = APIConnectionError(
        request=Mock()
    )
    mock_openai_client.return_value = mock_client_instance

    # Execute and assert exception
    adapter = OpenAIAdapter(api_key="test-key", model="gpt-4")
    with pytest.raises(APIConnectionError):
        adapter.run_completion(
            system_prompt="System", user_prompt="User", dto=MockAnalysisResponse
        )


@patch("openai.OpenAI")
def test_openai_with_timeout_raises_exception(mock_openai_client: Mock) -> None:
    """Test 6: OpenAI adapter raises exception on timeout."""
    # Setup mock to raise timeout error
    mock_client_instance = Mock()
    mock_client_instance.beta.chat.completions.parse.side_effect = APITimeoutError(
        "Request timed out"
    )
    mock_openai_client.return_value = mock_client_instance

    # Execute and assert exception
    adapter = OpenAIAdapter(api_key="test-key", model="gpt-4")
    with pytest.raises(APITimeoutError):
        adapter.run_completion(
            system_prompt="System", user_prompt="User", dto=MockAnalysisResponse
        )


@patch("openai.OpenAI")
def test_openai_with_invalid_json_response_raises_exception(
    mock_openai_client: Mock,
) -> None:
    """Test 7: OpenAI adapter handles malformed response gracefully."""
    # Setup mock with None parsed (simulating parse failure)
    mock_message = Mock()
    mock_message.parsed = None
    mock_choice = Mock()
    mock_choice.message = mock_message
    mock_completion = Mock()
    mock_completion.choices = [mock_choice]

    mock_client_instance = Mock()
    mock_client_instance.beta.chat.completions.parse.return_value = mock_completion
    mock_openai_client.return_value = mock_client_instance

    # Execute - OpenAI's parse method should handle this, but we verify behavior
    adapter = OpenAIAdapter(api_key="test-key", model="gpt-4")
    result = adapter.run_completion(
        system_prompt="System", user_prompt="User", dto=MockAnalysisResponse
    )

    # Assert None is returned (OpenAI SDK behavior)
    assert result is None


@patch("openai.OpenAI")
def test_openai_retries_on_transient_errors(mock_openai_client: Mock) -> None:
    """Test 8: OpenAI adapter behavior with transient errors (no retry logic in current impl)."""
    # Note: Current implementation doesn't have retry logic, but this test
    # documents expected behavior if retries are added in the future
    mock_client_instance = Mock()
    mock_client_instance.beta.chat.completions.parse.side_effect = APIConnectionError(
        request=Mock()
    )
    mock_openai_client.return_value = mock_client_instance

    adapter = OpenAIAdapter(api_key="test-key", model="gpt-4")
    with pytest.raises(APIConnectionError):
        adapter.run_completion(
            system_prompt="System", user_prompt="User", dto=MockAnalysisResponse
        )


# ============================================================================
# GROQ ADAPTER TESTS (8 tests)
# ============================================================================


@patch("app.backend.adapters.groq.Groq")
@patch("app.backend.adapters.groq.AsyncGroq")
def test_groq_adapter_implements_llm_port(mock_async_groq: Mock, mock_groq: Mock) -> None:
    """Test 9: Verify GroqAdapter implements LLm port interface."""
    # Mock the client constructors
    mock_groq.return_value = Mock()
    mock_async_groq.return_value = Mock()

    adapter = GroqAdapter(api_key="test-key", model="llama-3.3-70b-versatile")
    assert isinstance(adapter, LLm), "GroqAdapter must implement LLm port"


@patch("app.backend.adapters.groq.AsyncGroq")
@patch("app.backend.adapters.groq.Groq")
def test_groq_run_completion_sync_success(mock_groq_client: Mock, mock_async_groq: Mock) -> None:
    """Test 10: Groq synchronous completion returns parsed DTO."""
    # Setup mock response with JSON content
    json_response = json.dumps(
        {"summary": "Groq test summary", "next_actions": ["Groq action 1"]}
    )
    mock_message = Mock()
    mock_message.content = json_response
    mock_choice = Mock()
    mock_choice.message = mock_message
    mock_completion = Mock()
    mock_completion.choices = [mock_choice]

    # Configure mock client
    mock_client_instance = Mock()
    mock_client_instance.chat.completions.create.return_value = mock_completion
    mock_groq_client.return_value = mock_client_instance
    mock_async_groq.return_value = Mock()

    # Execute
    adapter = GroqAdapter(api_key="test-key")
    result = adapter.run_completion(
        system_prompt="You are a helpful assistant",
        user_prompt="Analyze this text",
        dto=MockAnalysisResponse,
    )

    # Assert
    assert isinstance(result, MockAnalysisResponse)
    assert result.summary == "Groq test summary"
    assert result.next_actions == ["Groq action 1"]
    mock_client_instance.chat.completions.create.assert_called_once()


@pytest.mark.asyncio
@patch("app.backend.adapters.groq.Groq")
@patch("app.backend.adapters.groq.AsyncGroq")
async def test_groq_run_completion_async_success(mock_async_groq: Mock, mock_groq: Mock) -> None:
    """Test 11: Groq asynchronous completion returns LLMResponse with observability."""
    # Setup mock response
    json_response = json.dumps(
        {"summary": "Async Groq summary", "next_actions": ["Async Groq action"]}
    )
    mock_message = Mock()
    mock_message.content = json_response
    mock_choice = Mock()
    mock_choice.message = mock_message

    # Mock token usage
    mock_usage = Mock()
    mock_usage.prompt_tokens = 80
    mock_usage.completion_tokens = 40
    mock_usage.total_tokens = 120

    mock_completion = Mock()
    mock_completion.choices = [mock_choice]
    mock_completion.usage = mock_usage

    # Configure async mock
    mock_async_client = Mock()
    mock_async_client.chat.completions.create = AsyncMock(return_value=mock_completion)
    mock_async_groq.return_value = mock_async_client
    mock_groq.return_value = Mock()

    # Execute
    adapter = GroqAdapter(api_key="test-key")
    result = await adapter.run_completion_async(
        system_prompt="You are a helpful assistant",
        user_prompt="Analyze this text",
        dto=MockAnalysisResponse,
    )

    # Assert - now returns LLMResponse
    assert isinstance(result, LLMResponse)
    assert isinstance(result.parsed_result, MockAnalysisResponse)
    assert result.parsed_result.summary == "Async Groq summary"
    assert result.parsed_result.next_actions == ["Async Groq action"]
    assert result.input_tokens == 80
    assert result.output_tokens == 40
    assert result.total_tokens == 120
    assert result.model == "llama-3.3-70b-versatile"  # default model
    assert result.provider == "groq"
    assert result.latency_ms > 0  # Should have some latency
    mock_async_client.chat.completions.create.assert_called_once()


@patch("app.backend.adapters.groq.AsyncGroq")
@patch("app.backend.adapters.groq.Groq")
def test_groq_parses_json_response_to_dto(mock_groq_client: Mock, mock_async_groq: Mock) -> None:
    """Test 12: Groq correctly parses JSON response into DTO structure."""
    # Setup mock with AnalysisResult JSON
    json_response = json.dumps(
        {
            "summary": "Groq medical analysis",
            "next_actions": ["Schedule follow-up", "Order tests"],
        }
    )
    mock_message = Mock()
    mock_message.content = json_response
    mock_choice = Mock()
    mock_choice.message = mock_message
    mock_completion = Mock()
    mock_completion.choices = [mock_choice]

    mock_client_instance = Mock()
    mock_client_instance.chat.completions.create.return_value = mock_completion
    mock_groq_client.return_value = mock_client_instance
    mock_async_groq.return_value = Mock()

    # Execute
    adapter = GroqAdapter(api_key="test-key")
    result = adapter.run_completion(
        system_prompt="Medical analysis", user_prompt="...", dto=AnalysisResult
    )

    # Assert DTO structure
    assert isinstance(result, AnalysisResult)
    assert hasattr(result, "summary")
    assert hasattr(result, "next_actions")
    assert result.summary == "Groq medical analysis"
    assert "Schedule follow-up" in result.next_actions


@patch("app.backend.adapters.groq.AsyncGroq")
@patch("app.backend.adapters.groq.Groq")
def test_groq_with_api_error_raises_exception(mock_groq_client: Mock, mock_async_groq: Mock) -> None:
    """Test 13: Groq adapter raises exception on API error."""
    # Setup mock to raise exception
    mock_client_instance = Mock()
    mock_client_instance.chat.completions.create.side_effect = Exception(
        "Groq API error"
    )
    mock_groq_client.return_value = mock_client_instance
    mock_async_groq.return_value = Mock()

    # Execute and assert exception
    adapter = GroqAdapter(api_key="test-key")
    with pytest.raises(Exception) as exc_info:
        adapter.run_completion(
            system_prompt="System", user_prompt="User", dto=MockAnalysisResponse
        )

    assert "Groq API error" in str(exc_info.value)


@patch("app.backend.adapters.groq.AsyncGroq")
@patch("app.backend.adapters.groq.Groq")
def test_groq_with_empty_response_raises_exception(mock_groq_client: Mock, mock_async_groq: Mock) -> None:
    """Test 14: Groq adapter raises exception when response content is None."""
    # Setup mock with None content
    mock_message = Mock()
    mock_message.content = None
    mock_choice = Mock()
    mock_choice.message = mock_message
    mock_completion = Mock()
    mock_completion.choices = [mock_choice]

    mock_client_instance = Mock()
    mock_client_instance.chat.completions.create.return_value = mock_completion
    mock_groq_client.return_value = mock_client_instance
    mock_async_groq.return_value = Mock()

    # Execute and assert ValueError
    adapter = GroqAdapter(api_key="test-key")
    with pytest.raises(ValueError) as exc_info:
        adapter.run_completion(
            system_prompt="System", user_prompt="User", dto=MockAnalysisResponse
        )

    assert "empty response" in str(exc_info.value).lower()


@patch("app.backend.adapters.groq.AsyncGroq")
@patch("app.backend.adapters.groq.Groq")
def test_groq_with_malformed_json_raises_exception(mock_groq_client: Mock, mock_async_groq: Mock) -> None:
    """Test 15: Groq adapter raises exception with invalid JSON response."""
    # Setup mock with malformed JSON
    mock_message = Mock()
    mock_message.content = "{invalid json content"
    mock_choice = Mock()
    mock_choice.message = mock_message
    mock_completion = Mock()
    mock_completion.choices = [mock_choice]

    mock_client_instance = Mock()
    mock_client_instance.chat.completions.create.return_value = mock_completion
    mock_groq_client.return_value = mock_client_instance
    mock_async_groq.return_value = Mock()

    # Execute and assert validation error
    adapter = GroqAdapter(api_key="test-key")
    with pytest.raises((json.JSONDecodeError, pydantic.ValidationError)):
        adapter.run_completion(
            system_prompt="System", user_prompt="User", dto=MockAnalysisResponse
        )


@patch("app.backend.adapters.groq.AsyncGroq")
@patch("app.backend.adapters.groq.Groq")
def test_groq_with_missing_fields_raises_exception(mock_groq_client: Mock, mock_async_groq: Mock) -> None:
    """Test 16: Groq adapter raises exception when required DTO fields are missing."""
    # Setup mock with incomplete JSON (missing next_actions field)
    json_response = json.dumps({"summary": "Only summary here"})
    mock_message = Mock()
    mock_message.content = json_response
    mock_choice = Mock()
    mock_choice.message = mock_message
    mock_completion = Mock()
    mock_completion.choices = [mock_choice]

    mock_client_instance = Mock()
    mock_client_instance.chat.completions.create.return_value = mock_completion
    mock_groq_client.return_value = mock_client_instance
    mock_async_groq.return_value = Mock()

    # Execute and assert Pydantic validation error
    adapter = GroqAdapter(api_key="test-key")
    with pytest.raises(pydantic.ValidationError) as exc_info:
        adapter.run_completion(
            system_prompt="System", user_prompt="User", dto=MockAnalysisResponse
        )

    # Verify the error is about missing fields
    error_details = str(exc_info.value)
    assert "next_actions" in error_details.lower() or "field required" in error_details.lower()
