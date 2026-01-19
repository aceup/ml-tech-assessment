"""
FastAPI application factory.

Creates and configures the FastAPI application with all middleware and routes.
"""

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from app.backend.api.v1 import router as api_v1_router
from app.backend.core.config import get_settings
from app.backend.core.logging import get_logger, setup_logging
from app.backend.core.middleware import RequestIDMiddleware, RequestLoggingMiddleware
from app.backend.core.rate_limiting import get_limiter, rate_limit_exceeded_handler
from app.backend.utils.exceptions import setup_exception_handlers

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """
    Application lifespan manager.

    Handles startup and shutdown events, including Redis initialization.
    """
    # Startup
    settings = get_settings()
    setup_logging(settings.log_level, settings.log_format)

    logger.info(
        "application_startup",
        environment=settings.environment,
        debug=settings.debug,
        version=settings.api_version,
        repository_backend=settings.repository_backend,
        rate_limiting_enabled=settings.enable_rate_limiting,
    )

    # Initialize Redis if using Redis backend
    redis_client = None
    if settings.repository_backend == "redis":
        try:
            from app.backend.infrastructure.redis_client import (
                get_redis_sync_client,
                initialize_redis_sync,
            )

            logger.info("redis_sync_initialization", message="Initializing synchronous Redis connection")
            redis_client = initialize_redis_sync(settings)
            redis_client.connect()
            logger.info("redis_sync_connected", message="Synchronous Redis connection established")
        except Exception as e:
            logger.error(
                "redis_sync_initialization_failed",
                message="Failed to initialize synchronous Redis",
                error=str(e),
            )
            # Don't fail startup - fall back to in-memory if needed
            logger.warning(
                "redis_sync_fallback",
                message="Continuing without Redis (check configuration)",
            )

    yield

    # Shutdown
    logger.info("application_shutdown", message="Shutting down application")

    # Disconnect Redis if connected
    if redis_client:
        try:
            redis_client.disconnect()
            logger.info("redis_sync_disconnected", message="Synchronous Redis connection closed")
        except Exception as e:
            logger.error(
                "redis_sync_disconnect_failed",
                message="Error disconnecting synchronous Redis",
                error=str(e),
            )


def create_app() -> FastAPI:
    """
    Application factory.

    Creates and configures a FastAPI application instance.

    Returns:
        Configured FastAPI application
    """
    settings = get_settings()

    # Create FastAPI app
    app = FastAPI(
        title=settings.api_title,
        version=settings.api_version,
        debug=settings.debug,
        docs_url=settings.docs_url,
        redoc_url=settings.redoc_url,
        lifespan=lifespan,
    )

    # Add rate limiting if enabled
    if settings.enable_rate_limiting:
        from slowapi.errors import RateLimitExceeded

        limiter = get_limiter()
        app.state.limiter = limiter
        app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

        logger.info(
            "rate_limiting_enabled",
            message="Rate limiting middleware enabled",
            default_limit=settings.rate_limit_default,
        )

    # Add middleware (ORDER MATTERS! Last added = first executed)
    # 1. GZip compression (outermost layer)
    if settings.enable_gzip:
        app.add_middleware(
            GZipMiddleware,
            minimum_size=1000,  # Only compress responses > 1KB
        )

    # 2. CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=settings.cors_allow_methods,
        allow_headers=settings.cors_allow_headers,
    )

    # 3. Request logging (needs request ID from next middleware)
    if settings.enable_request_logging:
        app.add_middleware(RequestLoggingMiddleware)

    # 4. Request ID generation (innermost layer - runs first)
    app.add_middleware(RequestIDMiddleware)

    # Include routers
    app.include_router(api_v1_router.router, prefix="/api/v1")

    # Setup exception handlers
    setup_exception_handlers(app)

    return app


# Create app instance
app = create_app()


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.is_development,
        log_level=settings.log_level.lower(),
    )
