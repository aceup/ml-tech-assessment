"""Request and response schemas for the API."""

import pydantic


class AnalyzeRequest(pydantic.BaseModel):
    """Request body for transcript analysis."""

    transcript: str = pydantic.Field(..., min_length=1)

    @pydantic.field_validator("transcript")
    @classmethod
    def validate_transcript_not_empty(cls, v: str) -> str:
        """Ensure transcript is not empty or whitespace-only."""
        if not v.strip():
            raise ValueError("Transcript cannot be empty or contain only whitespace")
        return v


class AnalyzeResponse(pydantic.BaseModel):
    """Response body for a single transcript analysis."""

    id: str
    summary: str
    action_items: list[str]


class BatchAnalyzeRequest(pydantic.BaseModel):
    """Request body for batch transcript analysis."""

    transcripts: list[str] = pydantic.Field(..., min_length=1)

    @pydantic.field_validator("transcripts")
    @classmethod
    def validate_transcripts_not_empty(cls, v: list[str]) -> list[str]:
        """Ensure no transcript in the list is empty."""
        for i, transcript in enumerate(v):
            if not transcript or not transcript.strip():
                raise ValueError(f"Transcript at index {i} cannot be empty")
        return v


class BatchAnalyzeResponse(pydantic.BaseModel):
    """Response body for batch transcript analysis."""

    results: list[AnalyzeResponse]
