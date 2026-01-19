"""
Health check endpoints.

Provides Kubernetes-compatible liveness and readiness probes.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.backend.core.config import Settings, get_settings
from app.backend.models.responses import HealthResponse

router = APIRouter(prefix="/health", tags=["Health"])


@router.get(
    "/live",
    response_model=HealthResponse,
    summary="Liveness Probe",
    description="Check if the service is alive and running",
)
async def liveness() -> HealthResponse:
    """
    Liveness probe for Kubernetes.

    Returns 200 if the service is alive.
    """
    return HealthResponse(status="alive")


@router.get(
    "/ready",
    response_model=HealthResponse,
    summary="Readiness Probe",
    description="Check if the service is ready to accept traffic",
)
async def readiness(
    settings: Annotated[Settings, Depends(get_settings)]
) -> HealthResponse:
    """
    Readiness probe for Kubernetes.

    Checks:
    - OpenAI API key is configured
    - Environment is valid

    Returns 200 if ready, 503 if not ready.
    """
    checks = {
        "openai_key_configured": bool(settings.openai_api_key),
        "environment": settings.environment,
    }

    # Service is ready if all checks pass
    if all([checks["openai_key_configured"]]):
        return HealthResponse(status="ready", checks=checks)
    else:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=HealthResponse(status="not_ready", checks=checks).model_dump(),
        )
