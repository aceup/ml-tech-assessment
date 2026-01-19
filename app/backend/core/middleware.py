"""
Custom middleware for request handling.

Provides request ID tracking and request/response logging.
"""

import time
import uuid
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.backend.core.logging import get_logger

logger = get_logger(__name__)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware to generate or extract X-Request-ID header.

    Ensures every request has a unique identifier for tracking and correlation.
    """

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Response]
    ) -> Response:
        # Get request ID from header or generate new one
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

        # Store in request state for access by other middleware/endpoints
        request.state.request_id = request_id

        # Process request
        response = await call_next(request)

        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id

        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log request start and completion with timing.

    Logs structured data including request ID, method, path, status code, and duration.
    """

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Response]
    ) -> Response:
        # Start timing
        start_time = time.time()

        # Get request ID from state (set by RequestIDMiddleware)
        request_id = getattr(request.state, "request_id", "unknown")

        # Bind context to logger for this request
        log = logger.bind(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            client_host=request.client.host if request.client else None,
        )

        # Log request start
        log.info("request_started")

        # Process request and capture any exceptions
        try:
            response = await call_next(request)
        except Exception as exc:
            # Calculate duration even for failed requests
            duration_ms = round((time.time() - start_time) * 1000, 2)

            log.error(
                "request_failed",
                duration_ms=duration_ms,
                error=str(exc),
                error_type=type(exc).__name__,
            )
            raise

        # Calculate duration
        duration_ms = round((time.time() - start_time) * 1000, 2)

        # Log request completion
        log.info(
            "request_completed",
            status_code=response.status_code,
            duration_ms=duration_ms,
        )

        return response
