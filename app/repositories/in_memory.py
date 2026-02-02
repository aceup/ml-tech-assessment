from app.domain.entities import Summary
from app.ports.summary_repository import SummaryRepository


class InMemorySummaryRepository(SummaryRepository):
    def __init__(self) -> None:
        self._store: dict[str, Summary] = {}

    def save(self, summary: Summary) -> None:
        self._store[str(summary.id)] = summary

    def get_by_id(self, id: str) -> Summary | None:
        return self._store.get(id)

    def list_ids(self) -> list[str]:
        return list(self._store.keys())
