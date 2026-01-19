"""
API security utilities.

Provides API key authentication for endpoint protection.
"""

from typing import Annotated

from fastapi import Header, HTTPException, status

from app.backend.core.config import get_settings
from app.backend.core.logging import get_logger

logger = get_logger(__name__)


async def verify_api_key(
    x_api_key: Annotated[str | None, Header()] = None,
) -> None:
    """
    Verify API key from request header.

    Checks the X-API-Key header against the configured API key.
    If no API key is configured in settings, authentication is disabled.

    Args:
        x_api_key: API key from X-API-Key header

    Raises:
        HTTPException: 401 if API key is missing or invalid

    Example:
        ```python
        @router.get("/protected", dependencies=[Depends(verify_api_key)])
        async def protected_endpoint():
            return {"message": "Access granted"}
        ```
    """
    settings = get_settings()

    # If no API key configured, skip authentication
    if not settings.api_key:
        return

    # Check if API key is provided
    if not x_api_key:
        logger.warning(
            "api_key_missing",
            message="API key missing in request",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required. Provide X-API-Key header.",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    # Verify API key matches
    if x_api_key != settings.api_key:
        logger.warning(
            "api_key_invalid",
            message="Invalid API key provided",
            provided_key_prefix=x_api_key[:8] if len(x_api_key) >= 8 else "***",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    logger.debug(
        "api_key_valid",
        message="API key authentication successful",
    )
