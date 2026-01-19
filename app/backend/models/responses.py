"""
API response models using Pydantic.

Defines the structure for API responses.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.backend.models.observability import ObservabilityMetadata


class AnalysisResult(BaseModel):
    """Analysis result returned by the LLM."""

    summary: str = Field(
        ...,
        description="Concise summary of the medical transcript",
    )
    next_actions: list[str] = Field(
        ...,
        description="List of recommended next actions",
        min_length=1,
        max_length=10,
    )


class AnalysisResponse(BaseModel):
    """Response model for single transcript analysis."""

    id: str = Field(
        ...,
        description="Unique identifier for this analysis",
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    )
    summary: str = Field(
        ...,
        description="Concise summary of the medical transcript",
    )
    next_actions: list[str] = Field(
        ...,
        description="List of recommended next actions (ordered by priority)",
    )
    created_at: datetime = Field(
        ...,
        description="Timestamp when the analysis was created",
    )
    transcript: str = Field(
        ...,
        description="Original transcript that was analyzed",
    )
    observability: ObservabilityMetadata | None = Field(
        default=None,
        description="Observability metadata (optional for backward compatibility)",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "summary": "Patient presents with persistent headaches for 3 days, "
                "worse in the morning. Currently managing with ibuprofen with minimal relief.",
                "next_actions": [
                    "Perform neurological examination",
                    "Review patient's medication history",
                    "Consider imaging if symptoms persist"
                ],
                "created_at": "2024-01-15T10:30:00Z",
                "transcript": "Patient reports persistent headaches...",
            }
        }
    )


class BatchAnalysisResponse(BaseModel):
    """Response model for batch transcript analysis."""

    results: list[AnalysisResponse] = Field(
        ...,
        description="List of analysis results",
    )
    total: int = Field(
        ...,
        description="Total number of transcripts submitted",
    )
    successful: int = Field(
        ...,
        description="Number of successful analyses",
    )
    failed: int = Field(
        ...,
        description="Number of failed analyses",
    )
    errors: list[str] | None = Field(
        default=None,
        description="List of error messages for failed analyses",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "results": [
                    {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "summary": "Patient A summary...",
                        "next_actions": ["Action A", "Action B"],
                        "created_at": "2024-01-15T10:30:00Z",
                        "transcript": "Patient A: headache...",
                    }
                ],
                "total": 3,
                "successful": 2,
                "failed": 1,
                "errors": ["Analysis failed for transcript 3: API timeout"],
            }
        }
    )


class HealthResponse(BaseModel):
    """Response model for health check endpoints."""

    status: str = Field(
        ...,
        description="Health status",
        examples=["healthy", "ready"],
    )
    checks: dict[str, Any] | None = Field(
        default=None,
        description="Detailed health check results",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "ready",
                "checks": {
                    "openai_key_configured": True,
                    "environment": "production",
                },
            }
        }
    )
