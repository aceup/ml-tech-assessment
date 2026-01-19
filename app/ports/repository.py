"""
Repository port interface for analysis persistence.

Defines the contract for analysis storage implementations (in-memory, Redis, etc.)
following the hexagonal architecture pattern.
"""

from abc import ABC, abstractmethod

from app.models.responses import AnalysisResponse


class AnalysisRepository(ABC):
    """
    Abstract base class for analysis persistence.

    Implementations must provide all CRUD operations for analysis results.
    This allows swapping storage backends (memory, Redis, PostgreSQL, etc.)
    without changing business logic.
    """

    @abstractmethod
    def save(self, analysis: AnalysisResponse) -> AnalysisResponse:
        """
        Save an analysis result.

        Args:
            analysis: Analysis to save

        Returns:
            Saved analysis (may include generated fields)

        Raises:
            Exception: If save fails
        """
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    def list_all(self) -> list[AnalysisResponse]:
        """
        List all analyses.

        Returns:
            List of all stored analyses (may be paginated in some implementations)
        """
        pass

    @abstractmethod
    def delete(self, analysis_id: str) -> None:
        """
        Delete an analysis by ID.

        Args:
            analysis_id: Unique identifier

        Raises:
            NotFoundException: If analysis not found
        """
        pass

    @abstractmethod
    def count(self) -> int:
        """
        Count total number of analyses.

        Returns:
            Total count
        """
        pass

    @abstractmethod
    def clear(self) -> None:
        """
        Clear all analyses.

        WARNING: This is destructive and should only be used for testing.
        """
        pass
