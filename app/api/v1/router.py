"""
API v1 router aggregator.

Combines all v1 endpoint routers.
"""

from fastapi import APIRouter

from app.api.v1.endpoints import analyses, health

# Create v1 router
router = APIRouter()

# Include all endpoint routers
router.include_router(health.router)
router.include_router(analyses.router)
