"""
In-memory repository for storing analysis results.

Provides thread-safe CRUD operations using a dictionary.
"""

import threading
from datetime import datetime
from typing import Dict

from app.models.responses import AnalysisResponse
from app.ports.repository import AnalysisRepository
from app.utils.exceptions import NotFoundException


class InMemoryAnalysisRepository(AnalysisRepository):
    """
    In-memory storage for analysis results.

    Thread-safe implementation using a lock for concurrent access.
    """

    def __init__(self) -> None:
        self._storage: Dict[str, AnalysisResponse] = {}
        self._lock = threading.Lock()

    def save(self, analysis: AnalysisResponse) -> AnalysisResponse:
        """
        Save an analysis result.

        Args:
            analysis: Analysis result to save

        Returns:
            The saved analysis result
        """
        with self._lock:
            self._storage[analysis.id] = analysis
        return analysis

    def get_by_id(self, analysis_id: str) -> AnalysisResponse:
        """
        Retrieve an analysis result by ID.

        Args:
            analysis_id: Unique identifier of the analysis

        Returns:
            The analysis result

        Raises:
            NotFoundException: If analysis not found
        """
        with self._lock:
            analysis = self._storage.get(analysis_id)

        if not analysis:
            raise NotFoundException(resource="Analysis", identifier=analysis_id)

        return analysis

    def list_all(self) -> list[AnalysisResponse]:
        """
        List all analysis results.

        Returns:
            List of all stored analysis results
        """
        with self._lock:
            return list(self._storage.values())

    def delete(self, analysis_id: str) -> None:
        """
        Delete an analysis result.

        Args:
            analysis_id: Unique identifier of the analysis to delete

        Raises:
            NotFoundException: If analysis not found
        """
        with self._lock:
            if analysis_id not in self._storage:
                raise NotFoundException(resource="Analysis", identifier=analysis_id)
            del self._storage[analysis_id]

    def count(self) -> int:
        """
        Get the total number of stored analyses.

        Returns:
            Count of stored analyses
        """
        with self._lock:
            return len(self._storage)

    def clear(self) -> None:
        """Clear all stored analyses (useful for testing)."""
        with self._lock:
            self._storage.clear()
