"""
Unit tests for InMemoryAnalysisRepository.

Tests cover CRUD operations, thread safety, and edge cases.
"""

import concurrent.futures
import uuid
from concurrent.futures import ThreadPoolExecutor

import pytest

from app.backend.repositories.in_memory import InMemoryAnalysisRepository
from app.backend.utils.exceptions import NotFoundException
from tests.factories.analysis_factory import (
    create_analysis_response,
    create_multiple_analyses,
)


@pytest.fixture
def repository():
    """Create a fresh InMemoryAnalysisRepository for each test."""
    return InMemoryAnalysisRepository()


@pytest.fixture
def sample_analysis():
    """Create a sample AnalysisResponse for testing."""
    return create_analysis_response()


# ============================================================================
# CRUD Operations Tests (6 tests)
# ============================================================================


def test_save_stores_analysis(repository, sample_analysis):
    """
    Test that save() stores an analysis and returns it.

    Arrange: Create repository and analysis
    Act: Save the analysis
    Assert: Returned analysis matches input, can be retrieved
    """
    # Act
    result = repository.save(sample_analysis)

    # Assert
    assert result == sample_analysis
    assert repository.count() == 1
    retrieved = repository.get_by_id(sample_analysis.id)
    assert retrieved == sample_analysis


def test_save_with_existing_id_updates(repository, sample_analysis):
    """
    Test that saving with an existing ID updates the record.

    Arrange: Save initial analysis
    Act: Save updated version with same ID
    Assert: Analysis is updated, count remains 1
    """
    # Arrange
    repository.save(sample_analysis)
    original_count = repository.count()

    # Create updated version with same ID
    updated_analysis = create_analysis_response(
        id=sample_analysis.id,
        summary="Updated summary",
        next_actions=["Updated actions"],
        transcript=sample_analysis.transcript,
    )

    # Act
    result = repository.save(updated_analysis)

    # Assert
    assert result.summary == "Updated summary"
    assert result.next_actions == ["Updated actions"]
    assert repository.count() == original_count  # Count unchanged
    retrieved = repository.get_by_id(sample_analysis.id)
    assert retrieved.summary == "Updated summary"


def test_get_by_id_returns_analysis(repository, sample_analysis):
    """
    Test that get_by_id() returns the correct analysis.

    Arrange: Save an analysis
    Act: Retrieve by ID
    Assert: Retrieved analysis matches saved one
    """
    # Arrange
    repository.save(sample_analysis)

    # Act
    result = repository.get_by_id(sample_analysis.id)

    # Assert
    assert result == sample_analysis
    assert result.id == sample_analysis.id
    assert result.summary == sample_analysis.summary


def test_get_by_id_raises_not_found(repository):
    """
    Test that get_by_id() raises NotFoundException for missing ID.

    Arrange: Empty repository
    Act: Try to retrieve non-existent ID
    Assert: NotFoundException is raised with correct details
    """
    # Arrange
    non_existent_id = str(uuid.uuid4())

    # Act & Assert
    with pytest.raises(NotFoundException) as exc_info:
        repository.get_by_id(non_existent_id)

    assert f"Analysis with id '{non_existent_id}' not found" in str(exc_info.value)
    assert exc_info.value.status_code == 404


def test_list_all_returns_empty_when_no_data(repository):
    """
    Test that list_all() returns empty list when repository is empty.

    Arrange: Empty repository
    Act: Call list_all()
    Assert: Returns empty list
    """
    # Act
    result = repository.list_all()

    # Assert
    assert result == []
    assert len(result) == 0


def test_list_all_returns_all_analyses(repository):
    """
    Test that list_all() returns all stored analyses.

    Arrange: Save multiple analyses
    Act: Call list_all()
    Assert: All analyses are returned
    """
    # Arrange
    analyses = create_multiple_analyses(count=3)
    for analysis in analyses:
        repository.save(analysis)

    # Act
    result = repository.list_all()

    # Assert
    assert len(result) == 3
    result_ids = {analysis.id for analysis in result}
    expected_ids = {analysis.id for analysis in analyses}
    assert result_ids == expected_ids


# ============================================================================
# Additional Operations Tests (3 tests)
# ============================================================================


def test_delete_removes_analysis(repository, sample_analysis):
    """
    Test that delete() removes an existing analysis.

    Arrange: Save an analysis
    Act: Delete it
    Assert: Analysis is removed, count decreases
    """
    # Arrange
    repository.save(sample_analysis)
    assert repository.count() == 1

    # Act
    repository.delete(sample_analysis.id)

    # Assert
    assert repository.count() == 0
    with pytest.raises(NotFoundException):
        repository.get_by_id(sample_analysis.id)


