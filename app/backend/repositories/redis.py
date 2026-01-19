"""
Redis-based repository for storing analysis results.

Provides async CRUD operations with Redis persistence and a synchronous wrapper.
"""

import asyncio
from functools import wraps
from typing import Any, Callable

from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.backend.core.logging import get_logger
from app.backend.models.responses import AnalysisResponse
from app.backend.ports.repository import AnalysisRepository
from app.backend.utils.exceptions import NotFoundException

logger = get_logger(__name__)


def sync_async(func: Callable) -> Callable:
    """
    Decorator to run async functions synchronously.

    Wraps async repository methods to provide sync interface
    compatible with current service layer.
    """

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        return asyncio.run(func(*args, **kwargs))

    return wrapper


class RedisAnalysisRepository:
    """
    Async Redis-based repository for analysis results.

    Uses JSON serialization to store Pydantic models in Redis.
    Key structure: {app}:{env}:analysis:{id}
    """

    def __init__(
        self,
        redis_client: Redis,
        key_prefix: str = "transcript-analysis",
        environment: str = "production",
        ttl_seconds: int | None = None,
    ) -> None:
        """
        Initialize Redis repository.

        Args:
            redis_client: Redis async client
            key_prefix: Prefix for Redis keys (default: "transcript-analysis")
            environment: Environment name for key namespacing
            ttl_seconds: TTL for keys (None = no expiration)
        """
        self.redis = redis_client
        self.key_prefix = key_prefix
        self.environment = environment
        self.ttl_seconds = ttl_seconds

        # Index key for tracking all analysis IDs
        self.index_key = f"{key_prefix}:{environment}:index"

        logger.info(
            "redis_repository_init",
            message="Redis repository initialized",
            key_prefix=key_prefix,
            environment=environment,
            ttl_seconds=ttl_seconds,
        )

    def _make_key(self, analysis_id: str) -> str:
        """
        Generate Redis key for an analysis.

        Args:
            analysis_id: Analysis ID

        Returns:
            Redis key string
        """
        return f"{self.key_prefix}:{self.environment}:analysis:{analysis_id}"

    async def save(self, analysis: AnalysisResponse) -> AnalysisResponse:
        """
        Save an analysis result to Redis.

        Args:
            analysis: Analysis to save

        Returns:
            Saved analysis

        Raises:
            RedisError: If Redis operation fails
        """
        try:
            key = self._make_key(analysis.id)

            # Serialize to JSON
            json_data = analysis.model_dump_json()

            # Use pipeline for atomic operations
            async with self.redis.pipeline(transaction=True) as pipe:
                # Store analysis data
                await pipe.set(key, json_data)

                # Add to index
                await pipe.sadd(self.index_key, analysis.id)

                # Set TTL if configured
                if self.ttl_seconds:
                    await pipe.expire(key, self.ttl_seconds)

                await pipe.execute()

            logger.debug(
                "redis_save",
                message="Analysis saved to Redis",
                analysis_id=analysis.id,
                key=key,
            )

            return analysis

        except RedisError as e:
            logger.error(
                "redis_save_failed",
                message="Failed to save analysis to Redis",
                analysis_id=analysis.id,
                error=str(e),
            )
            raise

    async def get_by_id(self, analysis_id: str) -> AnalysisResponse:
        """
        Retrieve an analysis by ID.

        Args:
            analysis_id: Analysis ID

        Returns:
            Analysis result

        Raises:
            NotFoundException: If analysis not found
            RedisError: If Redis operation fails
        """
        try:
            key = self._make_key(analysis_id)
            json_data = await self.redis.get(key)

            if not json_data:
                raise NotFoundException(resource="Analysis", identifier=analysis_id)

            # Deserialize from JSON
            analysis = AnalysisResponse.model_validate_json(json_data)

            logger.debug(
                "redis_get",
                message="Analysis retrieved from Redis",
                analysis_id=analysis_id,
            )

            return analysis

        except NotFoundException:
            raise
        except Exception as e:
            logger.error(
                "redis_get_failed",
                message="Failed to retrieve analysis from Redis",
                analysis_id=analysis_id,
                error=str(e),
            )
            raise

    async def list_all(self, limit: int = 1000) -> list[AnalysisResponse]:
        """
        List all analyses.

        Args:
            limit: Maximum number of results to return

        Returns:
            List of analyses (most recent first)

        Raises:
            RedisError: If Redis operation fails
        """
        try:
            # Get all analysis IDs from index
            analysis_ids = await self.redis.smembers(self.index_key)

            if not analysis_ids:
                return []

            # Convert bytes to strings and limit
            id_list = [aid.decode() if isinstance(aid, bytes) else aid for aid in analysis_ids]
            id_list = id_list[:limit]

            # Fetch all analyses in parallel
            keys = [self._make_key(aid) for aid in id_list]
            json_data_list = await self.redis.mget(keys)

            analyses = []
            for i, json_data in enumerate(json_data_list):
                if json_data:
                    try:
                        analysis = AnalysisResponse.model_validate_json(json_data)
                        analyses.append(analysis)
                    except Exception as e:
                        logger.warning(
                            "redis_list_parse_failed",
                            message="Failed to parse analysis from Redis",
                            analysis_id=id_list[i],
                            error=str(e),
                        )
                else:
                    # Stale index entry, remove it
                    await self.redis.srem(self.index_key, id_list[i])
                    logger.warning(
                        "redis_stale_index_entry",
                        message="Removed stale index entry",
                        analysis_id=id_list[i],
                    )

            # Sort by created_at desc (most recent first)
            analyses.sort(key=lambda a: a.created_at, reverse=True)

            logger.debug(
                "redis_list",
                message="Listed analyses from Redis",
                count=len(analyses),
            )

            return analyses

        except Exception as e:
            logger.error(
                "redis_list_failed",
                message="Failed to list analyses from Redis",
                error=str(e),
            )
            raise

    async def delete(self, analysis_id: str) -> None:
        """
        Delete an analysis by ID.

        Args:
            analysis_id: Analysis ID

        Raises:
            NotFoundException: If analysis not found
            RedisError: If Redis operation fails
        """
        try:
            key = self._make_key(analysis_id)

            # Check if exists
            exists = await self.redis.exists(key)
            if not exists:
                raise NotFoundException(resource="Analysis", identifier=analysis_id)

            # Delete atomically
            async with self.redis.pipeline(transaction=True) as pipe:
                await pipe.delete(key)
                await pipe.srem(self.index_key, analysis_id)
                await pipe.execute()

            logger.debug(
                "redis_delete",
                message="Analysis deleted from Redis",
                analysis_id=analysis_id,
            )

        except NotFoundException:
            raise
        except Exception as e:
            logger.error(
                "redis_delete_failed",
                message="Failed to delete analysis from Redis",
                analysis_id=analysis_id,
                error=str(e),
            )
            raise

    async def count(self) -> int:
        """
        Count total number of analyses.

        Returns:
            Total count

        Raises:
            RedisError: If Redis operation fails
        """
        try:
            count = await self.redis.scard(self.index_key)
            return count
        except Exception as e:
            logger.error(
                "redis_count_failed",
                message="Failed to count analyses in Redis",
                error=str(e),
            )
            raise

    async def clear(self) -> None:
        """
        Clear all analyses (for testing only).

        WARNING: This is destructive and will delete all data.

        Raises:
            RedisError: If Redis operation fails
        """
        try:
            # Get all analysis IDs
            analysis_ids = await self.redis.smembers(self.index_key)

            if analysis_ids:
                # Delete all analysis keys
                keys = [self._make_key(aid.decode() if isinstance(aid, bytes) else aid) for aid in analysis_ids]
                await self.redis.delete(*keys)

            # Clear index
            await self.redis.delete(self.index_key)

            logger.warning(
                "redis_clear",
                message="All analyses cleared from Redis",
                count=len(analysis_ids) if analysis_ids else 0,
            )

        except Exception as e:
            logger.error(
                "redis_clear_failed",
                message="Failed to clear analyses from Redis",
                error=str(e),
            )
            raise


