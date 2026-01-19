"""
Unit/Integration tests for Redis repository.

These tests require a running Redis instance and are marked as integration tests.
Run with: pytest tests/unit/test_redis_repository.py -m integration
"""

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from redis.asyncio import Redis
from redis.exceptions import ConnectionError as RedisConnectionError

from app.models.responses import AnalysisResponse
from app.repositories.redis import RedisAnalysisRepository, RedisAnalysisRepositorySync
from app.utils.exceptions import NotFoundException


@pytest.fixture
async def redis_client():
    """Create Redis client for testing."""
    client = Redis(
        host="localhost",
        port=6379,
        db=15,  # Use separate DB for tests
        decode_responses=False,
    )

    # Test connection
    try:
        await client.ping()
    except RedisConnectionError:
        pytest.skip("Redis not available for testing")

    yield client

    # Cleanup
    await client.flushdb()
    await client.aclose()


@pytest.fixture
async def redis_repository(redis_client):
    """Create Redis repository for testing."""
    repo = RedisAnalysisRepository(
        redis_client=redis_client,
        key_prefix="test-transcript",
        environment="test",
        ttl_seconds=None,
    )

    yield repo

    # Cleanup
    await repo.clear()


@pytest.fixture
def sync_redis_repository(redis_repository):
    """Create synchronous wrapper for Redis repository."""
    return RedisAnalysisRepositorySync(redis_repository)


@pytest.fixture
def sample_analysis():
    """Create sample analysis for testing."""
    return AnalysisResponse(
        id=str(uuid4()),
        summary="Test summary",
        next_actions=["Action 1", "Action 2", "Action 3"],
        created_at=datetime.now(UTC),
        transcript="Test transcript",
    )


@pytest.mark.integration
@pytest.mark.asyncio
class TestRedisRepositorySave:
    """Test save operations."""

    async def test_save_analysis(self, redis_repository, sample_analysis):
        """Test saving analysis to Redis."""
        result = await redis_repository.save(sample_analysis)

        assert result.id == sample_analysis.id
        assert result.summary == sample_analysis.summary
        assert result.next_actions == sample_analysis.next_actions

    async def test_save_creates_key(self, redis_repository, redis_client, sample_analysis):
        """Test save creates Redis key."""
        await redis_repository.save(sample_analysis)

        # Check key exists
        key = redis_repository._make_key(sample_analysis.id)
        exists = await redis_client.exists(key)
        assert exists == 1

    async def test_save_adds_to_index(self, redis_repository, redis_client, sample_analysis):
        """Test save adds ID to index."""
        await redis_repository.save(sample_analysis)

        # Check index contains ID
        members = await redis_client.smembers(redis_repository.index_key)
        id_list = [m.decode() if isinstance(m, bytes) else m for m in members]
        assert sample_analysis.id in id_list

    async def test_save_with_ttl(self, redis_client):
        """Test save with TTL sets expiration."""
        repo = RedisAnalysisRepository(
            redis_client=redis_client,
            key_prefix="test-ttl",
            environment="test",
            ttl_seconds=3600,  # 1 hour
        )

        analysis = AnalysisResponse(
            id=str(uuid4()),
            summary="TTL test",
            next_actions=["Action"],
            created_at=datetime.now(UTC),
            transcript="Test",
        )

        await repo.save(analysis)

        # Check TTL is set
        key = repo._make_key(analysis.id)
        ttl = await redis_client.ttl(key)
        assert ttl > 0
        assert ttl <= 3600

        # Cleanup
        await repo.clear()

    async def test_save_overwrites_existing(self, redis_repository, sample_analysis):
        """Test saving same ID overwrites existing data."""
        # Save first time
        await redis_repository.save(sample_analysis)

        # Modify and save again
        sample_analysis.summary = "Updated summary"
        await redis_repository.save(sample_analysis)

        # Retrieve and verify
        result = await redis_repository.get_by_id(sample_analysis.id)
        assert result.summary == "Updated summary"


