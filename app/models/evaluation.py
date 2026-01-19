"""
Evaluation models for human-in-the-loop feedback.

Enables collecting ratings, hallucination flags, and comments from real humans
(doctors, coaches, QA teams, end users) to build golden datasets and track quality.
"""

from datetime import datetime

from pydantic import BaseModel, Field


class AnalysisEvaluation(BaseModel):
    """Human feedback/evaluation for an analysis."""

    id: str
    analysis_id: str
    score: int = Field(..., ge=1, le=5, description="Human rating: 1-5 stars")
    is_hallucination: bool = Field(
        default=False,
        description="Human flagged: true if AI made things up",
    )
    comment: str | None = Field(
        default=None,
        max_length=1000,
        description="Human written feedback",
    )
    evaluated_at: datetime


class EvaluationRequest(BaseModel):
    """Request to submit human evaluation feedback."""

    score: int = Field(..., ge=1, le=5, description="Human rating: 1-5 stars")
    is_hallucination: bool = Field(
        default=False,
        description="Human flagged: true if AI made things up",
    )
    comment: str | None = Field(
        default=None,
        max_length=1000,
        description="Human written feedback",
    )
