from abc import ABC, abstractmethod

from app.domain.entities import Summary


class SummaryRepository(ABC):
    @abstractmethod
    def save(self, summary: Summary) -> None:
        pass

    @abstractmethod
    def get_by_id(self, id: str) -> Summary | None:
        pass

    @abstractmethod
    def list_ids(self) -> list[str]:
        pass
