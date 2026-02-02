from pydantic import BaseModel, Field

from app.domain.entities import Summary


class SummaryResponse(BaseModel):
    id: str = Field(examples=["123-abc"])
    summary: str = Field(examples=["Summary of the text provided"])
    ctas: list[str] = Field(
        examples=["1) First call to action 2) Second call to action"]
    )

    @classmethod
    def from_entity(cls, entity: Summary):
        return cls(id=entity.id, summary=entity.content, ctas=entity.ctas)


class BatchSummaryItem(BaseModel):
    """Single item in a batch summary response — either success or error."""

    summary: SummaryResponse | None = None
    error: str | None = None


class BatchSummaryResponse(BaseModel):
    """Batch response with one entry per input, preserving order."""

    items: list[BatchSummaryItem]