@pytest.mark.integration
@pytest.mark.asyncio
class TestRedisRepositoryGet:
    """Test get operations."""

    async def test_get_existing_analysis(self, redis_repository, sample_analysis):
        """Test retrieving existing analysis."""
        await redis_repository.save(sample_analysis)

        result = await redis_repository.get_by_id(sample_analysis.id)

        assert result.id == sample_analysis.id
        assert result.summary == sample_analysis.summary
        assert result.next_actions == sample_analysis.next_actions
        assert result.transcript == sample_analysis.transcript

    async def test_get_nonexistent_raises_not_found(self, redis_repository):
        """Test retrieving nonexistent analysis raises NotFoundException."""
        with pytest.raises(NotFoundException) as exc_info:
            await redis_repository.get_by_id("nonexistent-id")

        assert "Analysis" in str(exc_info.value)
        assert "nonexistent-id" in str(exc_info.value)

    async def test_get_deserializes_correctly(self, redis_repository, sample_analysis):
        """Test get correctly deserializes Pydantic model."""
        await redis_repository.save(sample_analysis)

        result = await redis_repository.get_by_id(sample_analysis.id)

        # Check all fields deserialized
        assert isinstance(result, AnalysisResponse)
        assert isinstance(result.created_at, datetime)
        assert isinstance(result.next_actions, list)
        assert all(isinstance(action, str) for action in result.next_actions)


@pytest.mark.integration
@pytest.mark.asyncio
class TestRedisRepositoryList:
    """Test list operations."""

    async def test_list_empty(self, redis_repository):
        """Test listing when repository is empty."""
        result = await redis_repository.list_all()
        assert result == []

    async def test_list_single_analysis(self, redis_repository, sample_analysis):
        """Test listing with single analysis."""
        await redis_repository.save(sample_analysis)

        result = await redis_repository.list_all()

        assert len(result) == 1
        assert result[0].id == sample_analysis.id

    async def test_list_multiple_analyses(self, redis_repository):
        """Test listing multiple analyses."""
        analyses = [
            AnalysisResponse(
                id=str(uuid4()),
                summary=f"Summary {i}",
                next_actions=[f"Action {i}"],
                created_at=datetime.now(UTC),
                transcript=f"Transcript {i}",
            )
            for i in range(5)
        ]

        for analysis in analyses:
            await redis_repository.save(analysis)

        result = await redis_repository.list_all()

        assert len(result) == 5
        result_ids = {r.id for r in result}
        expected_ids = {a.id for a in analyses}
        assert result_ids == expected_ids

    async def test_list_sorted_by_date(self, redis_repository):
        """Test list returns analyses sorted by date (newest first)."""
        import asyncio

        analyses = []
        for i in range(3):
            analysis = AnalysisResponse(
                id=str(uuid4()),
                summary=f"Summary {i}",
                next_actions=[f"Action {i}"],
                created_at=datetime.now(UTC),
                transcript=f"Transcript {i}",
            )
            await redis_repository.save(analysis)
            analyses.append(analysis)
            await asyncio.sleep(0.01)  # Small delay to ensure different timestamps

        result = await redis_repository.list_all()

        # Should be sorted newest first
        assert result[0].id == analyses[-1].id  # Most recent
        assert result[-1].id == analyses[0].id  # Oldest

    async def test_list_with_limit(self, redis_repository):
        """Test listing with limit parameter."""
        # Create 10 analyses
        for i in range(10):
            analysis = AnalysisResponse(
                id=str(uuid4()),
                summary=f"Summary {i}",
                next_actions=[f"Action {i}"],
                created_at=datetime.now(UTC),
                transcript=f"Transcript {i}",
            )
            await redis_repository.save(analysis)

        # List with limit
        result = await redis_repository.list_all(limit=5)

        assert len(result) == 5

    async def test_list_handles_stale_index(self, redis_repository, redis_client, sample_analysis):
        """Test list cleans up stale index entries."""
        # Save analysis
        await redis_repository.save(sample_analysis)

        # Manually delete the data but leave index
        key = redis_repository._make_key(sample_analysis.id)
        await redis_client.delete(key)

        # List should handle stale entry
        result = await redis_repository.list_all()

        # Should return empty (stale entry removed)
        assert len(result) == 0

        # Index should be cleaned
        members = await redis_client.smembers(redis_repository.index_key)
        assert len(members) == 0


