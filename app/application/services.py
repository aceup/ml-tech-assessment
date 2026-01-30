"""Application services for transcript analysis."""

import asyncio

from app.application.dtos import AnalysisLLMResponse
from app.domain.models import TranscriptAnalysis
from app.ports.llm import LLm
from app.ports.repository import TranscriptRepository
from app.prompts import RAW_USER_PROMPT, SYSTEM_PROMPT


class TranscriptService:
    """Orchestrates transcript analysis using LLM and repository."""

    def __init__(self, llm: LLm, repository: TranscriptRepository) -> None:
        self._llm = llm
        self._repository = repository

    def analyze(self, transcript: str) -> TranscriptAnalysis:
        """Analyze a transcript and persist the result."""
        user_prompt = RAW_USER_PROMPT.format(transcript=transcript)

        llm_response: AnalysisLLMResponse = self._llm.run_completion(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt,
            dto=AnalysisLLMResponse,
        )

        analysis = TranscriptAnalysis(
            summary=llm_response.summary,
            action_items=llm_response.action_items,
        )

        self._repository.save(analysis)
        return analysis

    async def analyze_async(self, transcript: str) -> TranscriptAnalysis:
        """Analyze a transcript asynchronously and persist the result."""
        user_prompt = RAW_USER_PROMPT.format(transcript=transcript)

        llm_response: AnalysisLLMResponse = await self._llm.run_completion_async(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt,
            dto=AnalysisLLMResponse,
        )

        analysis = TranscriptAnalysis(
            summary=llm_response.summary,
            action_items=llm_response.action_items,
        )

        self._repository.save(analysis)
        return analysis

    async def analyze_batch(self, transcripts: list[str]) -> list[TranscriptAnalysis]:
        """Analyze multiple transcripts concurrently."""
        tasks = [self.analyze_async(transcript) for transcript in transcripts]
        return await asyncio.gather(*tasks)

    def get_by_id(self, analysis_id: str) -> TranscriptAnalysis | None:
        """Retrieve an analysis by its ID."""
        return self._repository.get_by_id(analysis_id)
