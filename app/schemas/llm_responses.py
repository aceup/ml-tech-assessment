from pydantic import BaseModel, Field


class SummaryLLMOutput(BaseModel):
    content: str = Field(examples=["Summary of the text provided"])
    ctas: list[str] = Field(
        examples=["1) First call to action 2) Second call to action"]
    )