@pytest.mark.integration
@pytest.mark.asyncio
class TestRedisRepositoryDelete:
    """Test delete operations."""

    async def test_delete_existing_analysis(self, redis_repository, sample_analysis):
        """Test deleting existing analysis."""
        await redis_repository.save(sample_analysis)

        # Delete
        await redis_repository.delete(sample_analysis.id)

        # Verify deleted
        with pytest.raises(NotFoundException):
            await redis_repository.get_by_id(sample_analysis.id)

    async def test_delete_removes_key(self, redis_repository, redis_client, sample_analysis):
        """Test delete removes Redis key."""
        await redis_repository.save(sample_analysis)

        key = redis_repository._make_key(sample_analysis.id)
        assert await redis_client.exists(key) == 1

        await redis_repository.delete(sample_analysis.id)

        assert await redis_client.exists(key) == 0

    async def test_delete_removes_from_index(self, redis_repository, redis_client, sample_analysis):
        """Test delete removes ID from index."""
        await redis_repository.save(sample_analysis)

        await redis_repository.delete(sample_analysis.id)

        members = await redis_client.smembers(redis_repository.index_key)
        id_list = [m.decode() if isinstance(m, bytes) else m for m in members]
        assert sample_analysis.id not in id_list

    async def test_delete_nonexistent_raises_not_found(self, redis_repository):
        """Test deleting nonexistent analysis raises NotFoundException."""
        with pytest.raises(NotFoundException):
            await redis_repository.delete("nonexistent-id")


@pytest.mark.integration
@pytest.mark.asyncio
class TestRedisRepositoryCount:
    """Test count operations."""

    async def test_count_empty(self, redis_repository):
        """Test count when repository is empty."""
        count = await redis_repository.count()
        assert count == 0

    async def test_count_single(self, redis_repository, sample_analysis):
        """Test count with single analysis."""
        await redis_repository.save(sample_analysis)

        count = await redis_repository.count()
        assert count == 1

    async def test_count_multiple(self, redis_repository):
        """Test count with multiple analyses."""
        for i in range(5):
            analysis = AnalysisResponse(
                id=str(uuid4()),
                summary=f"Summary {i}",
                next_actions=[f"Action {i}"],
                created_at=datetime.now(UTC),
                transcript=f"Transcript {i}",
            )
            await redis_repository.save(analysis)

        count = await redis_repository.count()
        assert count == 5

    async def test_count_after_delete(self, redis_repository, sample_analysis):
        """Test count decreases after delete."""
        await redis_repository.save(sample_analysis)
        assert await redis_repository.count() == 1

        await redis_repository.delete(sample_analysis.id)
        assert await redis_repository.count() == 0


@pytest.mark.integration
@pytest.mark.asyncio
class TestRedisRepositoryClear:
    """Test clear operations."""

    async def test_clear_empty_repository(self, redis_repository):
        """Test clearing empty repository."""
        await redis_repository.clear()
        count = await redis_repository.count()
        assert count == 0

    async def test_clear_removes_all_analyses(self, redis_repository):
        """Test clear removes all analyses."""
        # Create multiple analyses
        for i in range(5):
            analysis = AnalysisResponse(
                id=str(uuid4()),
                summary=f"Summary {i}",
                next_actions=[f"Action {i}"],
                created_at=datetime.now(UTC),
                transcript=f"Transcript {i}",
            )
            await redis_repository.save(analysis)

        assert await redis_repository.count() == 5

        await redis_repository.clear()

        assert await redis_repository.count() == 0
        assert await redis_repository.list_all() == []

    async def test_clear_removes_index(self, redis_repository, redis_client):
        """Test clear removes index."""
        # Create analysis
        analysis = AnalysisResponse(
            id=str(uuid4()),
            summary="Test",
            next_actions=["Action"],
            created_at=datetime.now(UTC),
            transcript="Test",
        )
        await redis_repository.save(analysis)

        await redis_repository.clear()

        # Index should be gone
        exists = await redis_client.exists(redis_repository.index_key)
        assert exists == 0


