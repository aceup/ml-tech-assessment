"""
Analytics models for aggregated metrics.

Provides comprehensive observability metrics including cost analysis,
token usage, performance metrics, and quality scores from human evaluations.
"""

from pydantic import BaseModel


class AnalyticsResponse(BaseModel):
    """Aggregated analytics and metrics."""

    # Cost Analysis
    total_analyses: int
    total_cost_usd: float
    cost_per_1000_requests: float

    # Token Usage
    total_input_tokens: int
    total_output_tokens: int
    avg_input_tokens: float
    avg_output_tokens: float

    # Performance
    avg_latency_ms: float
    p50_latency_ms: float  # Median
    p95_latency_ms: float
    p99_latency_ms: float

    # Quality (from HUMAN evaluations)
    total_evaluations: int = 0
    avg_score: float | None = None  # Average of human ratings
    hallucination_rate: float | None = None  # Percentage humans flagged

    # Provider breakdown
    provider_breakdown: dict[str, int] = {}
