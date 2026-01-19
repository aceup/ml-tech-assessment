"""
Custom exceptions and global exception handlers.

Provides consistent error responses across the API.
"""

from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.backend.core.logging import get_logger

logger = get_logger(__name__)


class ErrorResponse(BaseModel):
    """Standard error response model."""

    error: str
    message: str
    request_id: str | None = None
    details: dict[str, Any] | None = None


class AppException(Exception):
    """Base exception for application errors."""

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: dict[str, Any] | None = None,
    ):
        self.message = message
        self.status_code = status_code
        self.details = details
        super().__init__(message)


class NotFoundException(AppException):
    """Exception raised when a resource is not found."""

    def __init__(self, resource: str, identifier: str):
        super().__init__(
            message=f"{resource} with id '{identifier}' not found",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"resource": resource, "identifier": identifier},
        )


class ValidationException(AppException):
    """Exception raised for validation errors."""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            details=details,
        )


class ExternalServiceException(AppException):
    """Exception raised when an external service fails."""

    def __init__(self, service: str, message: str, details: dict[str, Any] | None = None):
        super().__init__(
            message=f"{service} error: {message}",
            status_code=status.HTTP_502_BAD_GATEWAY,
            details={"service": service, **(details or {})},
        )


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Handle custom application exceptions."""
    request_id = getattr(request.state, "request_id", None)

    logger.error(
        "app_exception",
        request_id=request_id,
        error=exc.message,
        status_code=exc.status_code,
        details=exc.details,
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=type(exc).__name__,
            message=exc.message,
            request_id=request_id,
            details=exc.details,
        ).model_dump(exclude_none=True),
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """
    Handle Pydantic validation errors.

    Returns FastAPI's standard validation error format for compatibility.
    """
    request_id = getattr(request.state, "request_id", None)

    logger.warning(
        "validation_error",
        request_id=request_id,
        errors=exc.errors(),
    )

    # Serialize validation errors properly to handle non-JSON-serializable objects
    # like ValueError instances in the context
    def serialize_error(error: dict) -> dict:
        """Convert error dict to JSON-serializable format."""
        serialized = error.copy()
        # Handle context field which may contain non-serializable objects
        if "ctx" in serialized and isinstance(serialized["ctx"], dict):
            serialized["ctx"] = {
                k: str(v) if not isinstance(v, (str, int, float, bool, type(None))) else v
                for k, v in serialized["ctx"].items()
            }
        return serialized

    # Return FastAPI's standard validation error format with request_id for consistency
    response_content = {"detail": [serialize_error(err) for err in exc.errors()]}
    if request_id:
        response_content["request_id"] = request_id

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content=response_content,
        headers={"X-Request-ID": request_id} if request_id else {},
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions."""
    request_id = getattr(request.state, "request_id", None)

    logger.error(
        "unhandled_exception",
        request_id=request_id,
        error=str(exc),
        error_type=type(exc).__name__,
        exc_info=True,
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error="InternalServerError",
            message="An unexpected error occurred",
            request_id=request_id,
        ).model_dump(exclude_none=True),
    )


def setup_exception_handlers(app: FastAPI) -> None:
    """
    Register all exception handlers with the FastAPI app.

    Args:
        app: FastAPI application instance
    """
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
