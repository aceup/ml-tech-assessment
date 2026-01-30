"""DTOs for LLM structured output responses."""

import pydantic


class AnalysisLLMResponse(pydantic.BaseModel):
    """Response structure expected from the LLM analysis."""

    summary: str
    action_items: list[str]
