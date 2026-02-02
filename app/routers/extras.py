from fastapi import APIRouter, Depends

from app.dependencies import get_summary_repository
from app.ports.summary_repository import SummaryRepository

router = APIRouter(prefix="/extras", tags=["extras"])


@router.get(
    "/get_summaries_ids",
    response_model=list[str],
    summary="Retrieve list of all summary IDs",
    description=(
        "Fetches a list containing the unique IDs of all summaries that have been generated and stored "
        "in the repository. This endpoint provides a simple way to enumerate all available summaries for later retrieval."
    ),
)
async def get_summaries_ids(
    repository: SummaryRepository = Depends(get_summary_repository),
) -> list[str]:
    return repository.list_ids()
