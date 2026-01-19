"""
Observability models for LLM operations.

Provides structured metadata capture for debugging, monitoring, and cost tracking.
"""

from pydantic import BaseModel


class ObservabilityMetadata(BaseModel):
    """Observability metadata for LLM operations."""

    # Pillar A: Traceability
    prompt_version: str = "v1.0"
    raw_system_prompt: str
    raw_user_prompt: str
    raw_llm_response: str
    request_id: str | None = None

    # Pillar B: Performance
    latency_ms: float
    input_tokens: int
    output_tokens: int
    total_tokens: int
    llm_provider: str  # "openai" or "groq"
    llm_model: str  # e.g., "gpt-4o"

    # Pillar C: Semantic Logging
    retry_count: int = 0
    validation_failures: list[str] = []
    pii_detected: bool = False
