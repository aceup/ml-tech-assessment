"""Abstract repository interface for transcript analysis persistence."""

from abc import ABC, abstractmethod

from app.domain.models import TranscriptAnalysis


class TranscriptRepository(ABC):
    """Abstract interface for storing and retrieving transcript analyses."""

    @abstractmethod
    def save(self, analysis: TranscriptAnalysis) -> None:
        """Persist a transcript analysis."""
        pass

    @abstractmethod
    def get_by_id(self, analysis_id: str) -> TranscriptAnalysis | None:
        """Retrieve a transcript analysis by its ID."""
        pass