class RedisAnalysisRepositorySync(AnalysisRepository):
    """
    Synchronous wrapper for Redis repository.

    Provides sync interface compatible with current service layer
    by wrapping async operations with asyncio.run().
    """

    def __init__(self, async_repo: RedisAnalysisRepository) -> None:
        """
        Initialize sync wrapper.

        Args:
            async_repo: Async Redis repository to wrap
        """
        self.async_repo = async_repo

    def save(self, analysis: AnalysisResponse) -> AnalysisResponse:
        """Save analysis (sync)."""
        import concurrent.futures

        def run_async():
            return asyncio.run(self.async_repo.save(analysis))

        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(run_async)
            return future.result()

    def get_by_id(self, analysis_id: str) -> AnalysisResponse:
        """Get analysis by ID (sync)."""
        import concurrent.futures

        def run_async():
            return asyncio.run(self.async_repo.get_by_id(analysis_id))

        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(run_async)
            return future.result()

    def list_all(self) -> list[AnalysisResponse]:
        """List all analyses (sync)."""
        import concurrent.futures

        def run_async():
            return asyncio.run(self.async_repo.list_all())

        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(run_async)
            return future.result()

    def delete(self, analysis_id: str) -> None:
        """Delete analysis (sync)."""
        import concurrent.futures

        def run_async():
            asyncio.run(self.async_repo.delete(analysis_id))

        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(run_async)
            future.result()

    def count(self) -> int:
        """Count analyses (sync)."""
        import concurrent.futures

        def run_async():
            return asyncio.run(self.async_repo.count())

        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(run_async)
            return future.result()

    def clear(self) -> None:
        """Clear all analyses (sync)."""
        import concurrent.futures

        def run_async():
            asyncio.run(self.async_repo.clear())

        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(run_async)
            future.result()
