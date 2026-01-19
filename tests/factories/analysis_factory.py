"""
Factory for creating AnalysisResponse test objects.

Provides helper functions to generate test data with sensible defaults.
Enhanced with unique ID generation and batch creation capabilities.
"""

import uuid
from datetime import UTC, datetime, timedelta

from app.backend.models.responses import AnalysisResponse


def make_analysis_response(**overrides) -> AnalysisResponse:
    """
    Factory function to create AnalysisResponse with unique IDs.

    Uses **overrides pattern for flexible test data generation.
    Each call generates a new unique ID and timestamp.

    Args:
        **overrides: Optional field overrides (id, summary, next_actions, etc.)

    Returns:
        AnalysisResponse with unique ID and timestamp

    Example:
        >>> analysis = make_analysis_response(summary="Custom summary")
        >>> assert analysis.summary == "Custom summary"
        >>> assert isinstance(analysis.id, str)
    """
    # Default values with unique ID and current timestamp
    defaults = {
        "id": str(uuid.uuid4()),
        "summary": "Patient presents with persistent headaches for 3 days, worse in the morning.",
        "next_actions": [
            "Perform neurological examination",
            "Review patient's medication history",
            "Consider imaging if symptoms persist",
            "Schedule follow-up in 1 week"
        ],
        "created_at": datetime.now(UTC),
        "transcript": (
            "Patient: I've been having these headaches for about 3 days now. "
            "They're really bad in the morning.\n"
            "Doctor: Can you describe the pain?\n"
            "Patient: It's like a throbbing pain on the right side of my head. "
            "I've been taking ibuprofen but it's not helping much."
        ),
    }

    # Merge defaults with overrides
    defaults.update(overrides)
    return AnalysisResponse(**defaults)


def make_batch_analyses(count: int = 5, **overrides) -> list[AnalysisResponse]:
    """
    Generate list of AnalysisResponse objects with unique IDs.

    Each analysis gets a unique ID and timestamp offset by index.
    Timestamps are sequential with 1-minute intervals.

    Args:
        count: Number of analyses to generate (default: 5)
        **overrides: Optional field overrides applied to all instances

    Returns:
        List of AnalysisResponse objects with unique IDs

    Example:
        >>> analyses = make_batch_analyses(count=3)
        >>> assert len(analyses) == 3
        >>> assert len(set(a.id for a in analyses)) == 3  # All unique IDs
        >>> # Timestamps are sequential
        >>> assert analyses[0].created_at > analyses[1].created_at
    """
    analyses = []
    base_time = datetime.now(UTC)

    for i in range(count):
        # Create unique transcript and summary for each
        analysis_overrides = {
            "created_at": base_time - timedelta(minutes=i),
            "summary": f"Patient {i+1}: {overrides.get('summary', 'Medical consultation summary')}",
            "transcript": f"Transcript for patient {i+1}: {overrides.get('transcript', 'Medical consultation details')}",
        }

        # Merge with any additional overrides (excluding already handled fields)
        for key, value in overrides.items():
            if key not in ["summary", "transcript", "created_at"]:
                analysis_overrides[key] = value

        analyses.append(make_analysis_response(**analysis_overrides))

    return analyses


# Legacy compatibility (deprecated, use make_analysis_response instead)
def create_analysis_response(
    id: str | None = None,
    summary: str = "Patient presents with persistent headaches for 3 days",
    next_actions: list[str] | None = None,
    created_at: datetime | None = None,
    transcript: str = "Patient reports persistent headaches, worse in the morning",
) -> AnalysisResponse:
    """
    Create an AnalysisResponse object for testing.

    DEPRECATED: Use make_analysis_response(**overrides) instead.
    Kept for backward compatibility with existing tests.

    Args:
        id: Unique identifier (generated if not provided)
        summary: Analysis summary
        next_actions: List of recommended actions
        created_at: Creation timestamp (current time if not provided)
        transcript: Original transcript

    Returns:
        AnalysisResponse object with provided or default values
    """
    return AnalysisResponse(
        id=id or str(uuid.uuid4()),
        summary=summary,
        next_actions=next_actions or [
            "Perform neurological examination",
            "Review medication history"
        ],
        created_at=created_at or datetime.now(UTC),
        transcript=transcript,
    )


def create_multiple_analyses(count: int = 3) -> list[AnalysisResponse]:
    """
    Create multiple AnalysisResponse objects for testing.

    DEPRECATED: Use make_batch_analyses(count=N) instead.
    Kept for backward compatibility with existing tests.

    Args:
        count: Number of analyses to create

    Returns:
        List of AnalysisResponse objects
    """
    return [
        create_analysis_response(
            summary=f"Analysis summary {i + 1}",
            transcript=f"Patient transcript {i + 1}",
        )
        for i in range(count)
    ]