def test_delete_raises_not_found(repository):
    """
    Test that delete() raises NotFoundException for non-existent ID.

    Arrange: Empty repository
    Act: Try to delete non-existent ID
    Assert: NotFoundException is raised
    """
    # Arrange
    non_existent_id = str(uuid.uuid4())

    # Act & Assert
    with pytest.raises(NotFoundException) as exc_info:
        repository.delete(non_existent_id)

    assert f"Analysis with id '{non_existent_id}' not found" in str(exc_info.value)


def test_count_returns_correct_number(repository):
    """
    Test that count() returns the correct number of analyses.

    Arrange: Save varying numbers of analyses
    Act: Call count() at each stage
    Assert: Count is accurate
    """
    # Arrange & Act & Assert
    assert repository.count() == 0

    # Add first analysis
    analysis1 = create_analysis_response()
    repository.save(analysis1)
    assert repository.count() == 1

    # Add second analysis
    analysis2 = create_analysis_response()
    repository.save(analysis2)
    assert repository.count() == 2

    # Delete one analysis
    repository.delete(analysis1.id)
    assert repository.count() == 1

    # Clear all
    repository.clear()
    assert repository.count() == 0


# ============================================================================
# Utility & Cleanup Tests (3 tests)
# ============================================================================


def test_clear_removes_all_analyses(repository):
    """
    Test that clear() removes all stored analyses.

    Arrange: Save multiple analyses
    Act: Call clear()
    Assert: Repository is empty
    """
    # Arrange
    analyses = create_multiple_analyses(count=5)
    for analysis in analyses:
        repository.save(analysis)
    assert repository.count() == 5

    # Act
    repository.clear()

    # Assert
    assert repository.count() == 0
    assert repository.list_all() == []


def test_concurrent_saves_are_thread_safe(repository):
    """
    Test that concurrent save() operations are thread-safe.

    Arrange: Create multiple analyses
    Act: Save them concurrently using ThreadPoolExecutor
    Assert: All analyses are saved without data corruption
    """
    # Arrange
    num_threads = 10
    analyses = create_multiple_analyses(count=num_threads)

    # Act
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [
            executor.submit(repository.save, analysis)
            for analysis in analyses
        ]
        concurrent.futures.wait(futures)

    # Assert
    assert repository.count() == num_threads
    stored_analyses = repository.list_all()
    stored_ids = {analysis.id for analysis in stored_analyses}
    expected_ids = {analysis.id for analysis in analyses}
    assert stored_ids == expected_ids


def test_concurrent_reads_while_writing(repository):
    """
    Test that concurrent reads and writes are thread-safe.

    Arrange: Save initial analyses, prepare new ones
    Act: Perform concurrent reads, writes, and deletes
    Assert: No exceptions, data integrity maintained
    """
    # Arrange
    initial_analyses = create_multiple_analyses(count=5)
    for analysis in initial_analyses:
        repository.save(analysis)

    new_analyses = create_multiple_analyses(count=5)

    # Act
    def read_operation():
        """Perform read operations."""
        try:
            repository.list_all()
            if repository.count() > 0:
                analyses = repository.list_all()
                if analyses:
                    repository.get_by_id(analyses[0].id)
        except NotFoundException:
            # Expected during concurrent deletes
            pass

    def write_operation(analysis):
        """Perform write operations."""
        repository.save(analysis)

    def delete_operation(analysis_id):
        """Perform delete operations."""
        try:
            repository.delete(analysis_id)
        except NotFoundException:
            # Expected if already deleted
            pass

    with ThreadPoolExecutor(max_workers=15) as executor:
        futures = []

        # Submit read operations
        for _ in range(5):
            futures.append(executor.submit(read_operation))

        # Submit write operations
        for analysis in new_analyses:
            futures.append(executor.submit(write_operation, analysis))

        # Submit delete operations
        for analysis in initial_analyses[:3]:
            futures.append(executor.submit(delete_operation, analysis.id))

        # Wait for all operations to complete
        concurrent.futures.wait(futures)

    # Assert - No exceptions should have been raised (except expected NotFoundExceptions)
    # Check that final state is consistent
    final_count = repository.count()
    final_analyses = repository.list_all()
    assert len(final_analyses) == final_count
    # Verify all returned analyses are valid
    for analysis in final_analyses:
        assert analysis.id
        assert analysis.summary
        assert analysis.transcript
