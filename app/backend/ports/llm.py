import pydantic
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class LLMResponse:
    """Structured LLM response with observability metadata."""

    parsed_result: pydantic.BaseModel
    raw_response: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    latency_ms: float
    model: str
    provider: str


class LLm(ABC):
    @abstractmethod
    def run_completion(self, system_prompt: str, user_prompt: str, dto: type[pydantic.BaseModel]) -> pydantic.BaseModel:
        pass

    @abstractmethod
    async def run_completion_async(
        self,
        system_prompt: str,
        user_prompt: str,
        dto: type[pydantic.BaseModel],
    ) -> LLMResponse:
        """Execute async completion with observability metadata."""
        pass
