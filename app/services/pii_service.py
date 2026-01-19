"""
PII Detection and Anonymization Service.

Implements comprehensive PII detection using Microsoft Presidio to identify and mask
sensitive information before sending transcripts to LLM providers.
"""

from typing import Any

from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig

from app.core.logging import get_logger

logger = get_logger(__name__)


class PIIDetectionResult:
    """Result of PII detection analysis."""

    def __init__(
        self,
        original_text: str,
        anonymized_text: str,
        pii_detected: bool,
        entities_found: list[dict[str, Any]],
    ) -> None:
        """
        Initialize PII detection result.

        Args:
            original_text: Original input text
            anonymized_text: Text with PII entities masked
            pii_detected: Whether any PII was found
            entities_found: List of detected PII entities with metadata
        """
        self.original_text = original_text
        self.anonymized_text = anonymized_text
        self.pii_detected = pii_detected
        self.entities_found = entities_found


class PIIService:
    """
    Service for detecting and anonymizing Personally Identifiable Information (PII).

    Uses Microsoft Presidio to detect sensitive information including:
    - Names (PERSON)
    - Email addresses (EMAIL_ADDRESS)
    - Phone numbers (PHONE_NUMBER)
    - Social Security Numbers (US_SSN)
    - Credit card numbers (CREDIT_CARD)
    - IP addresses (IP_ADDRESS)
    - Locations (LOCATION)
    - Medical data (MEDICAL_LICENSE, etc.)
    - Financial data (IBAN_CODE, etc.)

    The service masks detected PII with placeholder values like <PERSON>, <EMAIL>, etc.
    """

    def __init__(self, enabled: bool = True) -> None:
        """
        Initialize PII detection service.

        Args:
            enabled: Whether PII detection is enabled (can be disabled for testing)
        """
        self.enabled = enabled
        self.analyzer: AnalyzerEngine | None = None
        self.anonymizer: AnonymizerEngine | None = None

        if self.enabled:
            self._initialize_engines()

    def _initialize_engines(self) -> None:
        """Initialize Presidio analyzer and anonymizer engines."""
        try:
            logger.info("pii_service_init", message="Initializing Presidio engines")

            # Initialize analyzer with support for multiple languages
            # Presidio will auto-detect available spaCy models (prefers smaller models first)
            # Supports: en_core_web_sm (12MB), en_core_web_md, en_core_web_lg (382MB)
            self.analyzer = AnalyzerEngine()

            # Initialize anonymizer
            self.anonymizer = AnonymizerEngine()

            logger.info(
                "pii_service_ready",
                message="Presidio engines initialized successfully",
                supported_entities=self.analyzer.get_supported_entities(),
            )
        except Exception as e:
            logger.error(
                "pii_service_init_failed",
                message="Failed to initialize Presidio engines",
                error=str(e),
            )
            # Disable the service if initialization fails
            self.enabled = False
            raise

    def detect_and_anonymize(
        self,
        text: str,
        language: str = "en",
        score_threshold: float = 0.5,
    ) -> PIIDetectionResult:
        """
        Detect and anonymize PII in the provided text.

        Args:
            text: Input text to analyze
            language: Language code (default: "en" for English)
            score_threshold: Minimum confidence score for PII detection (0.0-1.0)

        Returns:
            PIIDetectionResult: Detection results with anonymized text

        Raises:
            RuntimeError: If Presidio engines are not initialized
        """
        if not self.enabled:
            logger.debug(
                "pii_detection_disabled",
                message="PII detection is disabled, returning original text",
            )
            return PIIDetectionResult(
                original_text=text,
                anonymized_text=text,
                pii_detected=False,
                entities_found=[],
            )

        if not self.analyzer or not self.anonymizer:
            raise RuntimeError("Presidio engines not initialized")

        try:
            # Analyze text for PII entities
            results = self.analyzer.analyze(
                text=text,
                language=language,
                score_threshold=score_threshold,
            )

            pii_detected = len(results) > 0

            if pii_detected:
                # Log detected PII types (not the actual values for security)
                entity_types = [result.entity_type for result in results]
                logger.warning(
                    "pii_detected",
                    message="PII entities detected in transcript",
                    entity_types=entity_types,
                    entity_count=len(results),
                )

                # Anonymize detected PII with placeholder tags
                anonymized_result = self.anonymizer.anonymize(
                    text=text,
                    analyzer_results=results,
                    operators={
                        "DEFAULT": OperatorConfig("replace", {"new_value": "<PII>"}),
                        "PERSON": OperatorConfig("replace", {"new_value": "<PERSON>"}),
                        "EMAIL_ADDRESS": OperatorConfig(
                            "replace", {"new_value": "<EMAIL>"}
                        ),
                        "PHONE_NUMBER": OperatorConfig("replace", {"new_value": "<PHONE>"}),
                        "US_SSN": OperatorConfig("replace", {"new_value": "<SSN>"}),
                        "CREDIT_CARD": OperatorConfig(
                            "replace", {"new_value": "<CREDIT_CARD>"}
                        ),
                        "IP_ADDRESS": OperatorConfig("replace", {"new_value": "<IP>"}),
                        "LOCATION": OperatorConfig("replace", {"new_value": "<LOCATION>"}),
                        "DATE_TIME": OperatorConfig(
                            "replace", {"new_value": "<DATE_TIME>"}
                        ),
                    },
                )

                anonymized_text = anonymized_result.text
            else:
                anonymized_text = text
                logger.debug(
                    "pii_not_detected",
                    message="No PII detected in transcript",
                )

            # Format entity metadata for logging/auditing
            entities_found = [
                {
                    "entity_type": result.entity_type,
                    "start": result.start,
                    "end": result.end,
                    "score": result.score,
                }
                for result in results
            ]

            return PIIDetectionResult(
                original_text=text,
                anonymized_text=anonymized_text,
                pii_detected=pii_detected,
                entities_found=entities_found,
            )

        except Exception as e:
            logger.error(
                "pii_detection_error",
                message="Error during PII detection",
                error=str(e),
            )
            # On error, return original text but log the failure
            return PIIDetectionResult(
                original_text=text,
                anonymized_text=text,
                pii_detected=False,
                entities_found=[],
            )

    def validate_no_pii(self, text: str, score_threshold: float = 0.5) -> bool:
        """
        Validate that text contains no PII above the threshold.

        Args:
            text: Text to validate
            score_threshold: Minimum confidence score for PII detection

        Returns:
            bool: True if no PII detected, False otherwise
        """
        if not self.enabled:
            return True

        result = self.detect_and_anonymize(text, score_threshold=score_threshold)
        return not result.pii_detected
