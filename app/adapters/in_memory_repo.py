"""In-memory implementation of the transcript repository."""

from app.domain.models import TranscriptAnalysis
from app.ports.repository import TranscriptRepository


class InMemoryTranscriptRepository(TranscriptRepository):
    """Stores transcript analyses in memory using a dictionary."""

    def __init__(self) -> None:
        self._storage: dict[str, TranscriptAnalysis] = {}

    def save(self, analysis: TranscriptAnalysis) -> None:
        """Store an analysis indexed by its ID."""
        self._storage[analysis.id] = analysis

    def get_by_id(self, analysis_id: str) -> TranscriptAnalysis | None:
        """Retrieve an analysis by ID, or None if not found."""
        return self._storage.get(analysis_id)
