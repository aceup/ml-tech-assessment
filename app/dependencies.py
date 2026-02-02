from fastapi import HTTPException

from app.adapters.openai import OpenAIAdapter
from app.configurations import settings
from app.ports.llm import LLm
from app.ports.summary_repository import SummaryRepository


def get_llm_service_openai() -> LLm:
    return OpenAIAdapter(model=settings.OPENAI_MODEL, api_key=settings.OPENAI_API_KEY)


_summary_repository: SummaryRepository | None = None


def get_summary_repository() -> SummaryRepository:
    if _summary_repository is None:
        raise HTTPException(status_code=503, detail="Service temporarily unavailable")
    return _summary_repository


def set_summary_repository(repository: SummaryRepository) -> None:
    global _summary_repository
    _summary_repository = repository
