"""
Rate limiting middleware using slowapi with Redis backend.

Provides configurable rate limits per endpoint to prevent API abuse.
"""

from functools import lru_cache
from typing import Callable

from fastapi import Request, Response
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.core.logging import get_logger

logger = get_logger(__name__)


def get_redis_url_for_limiter() -> str:
    """
    Get Redis URL for rate limiter.

    Returns:
        str: Redis connection URL, or empty string if Redis not configured
    """
    try:
        from app.core.config import get_settings

        settings = get_settings()

        # Only use Redis if rate limiting is enabled and backend is Redis
        if settings.enable_rate_limiting and settings.repository_backend == "redis":
            redis_url = settings.redis_url
            logger.info(
                "rate_limiter_redis_enabled",
                message="Rate limiter using Redis backend",
                redis_host=settings.redis_host,
            )
            return redis_url
        else:
            # Use in-memory storage (not recommended for production)
            logger.warning(
                "rate_limiter_memory_mode",
                message="Rate limiter using in-memory storage (not distributed)",
            )
            return ""

    except Exception as e:
        logger.error(
            "rate_limiter_config_error",
            message="Error configuring rate limiter, using in-memory",
            error=str(e),
        )
        return ""


def get_key_func(request: Request) -> str:
    """
    Generate rate limit key from request.

    Uses IP address as the identifier. Can be extended to use API keys,
    user IDs, or other identifiers.

    Args:
        request: FastAPI request object

    Returns:
        str: Rate limit key (IP address)
    """
    # Get client IP address
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # Take first IP if multiple proxies
        ip = forwarded_for.split(",")[0].strip()
    else:
        ip = get_remote_address(request)

    # Could extend to use API key or user ID:
    # api_key = request.headers.get("X-API-Key")
    # if api_key:
    #     return f"apikey:{api_key}"

    return f"ip:{ip}"


@lru_cache
def get_limiter() -> Limiter:
    """
    Get rate limiter instance (cached singleton).

    Returns:
        Limiter: Configured slowapi Limiter instance
    """
    from app.core.config import get_settings

    settings = get_settings()

    # Get Redis URL if enabled
    storage_uri = get_redis_url_for_limiter()

    # Create limiter with Redis or in-memory storage
    limiter = Limiter(
        key_func=get_key_func,
        default_limits=[settings.rate_limit_default],
        storage_uri=storage_uri if storage_uri else None,
        # Strategy: fixed window (simple and predictable)
        strategy="fixed-window",
        # Don't raise exceptions automatically (we'll handle in FastAPI)
        swallow_errors=False,
        # Headers to include in responses
        headers_enabled=True,
    )

    logger.info(
        "rate_limiter_initialized",
        message="Rate limiter initialized",
        default_limit=settings.rate_limit_default,
        storage="redis" if storage_uri else "memory",
    )

    return limiter


def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> Response:
    """
    Custom handler for rate limit exceeded errors.

    Args:
        request: FastAPI request
        exc: RateLimitExceeded exception

    Returns:
        Response: JSON error response with 429 status
    """
    logger.warning(
        "rate_limit_exceeded",
        message="Rate limit exceeded",
        path=request.url.path,
        method=request.method,
        client_ip=get_key_func(request),
        limit=str(exc.detail),
    )

    # Use slowapi's default handler which returns proper JSON
    return _rate_limit_exceeded_handler(request, exc)


def get_rate_limit_state() -> dict:
    """
    Get current rate limiter state (for health checks / debugging).

    Returns:
        dict: Rate limiter state information
    """
    try:
        from app.core.config import get_settings

        settings = get_settings()
        limiter = get_limiter()

        return {
            "enabled": settings.enable_rate_limiting,
            "default_limit": settings.rate_limit_default,
            "storage": "redis" if settings.repository_backend == "redis" else "memory",
            "strategy": "fixed-window",
        }
    except Exception as e:
        logger.error(
            "rate_limit_state_error",
            message="Error getting rate limit state",
            error=str(e),
        )
        return {"error": str(e)}
