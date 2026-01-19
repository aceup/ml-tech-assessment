"""
Guardrails Service for LLM Input/Output Validation.

Implements token counting, content validation, and output sanitization
to prevent abuse and ensure safe LLM interactions.
"""

import json
import re
from typing import Any

import tiktoken

from app.backend.core.logging import get_logger

logger = get_logger(__name__)


class TokenLimitExceededError(Exception):
    """Raised when input or output exceeds token limits."""

    pass


class InvalidOutputError(Exception):
    """Raised when LLM output fails validation."""

    pass


class GuardrailsService:
    """
    Service for enforcing guardrails on LLM inputs and outputs.

    Responsibilities:
    - Token counting and limit enforcement
    - Input validation (length, format, suspicious patterns)
    - Output validation (format, completeness, safety)
    - Content sanitization
    """

    def __init__(
        self,
        max_input_tokens: int = 100000,
        max_output_tokens: int = 4000,
        encoding_name: str = "cl100k_base",  # GPT-4, GPT-3.5-turbo
    ) -> None:
        """
        Initialize guardrails service.

        Args:
            max_input_tokens: Maximum allowed tokens in input
            max_output_tokens: Maximum allowed tokens in output
            encoding_name: Tiktoken encoding to use (cl100k_base for GPT-4/3.5)
        """
        self.max_input_tokens = max_input_tokens
        self.max_output_tokens = max_output_tokens

        try:
            self.encoding = tiktoken.get_encoding(encoding_name)
            logger.info(
                "guardrails_init",
                message="Guardrails service initialized",
                encoding=encoding_name,
                max_input_tokens=max_input_tokens,
                max_output_tokens=max_output_tokens,
            )
        except Exception as e:
            logger.error(
                "guardrails_init_failed",
                message="Failed to initialize tiktoken encoding",
                error=str(e),
            )
            raise

    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text using tiktoken.

        Args:
            text: Input text to count tokens

        Returns:
            int: Number of tokens
        """
        try:
            tokens = self.encoding.encode(text)
            return len(tokens)
        except Exception as e:
            logger.warning(
                "token_count_error",
                message="Error counting tokens, using character-based estimate",
                error=str(e),
            )
            # Fallback: rough estimate (1 token ≈ 4 characters)
            return len(text) // 4

    def validate_input(self, text: str) -> tuple[bool, str | None]:
        """
        Validate input text before sending to LLM.

        Checks:
        - Token count within limits
        - Not empty
        - No excessively long lines (potential injection)
        - Reasonable character distribution

        Args:
            text: Input text to validate

        Returns:
            tuple: (is_valid, error_message)
        """
        # Check if empty
        if not text or not text.strip():
            return False, "Input text is empty"

        # Count tokens
        token_count = self.count_tokens(text)
        logger.debug(
            "input_validation",
            message="Validating input",
            token_count=token_count,
            max_tokens=self.max_input_tokens,
        )

        if token_count > self.max_input_tokens:
            logger.warning(
                "input_token_limit_exceeded",
                message="Input exceeds token limit",
                token_count=token_count,
                max_tokens=self.max_input_tokens,
            )
            return (
                False,
                f"Input exceeds token limit: {token_count} > {self.max_input_tokens}",
            )

        # Check for excessively long lines (potential prompt injection)
        lines = text.split("\n")
        max_line_length = 10000  # characters
        for i, line in enumerate(lines):
            if len(line) > max_line_length:
                logger.warning(
                    "suspicious_input_detected",
                    message="Input contains excessively long line",
                    line_number=i + 1,
                    line_length=len(line),
                )
                return (
                    False,
                    f"Line {i + 1} exceeds maximum length ({len(line)} > {max_line_length})",
                )

        # Check character distribution (detect potential binary/garbage data)
        if len(text) > 100:  # Only for non-trivial inputs
            printable_ratio = sum(c.isprintable() or c.isspace() for c in text) / len(text)
            if printable_ratio < 0.9:
                logger.warning(
                    "suspicious_input_detected",
                    message="Input contains high ratio of non-printable characters",
                    printable_ratio=printable_ratio,
                )
                return False, "Input contains too many non-printable characters"

        return True, None

    def validate_output(
        self,
        output: str,
        expected_format: str = "json",
    ) -> tuple[bool, str | None, Any]:
        """
        Validate LLM output.

        Checks:
        - Token count within limits
        - Expected format (JSON, plain text, etc.)
        - No obvious errors or refusals
        - Content completeness

        Args:
            output: LLM output text
            expected_format: Expected output format ("json" or "text")

        Returns:
            tuple: (is_valid, error_message, parsed_data)
        """
        # Check if empty
        if not output or not output.strip():
            return False, "Output is empty", None

        # Count tokens
        token_count = self.count_tokens(output)
        logger.debug(
            "output_validation",
            message="Validating output",
            token_count=token_count,
            max_tokens=self.max_output_tokens,
            expected_format=expected_format,
        )

        if token_count > self.max_output_tokens:
            logger.warning(
                "output_token_limit_exceeded",
                message="Output exceeds token limit",
                token_count=token_count,
                max_tokens=self.max_output_tokens,
            )
            return (
                False,
                f"Output exceeds token limit: {token_count} > {self.max_output_tokens}",
                None,
            )

        # Validate format
        if expected_format == "json":
            return self._validate_json_output(output)
        else:
            return True, None, output

    def _validate_json_output(self, output: str) -> tuple[bool, str | None, Any]:
        """
        Validate JSON output from LLM.

        Args:
            output: LLM output text expected to be JSON

        Returns:
            tuple: (is_valid, error_message, parsed_json)
        """
        # Clean common markdown artifacts
        cleaned_output = self._clean_json_output(output)

        # Try to parse JSON
        try:
            parsed = json.loads(cleaned_output)
            logger.debug(
                "json_validation_success",
                message="Successfully parsed JSON output",
            )
            return True, None, parsed

        except json.JSONDecodeError as e:
            logger.error(
                "json_validation_failed",
                message="Failed to parse JSON output",
                error=str(e),
                output_preview=output[:200],
            )
            return False, f"Invalid JSON output: {str(e)}", None

    def _clean_json_output(self, output: str) -> str:
        """
        Clean LLM output to extract JSON content.

        Removes common artifacts:
        - Markdown code blocks (```json ... ```)
        - Leading/trailing whitespace
        - Explanatory text before/after JSON

        Args:
            output: Raw LLM output

        Returns:
            str: Cleaned JSON string
        """
        # Remove markdown code blocks
        output = re.sub(r"```json\s*", "", output)
        output = re.sub(r"```\s*$", "", output)
        output = output.strip()

        # Try to extract JSON object/array if surrounded by text
        json_match = re.search(r"(\{.*\}|\[.*\])", output, re.DOTALL)
        if json_match:
            output = json_match.group(1)

        return output

    def check_suspicious_patterns(self, text: str) -> list[str]:
        """
        Check for suspicious patterns that might indicate prompt injection or abuse.

        Args:
            text: Text to check

        Returns:
            list[str]: List of detected suspicious patterns
        """
        suspicious_patterns = []

        # Check for instruction-like language
        instruction_keywords = [
            r"ignore\s+(previous|all|above)\s+instructions",
            r"disregard\s+(previous|all|above)",
            r"forget\s+(everything|previous|all)",
            r"system\s*:\s*you\s+are",
            r"new\s+instructions",
            r"from\s+now\s+on",
            r"instead\s*,?\s+(do|return|output)",
        ]

        for pattern in instruction_keywords:
            if re.search(pattern, text, re.IGNORECASE):
                suspicious_patterns.append(f"Instruction-like pattern: {pattern}")

        # Check for excessive repetition (potential token stuffing)
        words = text.split()
        if len(words) > 50:
            # Check for repeated 3-word phrases
            phrases = [" ".join(words[i : i + 3]) for i in range(len(words) - 2)]
            phrase_counts = {}
            for phrase in phrases:
                phrase_counts[phrase] = phrase_counts.get(phrase, 0) + 1

            max_repetition = max(phrase_counts.values()) if phrase_counts else 0
            if max_repetition > 5:
                suspicious_patterns.append(f"Excessive repetition detected: {max_repetition}x")

        # Check for base64-encoded content (potential data exfiltration)
        base64_pattern = r"[A-Za-z0-9+/]{50,}={0,2}"
        base64_matches = re.findall(base64_pattern, text)
        if len(base64_matches) > 3:
            suspicious_patterns.append(
                f"Multiple base64-like strings detected: {len(base64_matches)}"
            )

        if suspicious_patterns:
            logger.warning(
                "suspicious_patterns_detected",
                message="Suspicious patterns found in input",
                patterns=suspicious_patterns,
            )

        return suspicious_patterns

    def sanitize_for_logging(self, text: str, max_length: int = 200) -> str:
        """
        Sanitize text for safe logging (truncate and remove sensitive patterns).

        Args:
            text: Text to sanitize
            max_length: Maximum length for output

        Returns:
            str: Sanitized text safe for logging
        """
        # Truncate
        if len(text) > max_length:
            text = text[:max_length] + "..."

        # Replace potential sensitive patterns with placeholders
        # Email
        text = re.sub(
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
            "<EMAIL>",
            text,
        )
        # Phone (simple pattern)
        text = re.sub(r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b", "<PHONE>", text)
        # SSN pattern
        text = re.sub(r"\b\d{3}-\d{2}-\d{4}\b", "<SSN>", text)

        return text
