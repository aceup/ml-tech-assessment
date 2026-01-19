"""
Redis client infrastructure with connection pooling.

Provides singleton Redis client with lifecycle management for the application.
"""

from typing import Any

from redis import Redis as SyncRedis
from redis.asyncio import Redis
from redis.asyncio.connection import ConnectionPool
from redis.connection import ConnectionPool as SyncConnectionPool
from redis.exceptions import ConnectionError as RedisConnectionError
from redis.exceptions import TimeoutError as RedisTimeoutError

from app.core.config import Settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class RedisClient:
    """
    Redis client wrapper with connection pooling and lifecycle management.

    Provides async Redis operations with proper connection handling.
    """

    def __init__(self, settings: Settings) -> None:
        """
        Initialize Redis client.

        Args:
            settings: Application settings with Redis configuration
        """
        self.settings = settings
        self.pool: ConnectionPool | None = None
        self.client: Redis | None = None

        logger.info(
            "redis_client_init",
            message="Redis client initialized",
            host=settings.redis_host,
            port=settings.redis_port,
            db=settings.redis_db,
            max_connections=settings.redis_max_connections,
        )

    async def connect(self) -> None:
        """
        Establish Redis connection with connection pooling.

        Raises:
            RedisConnectionError: If connection fails
        """
        try:
            # Create connection pool
            self.pool = ConnectionPool.from_url(
                self.settings.redis_url,
                max_connections=self.settings.redis_max_connections,
                decode_responses=False,  # We'll handle encoding ourselves
                socket_connect_timeout=5,
                socket_timeout=5,
            )

            # Create Redis client
            self.client = Redis(connection_pool=self.pool)

            # Test connection
            await self.client.ping()

            logger.info(
                "redis_connected",
                message="Redis connection established",
                host=self.settings.redis_host,
            )

        except (RedisConnectionError, RedisTimeoutError) as e:
            logger.error(
                "redis_connection_failed",
                message="Failed to connect to Redis",
                error=str(e),
                host=self.settings.redis_host,
                port=self.settings.redis_port,
            )
            raise

    async def disconnect(self) -> None:
        """Close Redis connection and clean up resources."""
        if self.client:
            try:
                await self.client.aclose()
                logger.info("redis_disconnected", message="Redis connection closed")
            except Exception as e:
                logger.error(
                    "redis_disconnect_error",
                    message="Error during Redis disconnect",
                    error=str(e),
                )

        if self.pool:
            try:
                await self.pool.aclose()
                logger.info("redis_pool_closed", message="Redis connection pool closed")
            except Exception as e:
                logger.error(
                    "redis_pool_close_error",
                    message="Error closing Redis connection pool",
                    error=str(e),
                )

    def get_client(self) -> Redis:
        """
        Get Redis client instance.

        Returns:
            Redis client

        Raises:
            RuntimeError: If client is not connected
        """
        if not self.client:
            raise RuntimeError("Redis client not connected. Call connect() first.")
        return self.client

    async def health_check(self) -> dict[str, Any]:
        """
        Check Redis connection health.

        Returns:
            dict: Health status with connection info
        """
        if not self.client:
            return {
                "status": "disconnected",
                "error": "Redis client not initialized",
            }

        try:
            # Test connection with ping
            await self.client.ping()

            # Get server info
            info = await self.client.info("server")

            return {
                "status": "healthy",
                "redis_version": info.get("redis_version", "unknown"),
                "uptime_seconds": info.get("uptime_in_seconds", 0),
                "connected_clients": info.get("connected_clients", 0),
            }

        except Exception as e:
            logger.error(
                "redis_health_check_failed",
                message="Redis health check failed",
                error=str(e),
            )
            return {
                "status": "unhealthy",
                "error": str(e),
            }


