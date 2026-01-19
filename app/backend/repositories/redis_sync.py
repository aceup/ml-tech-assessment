"""
Synchronous Redis repository implementation.

Uses synchronous redis-py client for direct integration with
FastAPI synchronous endpoints without event loop complexity.
"""

from datetime import datetime, timezone
from uuid import UUID

from redis import Redis
from redis.exceptions import RedisError

from app.backend.core.logging import get_logger
from app.backend.models.evaluation import AnalysisEvaluation
from app.backend.models.responses import AnalysisResponse
from app.backend.ports.repository import AnalysisRepository
from app.backend.utils.exceptions import NotFoundException

logger = get_logger(__name__)


class RedisSyncRepository(AnalysisRepository):
    """
    Synchronous Redis repository for analysis results.

    Uses blocking Redis operations compatible with synchronous
    FastAPI endpoints without async/await complexity.
    """

    def __init__(
        self,
        redis_client: Redis,
        environment: str = "production",
        ttl_seconds: int | None = None,
    ) -> None:
        """
        Initialize Redis repository.

        Args:
            redis_client: Synchronous Redis client instance
            environment: Environment name for key prefixing
            ttl_seconds: Optional TTL for analysis records (None = no expiry)
        """
        self.redis = redis_client
        self.environment = environment
        self.ttl_seconds = ttl_seconds

        # Key prefixes for organization
        self.key_prefix = "transcript-analysis"
        self.analysis_key_template = f"{self.key_prefix}:{environment}:analysis:{{}}"
        self.evaluation_key_template = f"{self.key_prefix}:{environment}:evaluation:{{}}"
        self.index_key = f"{self.key_prefix}:{environment}:index"
        self.evaluation_index_key = f"{self.key_prefix}:{environment}:evaluation_index"

        logger.info(
            "redis_sync_repository_init",
            message="Synchronous Redis repository initialized",
            key_prefix=self.key_prefix,
            environment=environment,
            ttl_seconds=ttl_seconds,
        )

    def save(self, analysis: AnalysisResponse) -> AnalysisResponse:
        """
        Save analysis to Redis.

        Args:
            analysis: Analysis response to save

        Returns:
            Saved analysis response

        Raises:
            RedisError: If Redis operation fails
        """
        try:
            analysis_key = self.analysis_key_template.format(analysis.id)

            # Serialize to JSON
            analysis_json = analysis.model_dump_json()

            # Use pipeline for atomic operations
            pipe = self.redis.pipeline()

            # Store analysis data
            if self.ttl_seconds:
                pipe.setex(analysis_key, self.ttl_seconds, analysis_json)
            else:
                pipe.set(analysis_key, analysis_json)

            # Add to index
            pipe.sadd(self.index_key, str(analysis.id))

            # Execute atomically
            pipe.execute()

            logger.debug(
                "redis_sync_save_success",
                message="Analysis saved to Redis",
                analysis_id=str(analysis.id),
                key=analysis_key,
            )

            return analysis

        except RedisError as e:
            logger.error(
                "redis_sync_save_failed",
                message="Failed to save analysis to Redis",
                analysis_id=str(analysis.id),
                error=str(e),
            )
            raise

    def get_by_id(self, analysis_id: str) -> AnalysisResponse:
        """
        Retrieve analysis by ID.

        Args:
            analysis_id: UUID of analysis to retrieve

        Returns:
            Analysis response

        Raises:
            NotFoundException: If analysis not found
            RedisError: If Redis operation fails
        """
        try:
            # Validate UUID format
            UUID(analysis_id)

            analysis_key = self.analysis_key_template.format(analysis_id)
            analysis_json = self.redis.get(analysis_key)

            if not analysis_json:
                raise NotFoundException(
                    resource_type="Analysis",
                    resource_id=analysis_id,
                )

            # Deserialize from JSON
            analysis = AnalysisResponse.model_validate_json(analysis_json)

            logger.debug(
                "redis_sync_get_success",
                message="Analysis retrieved from Redis",
                analysis_id=analysis_id,
            )

            return analysis

        except ValueError as e:
            raise NotFoundException(
                resource_type="Analysis",
                resource_id=analysis_id,
            ) from e
        except RedisError as e:
            logger.error(
                "redis_sync_get_failed",
                message="Failed to retrieve analysis from Redis",
                analysis_id=analysis_id,
                error=str(e),
            )
            raise

    def list_all(self) -> list[AnalysisResponse]:
        """
        List all analyses.

        Returns:
            List of all analysis responses

        Raises:
            RedisError: If Redis operation fails
        """
        try:
            # Get all IDs from index
            analysis_ids = self.redis.smembers(self.index_key)

            if not analysis_ids:
                return []

            # Fetch all analyses
            analyses: list[AnalysisResponse] = []
            for analysis_id_bytes in analysis_ids:
                analysis_id = analysis_id_bytes.decode("utf-8")
                try:
                    analysis = self.get_by_id(analysis_id)
                    analyses.append(analysis)
                except NotFoundException:
                    # Clean up stale index entry
                    self.redis.srem(self.index_key, analysis_id)
                    logger.warning(
                        "redis_sync_stale_entry",
                        message="Removed stale index entry",
                        analysis_id=analysis_id,
                    )

            # Sort by creation time (newest first)
            analyses.sort(key=lambda a: a.created_at, reverse=True)

            logger.debug(
                "redis_sync_list_success",
                message="Listed analyses from Redis",
                count=len(analyses),
            )

            return analyses

        except RedisError as e:
            logger.error(
                "redis_sync_list_failed",
                message="Failed to list analyses from Redis",
                error=str(e),
            )
            raise

    def delete(self, analysis_id: str) -> None:
        """
        Delete analysis by ID.

        Args:
            analysis_id: UUID of analysis to delete

        Raises:
            NotFoundException: If analysis not found
            RedisError: If Redis operation fails
        """
        try:
            # Validate UUID format
            UUID(analysis_id)

            analysis_key = self.analysis_key_template.format(analysis_id)

            # Check if exists before deleting
            if not self.redis.exists(analysis_key):
                raise NotFoundException(
                    resource_type="Analysis",
                    resource_id=analysis_id,
                )

            # Use pipeline for atomic deletion
            pipe = self.redis.pipeline()
            pipe.delete(analysis_key)
            pipe.srem(self.index_key, analysis_id)
            pipe.execute()

            logger.debug(
                "redis_sync_delete_success",
                message="Analysis deleted from Redis",
                analysis_id=analysis_id,
            )

        except ValueError as e:
            raise NotFoundException(
                resource_type="Analysis",
                resource_id=analysis_id,
            ) from e
        except RedisError as e:
            logger.error(
                "redis_sync_delete_failed",
                message="Failed to delete analysis from Redis",
                analysis_id=analysis_id,
                error=str(e),
            )
            raise

    def count(self) -> int:
        """
        Count total analyses.

        Returns:
            Total number of analyses

        Raises:
            RedisError: If Redis operation fails
        """
        try:
            count = self.redis.scard(self.index_key)

            logger.debug(
                "redis_sync_count_success",
                message="Counted analyses in Redis",
                count=count,
            )

            return count

        except RedisError as e:
            logger.error(
                "redis_sync_count_failed",
                message="Failed to count analyses in Redis",
                error=str(e),
            )
            raise

    def clear(self) -> None:
        """
        Clear all analyses (for testing).

        Raises:
            RedisError: If Redis operation fails
        """
        try:
            # Get all IDs
            analysis_ids = self.redis.smembers(self.index_key)

            if analysis_ids:
                # Delete all analysis keys and index
                pipe = self.redis.pipeline()
                for analysis_id_bytes in analysis_ids:
                    analysis_id = analysis_id_bytes.decode("utf-8")
                    analysis_key = self.analysis_key_template.format(analysis_id)
                    pipe.delete(analysis_key)
                pipe.delete(self.index_key)
                pipe.execute()

            logger.info(
                "redis_sync_clear_success",
                message="Cleared all analyses from Redis",
                count=len(analysis_ids) if analysis_ids else 0,
            )

        except RedisError as e:
            logger.error(
                "redis_sync_clear_failed",
                message="Failed to clear analyses from Redis",
                error=str(e),
            )
            raise

    def save_evaluation(self, evaluation: AnalysisEvaluation) -> AnalysisEvaluation:
        """
        Save human evaluation for an analysis.

        Args:
            evaluation: Evaluation to save

        Returns:
            Saved evaluation

        Raises:
            RedisError: If Redis operation fails
        """
        try:
            evaluation_key = self.evaluation_key_template.format(evaluation.analysis_id)

            # Serialize to JSON
            evaluation_json = evaluation.model_dump_json()

            # Use pipeline for atomic operations
            pipe = self.redis.pipeline()

            # Store evaluation data (use same TTL as analyses if configured)
            if self.ttl_seconds:
                pipe.setex(evaluation_key, self.ttl_seconds, evaluation_json)
            else:
                pipe.set(evaluation_key, evaluation_json)

            # Add to evaluation index
            pipe.sadd(self.evaluation_index_key, str(evaluation.analysis_id))

            # Execute atomically
            pipe.execute()

            logger.debug(
                "redis_sync_save_evaluation_success",
                message="Evaluation saved to Redis",
                evaluation_id=str(evaluation.id),
                analysis_id=str(evaluation.analysis_id),
                key=evaluation_key,
            )

            return evaluation

        except RedisError as e:
            logger.error(
                "redis_sync_save_evaluation_failed",
                message="Failed to save evaluation to Redis",
                evaluation_id=str(evaluation.id),
                error=str(e),
            )
            raise

    def get_evaluation(self, analysis_id: str) -> AnalysisEvaluation | None:
        """
        Get evaluation for an analysis.

        Args:
            analysis_id: Analysis identifier

        Returns:
            Evaluation if exists, None otherwise

        Raises:
            RedisError: If Redis operation fails
        """
        try:
            evaluation_key = self.evaluation_key_template.format(analysis_id)
            evaluation_json = self.redis.get(evaluation_key)

            if not evaluation_json:
                return None

            # Deserialize from JSON
            evaluation = AnalysisEvaluation.model_validate_json(evaluation_json)

            logger.debug(
                "redis_sync_get_evaluation_success",
                message="Evaluation retrieved from Redis",
                analysis_id=analysis_id,
            )

            return evaluation

        except RedisError as e:
            logger.error(
                "redis_sync_get_evaluation_failed",
                message="Failed to retrieve evaluation from Redis",
                analysis_id=analysis_id,
                error=str(e),
            )
            raise

    def list_evaluations(self) -> list[AnalysisEvaluation]:
        """
        List all evaluations.

        Returns:
            List of all evaluations

        Raises:
            RedisError: If Redis operation fails
        """
        try:
            # Get all analysis IDs from evaluation index
            analysis_ids = self.redis.smembers(self.evaluation_index_key)

            if not analysis_ids:
                return []

            # Fetch all evaluations
            evaluations: list[AnalysisEvaluation] = []
            for analysis_id_bytes in analysis_ids:
                analysis_id = analysis_id_bytes.decode("utf-8")
                evaluation = self.get_evaluation(analysis_id)
                if evaluation:
                    evaluations.append(evaluation)
                else:
                    # Clean up stale index entry
                    self.redis.srem(self.evaluation_index_key, analysis_id)
                    logger.warning(
                        "redis_sync_stale_evaluation_entry",
                        message="Removed stale evaluation index entry",
                        analysis_id=analysis_id,
                    )

            # Sort by evaluation time (newest first)
            evaluations.sort(key=lambda e: e.evaluated_at, reverse=True)

            logger.debug(
                "redis_sync_list_evaluations_success",
                message="Listed evaluations from Redis",
                count=len(evaluations),
            )

            return evaluations

        except RedisError as e:
            logger.error(
                "redis_sync_list_evaluations_failed",
                message="Failed to list evaluations from Redis",
                error=str(e),
            )
            raise
