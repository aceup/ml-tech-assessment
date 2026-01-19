"""
Analysis endpoints for transcript processing.

Provides CRUD operations for transcript analysis.
"""

import asyncio
import uuid
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.backend.api.dependencies import get_analysis_service
from app.backend.models.evaluation import AnalysisEvaluation, EvaluationRequest
from app.backend.models.requests import AnalyzeTranscriptRequest, BatchAnalyzeRequest
from app.backend.models.responses import AnalysisResponse, BatchAnalysisResponse
from app.backend.services.analysis_service import AnalysisService
from app.backend.core.logging import get_logger
from app.backend.core.security import verify_api_key

logger = get_logger(__name__)

router = APIRouter(
    prefix="/analyses",
    tags=["Analyses"],
    dependencies=[Depends(verify_api_key)],  # API key required for all endpoints
)


@router.get(
    "/analyze",
    response_model=AnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyze Transcript",
    description="Analyze a single medical transcript using GET method with query parameter. "
    "This endpoint performs transcript analysis and returns computed insights (summary and next actions). "
    "The analysis result is also stored for later retrieval via the /analyses/{id} endpoint.",
)
async def analyze_transcript_get(
    transcript: Annotated[
        str,
        Query(
            min_length=10,
            max_length=10000,
            description="Medical transcript text to analyze",
            examples=["Patient reports persistent headaches for 3 days, worse in the morning. "
                     "No fever or visual disturbances. Taking ibuprofen with minimal relief."],
        ),
    ],
    service: Annotated[AnalysisService, Depends(get_analysis_service)],
    num_next_actions: Annotated[
        int,
        Query(
            ge=1,
            le=10,
            description="Number of next action items to generate (1-10)",
        ),
    ] = 3,
) -> AnalysisResponse:
    """
    Analyze a single medical transcript.

    This endpoint computes analysis results from the provided transcript. The result is returned
    immediately and also stored in memory for potential future retrieval.

    Processes the transcript through the LLM and returns:
    - Summary of key points
    - Recommended next actions
    - Unique analysis ID for retrieval

    Query Parameters:
    - transcript: Plain text medical transcript (10-10,000 characters)
    - num_next_actions: Number of next action items to generate (1-10, default: 3)
    """
    # Validate transcript is not just whitespace
    if not transcript.strip():
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Transcript cannot be empty or whitespace only"
        )

    return await service.analyze(transcript.strip(), num_next_actions)


@router.get(
    "/evaluations",
    response_model=list[AnalysisEvaluation],
    status_code=status.HTTP_200_OK,
    summary="List All Evaluations",
    description="Get all submitted evaluations/feedback for analyses.",
)
async def list_evaluations(
    service: Annotated[AnalysisService, Depends(get_analysis_service)],
) -> list[AnalysisEvaluation]:
    """
    List all evaluation feedback submitted for analyses.

    Returns all evaluations including scores, hallucination flags, and comments.
    """
    return service.repository.list_evaluations()


@router.get(
    "/{analysis_id}",
    response_model=AnalysisResponse,
    summary="Get Analysis by ID",
    description="Retrieve a previously completed analysis by its unique identifier",
)
async def get_analysis(
    analysis_id: str,
    service: Annotated[AnalysisService, Depends(get_analysis_service)],
) -> AnalysisResponse:
    """
    Get an analysis by ID.

    Returns the complete analysis result including:
    - Original transcript
    - Summary
    - Next actions
    - Created timestamp
    """
    return service.get_by_id(analysis_id)


@router.post(
    "/{analysis_id}/feedback",
    response_model=AnalysisEvaluation,
    status_code=status.HTTP_201_CREATED,
    summary="Submit Evaluation Feedback",
    description="Submit human feedback/evaluation for an analysis. "
    "This enables collecting quality ratings, hallucination flags, and comments "
    "from real users (doctors, coaches, QA teams) to build golden datasets.",
)
async def submit_evaluation(
    analysis_id: str,
    request: EvaluationRequest,
    service: Annotated[AnalysisService, Depends(get_analysis_service)],
) -> AnalysisEvaluation:
    """
    Submit user feedback/evaluation for an analysis.

    Human-in-the-loop evaluation system for tracking AI quality.
    Humans (doctors, coaches, QA) rate the analysis on:
    - Score: 1-5 stars
    - Hallucination: True if AI made things up
    - Comment: Optional written feedback

    This data builds golden datasets for prompt regression testing.
    """
    # Verify analysis exists
    service.get_by_id(analysis_id)

    # Create and save evaluation
    evaluation = AnalysisEvaluation(
        id=str(uuid.uuid4()),
        analysis_id=analysis_id,
        score=request.score,
        is_hallucination=request.is_hallucination,
        comment=request.comment,
        evaluated_at=datetime.now(UTC),
    )

    service.repository.save_evaluation(evaluation)

    logger.info(
        "evaluation_submitted",
        evaluation_id=evaluation.id,
        analysis_id=analysis_id,
        score=request.score,
        is_hallucination=request.is_hallucination,
    )

    return evaluation


@router.get(
    "",
    response_model=list[AnalysisResponse],
    summary="List All Analyses",
    description="Retrieve all stored analyses",
)
async def list_analyses(
    service: Annotated[AnalysisService, Depends(get_analysis_service)],
) -> list[AnalysisResponse]:
    """
    List all analyses.

    Returns all stored analysis results.
    """
    return service.list_all()


@router.post(
    "/batch",
    response_model=BatchAnalysisResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Batch Analyze Transcripts",
    description="Analyze multiple transcripts concurrently with rate limiting",
)
async def analyze_batch(
    request: BatchAnalyzeRequest,
    service: Annotated[AnalysisService, Depends(get_analysis_service)],
) -> BatchAnalysisResponse:
    """
    Analyze multiple transcripts in batch.

    Processes transcripts concurrently with a semaphore to limit concurrent requests.
    Maximum 5 concurrent analyses to prevent overwhelming the LLM API.

    Returns:
    - List of successful analysis results
    - Count of successful and failed analyses
    - List of error messages for failed analyses
    """
    # Semaphore to limit concurrent API calls
    semaphore = asyncio.Semaphore(5)

    logger.info(
        "batch_analysis_started",
        total_transcripts=len(request.transcripts),
        num_next_actions=request.num_next_actions,
    )

    async def analyze_with_limit(transcript: str) -> AnalysisResponse | Exception:
        """Analyze with concurrency limit."""
        async with semaphore:
            try:
                return await service.analyze(transcript, request.num_next_actions)
            except Exception as exc:
                return exc

    # Execute all analyses concurrently (but limited by semaphore)
    tasks = [analyze_with_limit(t) for t in request.transcripts]
    results = await asyncio.gather(*tasks)

    # Separate successes from failures
    successes: list[AnalysisResponse] = []
    errors: list[str] = []

    for i, result in enumerate(results):
        if isinstance(result, Exception):
            errors.append(f"Transcript {i + 1}: {str(result)}")
        else:
            successes.append(result)

    logger.info(
        "batch_analysis_completed",
        total=len(request.transcripts),
        successful=len(successes),
        failed=len(errors),
    )

    return BatchAnalysisResponse(
        results=successes,
        total=len(request.transcripts),
        successful=len(successes),
        failed=len(errors),
        errors=errors if errors else None,
    )
