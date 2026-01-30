"""API route definitions for transcript analysis."""

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_transcript_service
from app.api.schemas import (
    AnalyzeRequest,
    AnalyzeResponse,
    BatchAnalyzeRequest,
    BatchAnalyzeResponse,
)
from app.application.services import TranscriptService
from app.domain.models import TranscriptAnalysis

router = APIRouter(prefix="/transcripts", tags=["transcripts"])


def _to_response(analysis: TranscriptAnalysis) -> AnalyzeResponse:
    """Convert domain model to API response schema."""
    return AnalyzeResponse(
        id=analysis.id,
        summary=analysis.summary,
        action_items=analysis.action_items,
    )


@router.post(
    "/analyze",
    response_model=AnalyzeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Analyze a transcript",
    description="Analyzes a transcript and returns a summary with action items.",
)
def analyze_transcript(
    request: AnalyzeRequest,
    service: TranscriptService = Depends(get_transcript_service),
) -> AnalyzeResponse:
    """Analyze a single transcript."""
    analysis = service.analyze(request.transcript)
    return _to_response(analysis)


@router.get(
    "/{transcript_id}",
    response_model=AnalyzeResponse,
    summary="Get analysis by ID",
    description="Retrieves a previously analyzed transcript by its ID.",
)
def get_transcript(
    transcript_id: str,
    service: TranscriptService = Depends(get_transcript_service),
) -> AnalyzeResponse:
    """Retrieve a transcript analysis by ID."""
    analysis = service.get_by_id(transcript_id)
    if analysis is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transcript analysis not found",
        )
    return _to_response(analysis)


@router.post(
    "/analyze/batch",
    response_model=BatchAnalyzeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Analyze multiple transcripts",
    description="Analyzes multiple transcripts concurrently.",
)
async def analyze_batch(
    request: BatchAnalyzeRequest,
    service: TranscriptService = Depends(get_transcript_service),
) -> BatchAnalyzeResponse:
    """Analyze multiple transcripts concurrently."""
    analyses = await service.analyze_batch(request.transcripts)
    return BatchAnalyzeResponse(results=[_to_response(a) for a in analyses])