class RedisSyncClient:
    """
    Synchronous Redis client wrapper with connection pooling.

    Provides blocking Redis operations compatible with synchronous code.
    """

    def __init__(self, settings: Settings) -> None:
        """
        Initialize synchronous Redis client.

        Args:
            settings: Application settings with Redis configuration
        """
        self.settings = settings
        self.pool: SyncConnectionPool | None = None
        self.client: SyncRedis | None = None

        logger.info(
            "redis_sync_client_init",
            message="Synchronous Redis client initialized",
            host=settings.redis_host,
            port=settings.redis_port,
            db=settings.redis_db,
            max_connections=settings.redis_max_connections,
        )

    def connect(self, max_retries: int = 5, retry_delay: float = 1.0) -> None:
        """
        Establish Redis connection with connection pooling and retry logic.

        Includes DNS fallback: if hostname resolution fails, attempts to use
        fallback IP address if configured.

        Args:
            max_retries: Maximum number of connection attempts
            retry_delay: Delay in seconds between retries

        Raises:
            RedisConnectionError: If all connection attempts fail
        """
        import time

        last_error = None
        hosts_to_try = [self.settings.redis_host]

        # Add fallback IP if configured
        if self.settings.redis_fallback_ip:
            hosts_to_try.append(self.settings.redis_fallback_ip)

        for attempt in range(1, max_retries + 1):
            for host_index, host in enumerate(hosts_to_try):
                try:
                    is_fallback = host_index > 0
                    log_message = f"Attempting Redis connection (attempt {attempt}/{max_retries})"
                    if is_fallback:
                        log_message += f" using fallback IP {host}"

                    logger.info(
                        "redis_sync_connect_attempt",
                        message=log_message,
                        host=host,
                        is_fallback=is_fallback,
                    )

                    # Build Redis URL for this host
                    if self.settings.redis_password:
                        redis_url = f"redis://:{self.settings.redis_password}@{host}:{self.settings.redis_port}/{self.settings.redis_db}"
                    else:
                        redis_url = f"redis://{host}:{self.settings.redis_port}/{self.settings.redis_db}"

                    # Create connection pool
                    self.pool = SyncConnectionPool.from_url(
                        redis_url,
                        max_connections=self.settings.redis_max_connections,
                        decode_responses=False,
                        socket_connect_timeout=5,
                        socket_timeout=5,
                    )

                    # Create Redis client
                    self.client = SyncRedis(connection_pool=self.pool)

                    # Test connection
                    self.client.ping()

                    logger.info(
                        "redis_sync_connected",
                        message=f"Synchronous Redis connection established (attempt {attempt})",
                        host=host,
                        is_fallback=is_fallback,
                    )

                    return  # Success!

                except (RedisConnectionError, RedisTimeoutError, OSError) as e:
                    last_error = e
                    error_str = str(e)

                    # Check if it's a DNS error
                    is_dns_error = "Name or service not known" in error_str or "Temporary failure in name resolution" in error_str

                    logger.warning(
                        "redis_sync_connection_attempt_failed",
                        message=f"Connection attempt {attempt}/{max_retries} failed",
                        error=error_str,
                        host=host,
                        port=self.settings.redis_port,
                        is_dns_error=is_dns_error,
                        is_fallback=is_fallback,
                    )

                    # If DNS error and this was the hostname, try fallback IP immediately
                    if is_dns_error and not is_fallback and self.settings.redis_fallback_ip:
                        continue  # Try next host (fallback IP)

                    # Otherwise break inner loop and retry
                    break

            # Delay before next attempt
            if attempt < max_retries:
                time.sleep(retry_delay)

        # All attempts exhausted
        logger.error(
            "redis_sync_connection_failed",
            message=f"Failed to connect to Redis after {max_retries} attempts",
            error=str(last_error),
            hosts_tried=hosts_to_try,
            port=self.settings.redis_port,
        )
        raise last_error

    def disconnect(self) -> None:
        """Close Redis connection and clean up resources."""
        if self.client:
            try:
                self.client.close()
                logger.info("redis_sync_disconnected", message="Synchronous Redis connection closed")
            except Exception as e:
                logger.error(
                    "redis_sync_disconnect_error",
                    message="Error during synchronous Redis disconnect",
                    error=str(e),
                )

        if self.pool:
            try:
                self.pool.disconnect()
                logger.info("redis_sync_pool_closed", message="Synchronous Redis connection pool closed")
            except Exception as e:
                logger.error(
                    "redis_sync_pool_close_error",
                    message="Error closing synchronous Redis connection pool",
                    error=str(e),
                )

    def get_client(self) -> SyncRedis:
        """
        Get synchronous Redis client instance.

        Returns:
            Synchronous Redis client

        Raises:
            RuntimeError: If client is not connected
        """
        if not self.client:
            raise RuntimeError("Synchronous Redis client not connected. Call connect() first.")
        return self.client

    def health_check(self) -> dict[str, Any]:
        """
        Check Redis connection health.

        Returns:
            dict: Health status with connection info
        """
        if not self.client:
            return {
                "status": "disconnected",
                "error": "Synchronous Redis client not initialized",
            }

        try:
            # Test connection with ping
            self.client.ping()

            # Get server info
            info = self.client.info("server")

            return {
                "status": "healthy",
                "redis_version": info.get("redis_version", "unknown"),
                "uptime_seconds": info.get("uptime_in_seconds", 0),
                "connected_clients": info.get("connected_clients", 0),
            }

        except Exception as e:
            logger.error(
                "redis_sync_health_check_failed",
                message="Synchronous Redis health check failed",
                error=str(e),
            )
            return {
                "status": "unhealthy",
                "error": str(e),
            }


# Global singleton instances
_redis_client: RedisClient | None = None
_redis_sync_client: RedisSyncClient | None = None


def initialize_redis(settings: Settings) -> RedisClient:
    """
    Initialize global Redis client singleton.

    Args:
        settings: Application settings

    Returns:
        RedisClient instance
    """
    global _redis_client

    if _redis_client is None:
        _redis_client = RedisClient(settings)
        logger.info("redis_singleton_created", message="Redis singleton initialized")

    return _redis_client


def get_redis_client() -> RedisClient:
    """
    Get global Redis client instance.

    Returns:
        RedisClient: Global Redis client

    Raises:
        RuntimeError: If Redis client not initialized
    """
    if _redis_client is None:
        raise RuntimeError(
            "Redis client not initialized. Call initialize_redis() first."
        )

    return _redis_client


def initialize_redis_sync(settings: Settings) -> RedisSyncClient:
    """
    Initialize global synchronous Redis client singleton.

    Args:
        settings: Application settings

    Returns:
        RedisSyncClient instance
    """
    global _redis_sync_client

    if _redis_sync_client is None:
        _redis_sync_client = RedisSyncClient(settings)
        logger.info("redis_sync_singleton_created", message="Synchronous Redis singleton initialized")

    return _redis_sync_client


def get_redis_sync_client() -> RedisSyncClient:
    """
    Get global synchronous Redis client instance.

    Returns:
        RedisSyncClient: Global synchronous Redis client

    Raises:
        RuntimeError: If synchronous Redis client not initialized
    """
    if _redis_sync_client is None:
        raise RuntimeError(
            "Synchronous Redis client not initialized. Call initialize_redis_sync() first."
        )

    return _redis_sync_client
