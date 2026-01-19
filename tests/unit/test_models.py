"""
Unit tests for Pydantic request models.

Tests validation logic for AnalyzeTranscriptRequest and BatchAnalyzeRequest,
including field constraints and custom validators.
"""

import pytest
from pydantic import ValidationError

from app.models.requests import AnalyzeTranscriptRequest, BatchAnalyzeRequest


class TestAnalyzeTranscriptRequest:
    """Test suite for AnalyzeTranscriptRequest validation."""

    def test_analyze_request_with_valid_transcript_succeeds(self):
        """Should accept a valid transcript within length constraints."""
        # Arrange
        valid_transcript = "Patient reports persistent headaches for 3 days."

        # Act
        request = AnalyzeTranscriptRequest(transcript=valid_transcript)

        # Assert
        assert request.transcript == valid_transcript

    def test_analyze_request_strips_whitespace(self):
        """Should strip leading and trailing whitespace from transcript."""
        # Arrange
        transcript_with_whitespace = "  Patient has fever and cough.  \n\t"

        # Act
        request = AnalyzeTranscriptRequest(transcript=transcript_with_whitespace)

        # Assert
        assert request.transcript == "Patient has fever and cough."
        assert not request.transcript.startswith(" ")
        assert not request.transcript.endswith(" ")

    def test_analyze_request_with_too_short_fails(self):
        """Should reject transcript shorter than 10 characters."""
        # Arrange
        too_short = "Too short"  # 9 characters

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            AnalyzeTranscriptRequest(transcript=too_short)

        # Verify error message mentions length constraint
        error = exc_info.value
        assert "at least 10 characters" in str(error).lower()

    def test_analyze_request_with_too_long_fails(self):
        """Should reject transcript longer than 10000 characters."""
        # Arrange
        too_long = "x" * 10001  # 10001 characters (max is 10000)

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            AnalyzeTranscriptRequest(transcript=too_long)

        # Verify error message mentions length constraint
        error = exc_info.value
        assert "at most 10000 characters" in str(error).lower()

    def test_analyze_request_with_empty_string_fails(self):
        """Should reject empty string transcript."""
        # Arrange
        empty_transcript = ""

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            AnalyzeTranscriptRequest(transcript=empty_transcript)

        # Verify error mentions empty/length constraint
        error = exc_info.value
        assert any(
            keyword in str(error).lower()
            for keyword in ["at least", "empty", "whitespace"]
        )

    def test_analyze_request_with_whitespace_only_fails(self):
        """Should reject transcript with only whitespace characters."""
        # Arrange - Use whitespace-only string longer than min_length (10 chars)
        # so it passes min_length validator and reaches custom whitespace validator
        whitespace_only = "   \n\t   \n  \t "  # 14 chars of whitespace

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            AnalyzeTranscriptRequest(transcript=whitespace_only)

        # Verify error message is about empty/whitespace
        error = exc_info.value
        assert "empty or whitespace only" in str(error).lower()

    def test_analyze_request_with_default_num_next_actions(self):
        """Should default num_next_actions to 3."""
        # Arrange
        transcript = "Patient reports headaches for 3 days."

        # Act
        request = AnalyzeTranscriptRequest(transcript=transcript)

        # Assert
        assert request.num_next_actions == 3

    def test_analyze_request_with_custom_num_next_actions(self):
        """Should accept custom num_next_actions within valid range."""
        # Arrange
        transcript = "Patient reports headaches for 3 days."

        # Act
        request = AnalyzeTranscriptRequest(transcript=transcript, num_next_actions=5)

        # Assert
        assert request.num_next_actions == 5

    def test_analyze_request_with_num_next_actions_below_min_fails(self):
        """Should reject num_next_actions below 1."""
        # Arrange
        transcript = "Patient reports headaches for 3 days."

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            AnalyzeTranscriptRequest(transcript=transcript, num_next_actions=0)

        error = exc_info.value
        assert "greater than or equal to 1" in str(error).lower()

    def test_analyze_request_with_num_next_actions_above_max_fails(self):
        """Should reject num_next_actions above 10."""
        # Arrange
        transcript = "Patient reports headaches for 3 days."

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            AnalyzeTranscriptRequest(transcript=transcript, num_next_actions=11)

        error = exc_info.value
        assert "less than or equal to 10" in str(error).lower()


