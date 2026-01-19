"""
Analysis service for transcript processing.

Orchestrates the business logic for analyzing transcripts using LLM.
Includes security layers: PII detection, input/output validation, content moderation.
"""

import uuid
from datetime import UTC, datetime

from pydantic import BaseModel, Field, field_validator

from app.adapters.openai import OpenAIAdapter
from app.core.logging import get_logger
from app.models.responses import AnalysisResponse
from app.ports.llm import LLm
from app.prompts import RAW_USER_PROMPT, SYSTEM_PROMPT
from app.repositories.in_memory import InMemoryAnalysisRepository
from app.services.guardrails_service import GuardrailsService, TokenLimitExceededError
from app.services.pii_service import PIIService
from app.utils.exceptions import ExternalServiceException, ValidationException

logger = get_logger(__name__)


class LLMAnalysisResult(BaseModel):
    """DTO for LLM response structure."""

    summary: str = Field(
        ...,
        description="Concise summary of the transcript",
    )
    next_actions: list[str] = Field(
        ...,
        min_length=1,
        max_length=10,
        description="List of recommended next actions",
    )

    @field_validator("next_actions")
    @classmethod
    def validate_actions_not_empty(cls, v: list[str]) -> list[str]:
        """Ensure all actions are non-empty strings."""
        if not v:
            raise ValueError("next_actions cannot be empty")

        cleaned = []
        for i, action in enumerate(v):
            stripped = action.strip()
            if not stripped:
                raise ValueError(f"Action at index {i} is empty")
            cleaned.append(stripped)

        return cleaned


