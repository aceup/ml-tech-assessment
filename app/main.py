"""FastAPI application entry point."""

from fastapi import FastAPI

from app.api.routes import router

app = FastAPI(
    title="Transcript Analysis API",
    description="API for analyzing coaching session transcripts using AI",
    version="1.0.0",
)

app.include_router(router)


@app.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy"}
