
from uuid import uuid4

from app.models.transcript import AnalysisResult
from app.ports.llm import LLm
from app.storage.memory_repository import MemoryRepository
from app.prompts import SYSTEM_PROMPT, RAW_USER_PROMPT
from app.models.transcript import AnalysisResult
from app.models.transcript import StoredAnalysis

class TranscriptService:
    def __init__(self, llm_adapter, repository):
        self.llm_adapter = llm_adapter
        self.repository = repository

    def analyze(self, transcript: str) -> AnalysisResult:
        prompt = RAW_USER_PROMPT.format(transcript=transcript)

        response = self.llm_adapter.run_completion(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=prompt,
            dto=AnalysisResult
        )

        result = AnalysisResult(
            id=str(uuid4()),
            summary=response.summary,
            action_items=response.action_items
        )

        self.repository.save(result)
        return result
    
    def get_by_id(self, analysis_id: str) -> StoredAnalysis | None:
        return self.repository.get(analysis_id)
