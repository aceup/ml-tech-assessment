"""
API request models using Pydantic.

Defines the structure and validation for incoming API requests.
"""

from pydantic import BaseModel, Field, field_validator


class AnalyzeTranscriptRequest(BaseModel):
    """Request model for single transcript analysis."""

    transcript: str = Field(
        ...,
        min_length=10,
        max_length=10000,
        description="Medical transcript text to analyze",
        examples=[
            "Patient reports persistent headaches for 3 days, worse in the morning. "
            "No fever or visual disturbances. Taking ibuprofen with minimal relief."
        ],
    )

    num_next_actions: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Number of next action items to generate (1-10)",
    )

    @field_validator("transcript")
    @classmethod
    def transcript_not_empty(cls, v: str) -> str:
        """Ensure transcript is not just whitespace."""
        if not v.strip():
            raise ValueError("Transcript cannot be empty or whitespace only")
        return v.strip()


class BatchAnalyzeRequest(BaseModel):
    """Request model for batch transcript analysis."""

    transcripts: list[str] = Field(
        ...,
        min_length=1,
        max_length=100,
        description="List of medical transcripts to analyze in batch",
        examples=[
            [
                "Patient A: headache for 2 days, no fever",
                "Patient B: chest pain, shortness of breath",
                "Patient C: fever and cough for 5 days",
            ]
        ],
    )

    num_next_actions: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Number of next action items to generate for each transcript (1-10)",
    )

    @field_validator("transcripts")
    @classmethod
    def validate_transcripts(cls, v: list[str]) -> list[str]:
        """Ensure all transcripts meet minimum requirements."""
        validated = []
        for i, transcript in enumerate(v):
            stripped = transcript.strip()
            if not stripped:
                raise ValueError(f"Transcript at index {i} cannot be empty")
            if len(stripped) < 10:
                raise ValueError(
                    f"Transcript at index {i} is too short (minimum 10 characters)"
                )
            validated.append(stripped)
        return validated
