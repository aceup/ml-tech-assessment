import asyncio
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query

from app.dependencies import get_llm_service_openai, get_summary_repository
from app.domain.entities import Summary
from app.ports.llm import LLm
from app.ports.summary_repository import SummaryRepository
from app.prompts import RAW_USER_PROMPT, SYSTEM_PROMPT
from app.schemas.llm_responses import SummaryLLMOutput
from app.schemas.requests import TextToSummary
from app.schemas.responses import (
    BatchSummaryItem,
    BatchSummaryResponse,
    SummaryResponse,
)

router = APIRouter(prefix="/summary_maker", tags=["summary_maker"])


@router.get(
    "/get_summary_and_ctas",
    response_model=SummaryResponse,
    summary="Gets the summary and calls to action (CTAs) for a given text.",
    description=(
        "Provides a summary and actionable CTAs for a supplied text. "
        "This endpoint accepts a text input, processes it via the LLM service, "
        "and returns a structured response containing the generated summary and a list of CTAs. "
        "The summary is designed to encapsulate the key ideas, while the CTAs are actionable recommendations "
        "or next steps derived from the content."
    ),
)
async def get_summary_and_ctas(
    text_to_summary: TextToSummary = Query(
        ...,
        description="The transcript text to analyze",
        example="This is a sample transcript discussing project goals...",
    ),
    llm: LLm = Depends(get_llm_service_openai),
    repository: SummaryRepository = Depends(get_summary_repository),
) -> SummaryResponse:
    llm_result = llm.run_completion(
        SYSTEM_PROMPT,
        RAW_USER_PROMPT.format(transcript=str(text_to_summary)),
        dto=SummaryLLMOutput,
    )

    summary_entity = Summary(
        id=str(uuid4()), content=llm_result.content, ctas=llm_result.ctas
    )

    repository.save(summary_entity)

    return SummaryResponse.from_entity(summary_entity)


@router.get(
    "/get_summary_and_ctas_by_id",
    response_model=Summary,
    summary="Retrieve a summary and CTAs by its unique ID.",
    description=(
        "Fetches a previously generated summary and its associated calls to action (CTAs) "
        "using the provided summary ID. This endpoint allows consumers to retrieve the summary content "
        "and actionable CTAs for a specific document or text that was processed earlier and stored in the repository."
    ),
)
async def get_summary_and_ctas_by_id(
    id: str, repository: SummaryRepository = Depends(get_summary_repository)
) -> Summary:
    summary = repository.get_by_id(id)

    if summary is None:
        raise HTTPException(status_code=404, detail="Summary not found")
    return summary


@router.post(
    "/async_get_summary_and_ctas",
    response_model=BatchSummaryResponse,
    summary="Asynchronously generate summaries and CTAs for a batch of texts.",
    description=(
        "Accepts a list of texts and asynchronously processes each to generate a summary and actionable calls to action (CTAs) "
        "using the LLM service. Instead of handling requests one by one, this endpoint allows multiple texts to be summarized in parallel, "
        "returning a list of structured summary responses. Each response contains the summary and associated CTAs for the corresponding input text."
    ),
)
async def async_single_get_summary_and_ctas(
    list_of_texts_to_summarize: list[TextToSummary],
    llm: LLm = Depends(get_llm_service_openai),
    repository: SummaryRepository = Depends(get_summary_repository),
) -> BatchSummaryResponse:
    async def process_one_request(text_to_summarize: TextToSummary) -> Summary:
        llm_result = await llm.run_completion_async(
            SYSTEM_PROMPT,
            RAW_USER_PROMPT.format(transcript=str(text_to_summarize)),
            dto=SummaryLLMOutput,
        )

        summary_entity = Summary(
            id=str(uuid4()), content=llm_result.content, ctas=llm_result.ctas
        )

        repository.save(summary_entity)

        return summary_entity

    tasks = [process_one_request(item) for item in list_of_texts_to_summarize]
    raw_results = await asyncio.gather(*tasks, return_exceptions=True)
    items: list[BatchSummaryItem] = []
    for result in raw_results:
        if isinstance(result, BaseException):
            items.append(BatchSummaryItem(error=str(result)))
        else:
            items.append(BatchSummaryItem(summary=SummaryResponse.from_entity(result)))

    return BatchSummaryResponse(items=items)