class AnalysisService:
    """
    Service for analyzing transcripts.

    Coordinates between the LLM adapter, repository, and security services.
    Implements multi-layer security: PII detection, guardrails, content moderation.
    """

    def __init__(
        self,
        llm_adapter: LLm,
        repository: InMemoryAnalysisRepository,
        pii_service: PIIService | None = None,
        guardrails_service: GuardrailsService | None = None,
        enable_moderation: bool = True,
    ):
        """
        Initialize analysis service with security layers.

        Args:
            llm_adapter: LLM adapter (OpenAI or Groq)
            repository: Storage repository
            pii_service: PII detection service (optional, created if None)
            guardrails_service: Guardrails validation service (optional, created if None)
            enable_moderation: Enable content moderation (OpenAI only)
        """
        self.llm_adapter = llm_adapter
        self.repository = repository
        self.pii_service = pii_service
        self.guardrails_service = guardrails_service
        self.enable_moderation = enable_moderation

        logger.info(
            "analysis_service_init",
            message="Analysis service initialized",
            pii_enabled=pii_service is not None and pii_service.enabled,
            guardrails_enabled=guardrails_service is not None,
            moderation_enabled=enable_moderation,
        )

    async def analyze(self, transcript: str, num_next_actions: int = 3) -> AnalysisResponse:
        """
        Analyze a single transcript with multi-layer security.

        Security Layers:
        1. Basic validation (empty, length)
        2. PII detection and anonymization
        3. Guardrails input validation (token limits, suspicious patterns)
        4. LLM processing
        5. Guardrails output validation
        6. Content moderation (if enabled)

        Args:
            transcript: Text transcript to analyze
            num_next_actions: Number of next action items to generate (1-10)

        Returns:
            Analysis result with summary and next actions

        Raises:
            ValidationException: If transcript is invalid or fails security checks
            ExternalServiceException: If LLM API fails
        """
        # Validate inputs
        if not transcript or not transcript.strip():
            raise ValidationException("Transcript cannot be empty")

        if not 1 <= num_next_actions <= 10:
            raise ValidationException(
                f"num_next_actions must be between 1 and 10, got {num_next_actions}"
            )

        # Generate unique ID
        analysis_id = str(uuid.uuid4())

        logger.info(
            "analysis_started",
            analysis_id=analysis_id,
            transcript_length=len(transcript),
            num_next_actions=num_next_actions,
        )

        try:
            # SECURITY LAYER 1: PII Detection & Anonymization
            processed_transcript = transcript
            if self.pii_service:
                pii_result = self.pii_service.detect_and_anonymize(transcript)
                if pii_result.pii_detected:
                    logger.warning(
                        "pii_found_in_transcript",
                        analysis_id=analysis_id,
                        entity_count=len(pii_result.entities_found),
                        entity_types=[e["entity_type"] for e in pii_result.entities_found],
                    )
                    # Use anonymized version for LLM
                    processed_transcript = pii_result.anonymized_text

            # SECURITY LAYER 2: Input Validation with Guardrails
            if self.guardrails_service:
                # Validate input
                is_valid, error_msg = self.guardrails_service.validate_input(
                    processed_transcript
                )
                if not is_valid:
                    logger.error(
                        "input_validation_failed",
                        analysis_id=analysis_id,
                        error=error_msg,
                    )
                    raise ValidationException(f"Input validation failed: {error_msg}")

                # Check for suspicious patterns
                suspicious = self.guardrails_service.check_suspicious_patterns(
                    processed_transcript
                )
                if suspicious:
                    logger.warning(
                        "suspicious_input_patterns",
                        analysis_id=analysis_id,
                        patterns=suspicious,
                    )
                    # Log but don't block (XML delimiters handle injection)

            # Format prompts with both transcript AND num_next_actions
            user_prompt = RAW_USER_PROMPT.format(
                transcript=processed_transcript,
                num_next_actions=num_next_actions,
            )
            system_prompt = SYSTEM_PROMPT.format(num_next_actions=num_next_actions)

            # SECURITY LAYER 3: LLM Processing
            result = await self.llm_adapter.run_completion_async(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                dto=LLMAnalysisResult,
            )

            # SECURITY LAYER 4: Output Validation
            if self.guardrails_service:
                # Convert result to JSON string for validation
                result_json = result.model_dump_json()
                is_valid, error_msg, _ = self.guardrails_service.validate_output(
                    result_json, expected_format="json"
                )
                if not is_valid:
                    logger.error(
                        "output_validation_failed",
                        analysis_id=analysis_id,
                        error=error_msg,
                    )
                    raise ValidationException(f"Output validation failed: {error_msg}")

            # SECURITY LAYER 5: Content Moderation (OpenAI only)
            if self.enable_moderation and isinstance(self.llm_adapter, OpenAIAdapter):
                combined_output = f"{result.summary} {' '.join(result.next_actions)}"
                is_safe, mod_results = await self.llm_adapter.moderate_content_async(
                    combined_output
                )
                if not is_safe:
                    logger.error(
                        "content_moderation_failed",
                        analysis_id=analysis_id,
                        moderation_results=mod_results,
                    )
                    raise ValidationException(
                        "Generated content failed moderation check (inappropriate content)"
                    )

            # Validate LLM returned correct count
            if len(result.next_actions) != num_next_actions:
                logger.warning(
                    "llm_action_count_mismatch",
                    analysis_id=analysis_id,
                    requested=num_next_actions,
                    received=len(result.next_actions),
                )
                # Truncate if too many
                if len(result.next_actions) > num_next_actions:
                    result.next_actions = result.next_actions[:num_next_actions]
                # Accept fewer if LLM couldn't generate more

            # Create response (store original transcript, not anonymized)
            analysis = AnalysisResponse(
                id=analysis_id,
                summary=result.summary,
                next_actions=result.next_actions,
                created_at=datetime.now(UTC),
                transcript=transcript,  # Store original, not anonymized
            )

            # Save to repository
            self.repository.save(analysis)

            logger.info(
                "analysis_completed",
                analysis_id=analysis_id,
                action_count=len(result.next_actions),
            )

            return analysis

        except ValidationException:
            # Re-raise ValidationException as-is
            raise

        except TokenLimitExceededError as exc:
            logger.error(
                "token_limit_exceeded",
                analysis_id=analysis_id,
                error=str(exc),
            )
            raise ValidationException(f"Token limit exceeded: {str(exc)}")

        except ExternalServiceException:
            # Re-raise ExternalServiceException as-is (already properly formatted)
            raise

        except Exception as exc:
            logger.error(
                "analysis_failed",
                analysis_id=analysis_id,
                error=str(exc),
                error_type=type(exc).__name__,
            )

            # Wrap all other LLM adapter exceptions as ExternalServiceException
            # Detect service name from exception type or use generic "LLM"
            exc_type_lower = str(type(exc)).lower()
            if "openai" in exc_type_lower:
                service_name = "OpenAI"
            elif "groq" in exc_type_lower:
                service_name = "Groq"
            else:
                service_name = "LLM"

            raise ExternalServiceException(
                service=service_name,
                message=str(exc),
                details={"analysis_id": analysis_id},
            )

    def get_by_id(self, analysis_id: str) -> AnalysisResponse:
        """
        Retrieve an analysis by ID.

        Args:
            analysis_id: Unique identifier

        Returns:
            Analysis result

        Raises:
            NotFoundException: If analysis not found
        """
        return self.repository.get_by_id(analysis_id)

    def list_all(self) -> list[AnalysisResponse]:
        """
        List all analyses.

        Returns:
            List of all stored analyses
        """
        return self.repository.list_all()