@pytest.mark.integration
class TestSyncRepositoryWrapper:
    """Test synchronous wrapper."""

    def test_sync_save(self, sync_redis_repository, sample_analysis):
        """Test synchronous save."""
        result = sync_redis_repository.save(sample_analysis)
        assert result.id == sample_analysis.id

    def test_sync_get(self, sync_redis_repository, sample_analysis):
        """Test synchronous get."""
        sync_redis_repository.save(sample_analysis)
        result = sync_redis_repository.get_by_id(sample_analysis.id)
        assert result.id == sample_analysis.id

    def test_sync_list(self, sync_redis_repository, sample_analysis):
        """Test synchronous list."""
        sync_redis_repository.save(sample_analysis)
        result = sync_redis_repository.list_all()
        assert len(result) == 1

    def test_sync_delete(self, sync_redis_repository, sample_analysis):
        """Test synchronous delete."""
        sync_redis_repository.save(sample_analysis)
        sync_redis_repository.delete(sample_analysis.id)

        with pytest.raises(NotFoundException):
            sync_redis_repository.get_by_id(sample_analysis.id)

    def test_sync_count(self, sync_redis_repository, sample_analysis):
        """Test synchronous count."""
        sync_redis_repository.save(sample_analysis)
        count = sync_redis_repository.count()
        assert count == 1

    def test_sync_clear(self, sync_redis_repository, sample_analysis):
        """Test synchronous clear."""
        sync_redis_repository.save(sample_analysis)
        sync_redis_repository.clear()
        count = sync_redis_repository.count()
        assert count == 0


@pytest.mark.integration
@pytest.mark.asyncio
class TestRedisRepositoryEdgeCases:
    """Test edge cases and error handling."""

    async def test_very_long_transcript(self, redis_repository):
        """Test handling of very long transcripts."""
        analysis = AnalysisResponse(
            id=str(uuid4()),
            summary="Summary",
            next_actions=["Action"],
            created_at=datetime.now(UTC),
            transcript="word " * 10000,  # Very long
        )

        await redis_repository.save(analysis)
        result = await redis_repository.get_by_id(analysis.id)

        assert result.transcript == analysis.transcript

    async def test_special_characters_in_content(self, redis_repository):
        """Test handling of special characters."""
        analysis = AnalysisResponse(
            id=str(uuid4()),
            summary="Summary with émojis 🎉 and spëcial çharacters",
            next_actions=["Action with 中文", "Действие"],
            created_at=datetime.now(UTC),
            transcript="Transcript with\nnewlines\tand\ttabs",
        )

        await redis_repository.save(analysis)
        result = await redis_repository.get_by_id(analysis.id)

        assert result.summary == analysis.summary
        assert result.next_actions == analysis.next_actions
        assert result.transcript == analysis.transcript

    async def test_many_next_actions(self, redis_repository):
        """Test handling of many next actions."""
        analysis = AnalysisResponse(
            id=str(uuid4()),
            summary="Summary",
            next_actions=[f"Action {i}" for i in range(100)],
            created_at=datetime.now(UTC),
            transcript="Test",
        )

        await redis_repository.save(analysis)
        result = await redis_repository.get_by_id(analysis.id)

        assert len(result.next_actions) == 100

    async def test_concurrent_saves(self, redis_repository):
        """Test concurrent save operations."""
        import asyncio

        analyses = [
            AnalysisResponse(
                id=str(uuid4()),
                summary=f"Summary {i}",
                next_actions=[f"Action {i}"],
                created_at=datetime.now(UTC),
                transcript=f"Transcript {i}",
            )
            for i in range(10)
        ]

        # Save concurrently
        await asyncio.gather(*[redis_repository.save(a) for a in analyses])

        # Verify all saved
        count = await redis_repository.count()
        assert count == 10
