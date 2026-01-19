"""
Analytics endpoints for observability metrics.

Provides aggregated metrics for cost analysis, performance monitoring,
and quality tracking from human evaluations.
"""

import statistics
from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.dependencies import get_analysis_service
from app.core.logging import get_logger
from app.core.security import verify_api_key
from app.models.analytics import AnalyticsResponse
from app.services.analysis_service import AnalysisService

logger = get_logger(__name__)

router = APIRouter(
    prefix="/analytics",
    tags=["Analytics"],
    dependencies=[Depends(verify_api_key)],  # API key required
)

# Pricing per 1M tokens (hardcoded, update manually)
# Last updated: 2025-01-19
PRICING = {
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "llama-3.3-70b-versatile": {"input": 0.59, "output": 0.79},
}


def calculate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """
    Calculate cost in USD for a single LLM call.

    Args:
        model: Model name
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens

    Returns:
        Cost in USD
    """
    if model not in PRICING:
        # Default to most expensive pricing if model not found
        pricing = PRICING["gpt-4o"]
    else:
        pricing = PRICING[model]

    input_cost = (input_tokens / 1_000_000) * pricing["input"]
    output_cost = (output_tokens / 1_000_000) * pricing["output"]

    return input_cost + output_cost


@router.get(
    "/metrics",
    response_model=AnalyticsResponse,
    summary="Get Analytics Metrics",
    description="Get comprehensive observability metrics including cost, performance, and quality.",
)
async def get_metrics(
    service: Annotated[AnalysisService, Depends(get_analysis_service)],
) -> AnalyticsResponse:
    """
    Get comprehensive analytics metrics.

    Returns aggregated metrics across all analyses:
    - Cost Analysis: Total USD spent, cost per 1000 requests
    - Token Usage: Total and average input/output tokens
    - Performance: Latency percentiles (avg, p50, p95, p99)
    - Quality: Human evaluation scores and hallucination rates
    - Provider Breakdown: Distribution across LLM providers
    """
    analyses = service.list_all()

    # Filter analyses with observability data
    obs_analyses = [a for a in analyses if a.observability]

    if not obs_analyses:
        # No observability data yet
        return AnalyticsResponse(
            total_analyses=0,
            total_cost_usd=0.0,
            cost_per_1000_requests=0.0,
            total_input_tokens=0,
            total_output_tokens=0,
            avg_input_tokens=0.0,
            avg_output_tokens=0.0,
            avg_latency_ms=0.0,
            p50_latency_ms=0.0,
            p95_latency_ms=0.0,
            p99_latency_ms=0.0,
            total_evaluations=0,
            avg_score=None,
            hallucination_rate=None,
            provider_breakdown={},
        )

    # Calculate cost metrics
    total_cost = 0.0
    total_input_tokens = 0
    total_output_tokens = 0
    latencies = []
    provider_counts: dict[str, int] = {}

    for analysis in obs_analyses:
        obs = analysis.observability
        if obs:
            # Accumulate token counts
            total_input_tokens += obs.input_tokens
            total_output_tokens += obs.output_tokens

            # Calculate cost
            cost = calculate_cost(obs.llm_model, obs.input_tokens, obs.output_tokens)
            total_cost += cost

            # Collect latency
            latencies.append(obs.latency_ms)

            # Count providers
            provider_counts[obs.llm_provider] = provider_counts.get(obs.llm_provider, 0) + 1

    # Calculate averages
    count = len(obs_analyses)
    avg_input_tokens = total_input_tokens / count
    avg_output_tokens = total_output_tokens / count
    avg_latency_ms = statistics.mean(latencies)

    # Calculate cost per 1000 requests
    cost_per_1000 = (total_cost / count) * 1000 if count > 0 else 0.0

    # Calculate latency percentiles
    sorted_latencies = sorted(latencies)
    p50_latency_ms = statistics.median(sorted_latencies)
    p95_latency_ms = statistics.quantiles(sorted_latencies, n=20)[18]  # 95th percentile
    p99_latency_ms = statistics.quantiles(sorted_latencies, n=100)[98]  # 99th percentile

    # Get evaluation metrics
    evaluations = service.repository.list_evaluations()
    total_evaluations = len(evaluations)
    avg_score = None
    hallucination_rate = None

    if total_evaluations > 0:
        scores = [e.score for e in evaluations]
        avg_score = statistics.mean(scores)

        hallucination_count = sum(1 for e in evaluations if e.is_hallucination)
        hallucination_rate = (hallucination_count / total_evaluations) * 100

    logger.info(
        "analytics_metrics_calculated",
        total_analyses=count,
        total_cost_usd=total_cost,
        total_evaluations=total_evaluations,
    )

    return AnalyticsResponse(
        total_analyses=count,
        total_cost_usd=round(total_cost, 4),
        cost_per_1000_requests=round(cost_per_1000, 4),
        total_input_tokens=total_input_tokens,
        total_output_tokens=total_output_tokens,
        avg_input_tokens=round(avg_input_tokens, 2),
        avg_output_tokens=round(avg_output_tokens, 2),
        avg_latency_ms=round(avg_latency_ms, 2),
        p50_latency_ms=round(p50_latency_ms, 2),
        p95_latency_ms=round(p95_latency_ms, 2),
        p99_latency_ms=round(p99_latency_ms, 2),
        total_evaluations=total_evaluations,
        avg_score=round(avg_score, 2) if avg_score is not None else None,
        hallucination_rate=round(hallucination_rate, 2) if hallucination_rate is not None else None,
        provider_breakdown=provider_counts,
    )