class TestBatchAnalyzeRequest:
    """Test suite for BatchAnalyzeRequest validation."""

    def test_batch_request_with_valid_transcripts_succeeds(self):
        """Should accept a valid list of transcripts within constraints."""
        # Arrange
        valid_transcripts = [
            "Patient A has persistent headaches for 3 days.",
            "Patient B reports chest pain and shortness of breath.",
            "Patient C presents with fever and cough for 5 days.",
        ]

        # Act
        request = BatchAnalyzeRequest(transcripts=valid_transcripts)

        # Assert
        assert len(request.transcripts) == 3
        assert all(isinstance(t, str) for t in request.transcripts)
        # Verify whitespace was stripped
        assert request.transcripts[0] == valid_transcripts[0].strip()

    def test_batch_request_with_empty_list_fails(self):
        """Should reject empty list of transcripts (min_length=1)."""
        # Arrange
        empty_list = []

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            BatchAnalyzeRequest(transcripts=empty_list)

        # Verify error mentions list constraint
        error = exc_info.value
        assert "at least 1" in str(error).lower()

    def test_batch_request_with_over_limit_fails(self):
        """Should reject list with more than 100 transcripts (max_length=100)."""
        # Arrange
        over_limit = ["Patient has symptoms for days." for _ in range(101)]

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            BatchAnalyzeRequest(transcripts=over_limit)

        # Verify error mentions max constraint
        error = exc_info.value
        assert "at most 100" in str(error).lower()

    def test_batch_request_with_one_too_short_transcript_fails(self):
        """Should reject if any transcript is shorter than 10 characters."""
        # Arrange
        transcripts_with_short = [
            "Patient A has persistent headaches for 3 days.",
            "Too short",  # 9 characters - violates minimum
            "Patient C presents with fever and cough for 5 days.",
        ]

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            BatchAnalyzeRequest(transcripts=transcripts_with_short)

        # Verify error mentions the index and length requirement
        error = exc_info.value
        error_str = str(error).lower()
        assert "index 1" in error_str
        assert "too short" in error_str or "minimum 10" in error_str

    def test_batch_request_with_default_num_next_actions(self):
        """Should default num_next_actions to 3."""
        # Arrange
        transcripts = [
            "Patient A has persistent headaches for 3 days.",
            "Patient B reports chest pain and shortness of breath.",
        ]

        # Act
        request = BatchAnalyzeRequest(transcripts=transcripts)

        # Assert
        assert request.num_next_actions == 3

    def test_batch_request_with_custom_num_next_actions(self):
        """Should accept custom num_next_actions within valid range."""
        # Arrange
        transcripts = [
            "Patient A has persistent headaches for 3 days.",
            "Patient B reports chest pain and shortness of breath.",
        ]

        # Act
        request = BatchAnalyzeRequest(transcripts=transcripts, num_next_actions=7)

        # Assert
        assert request.num_next_actions == 7

    def test_batch_request_with_num_next_actions_below_min_fails(self):
        """Should reject num_next_actions below 1."""
        # Arrange
        transcripts = ["Patient A has persistent headaches for 3 days."]

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            BatchAnalyzeRequest(transcripts=transcripts, num_next_actions=0)

        error = exc_info.value
        assert "greater than or equal to 1" in str(error).lower()

    def test_batch_request_with_num_next_actions_above_max_fails(self):
        """Should reject num_next_actions above 10."""
        # Arrange
        transcripts = ["Patient A has persistent headaches for 3 days."]

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            BatchAnalyzeRequest(transcripts=transcripts, num_next_actions=11)

        error = exc_info.value
        assert "less than or equal to 10" in str(error).lower()
