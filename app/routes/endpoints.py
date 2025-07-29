from app.adapters.openai import OpenAIAdapter
from app.storage.memory_repository import MemoryRepository
from app.config.openai import EnvConfigs
from app.services.transcript_service import TranscriptService
from app.models.transcript import AnalysisResult

from fastapi import APIRouter, HTTPException, Query
from typing import List
import asyncio

router = APIRouter()
service: TranscriptService = None
env = EnvConfigs()

def initialize_service():
    global service
    service = TranscriptService(OpenAIAdapter(env.OPENAI_API_KEY, model=env.OPENAI_MODEL), MemoryRepository())

@router.get("/analyze", response_model=AnalysisResult)
def analyze(transcript: str = Query(..., min_length=1)):
    try:
        return service.analyze(transcript)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/transcript/{analysis_id}", response_model=AnalysisResult)
def get_transcript(analysis_id: str):
    result = service.get_by_id(analysis_id)
    if not result:
        raise HTTPException(status_code=404, detail="Transcript not found")
    return result

@router.post("/batch-analyze", response_model=List[AnalysisResult])
async def batch_analyze(transcripts: List[str]):
    async def task(text):
        return await asyncio.to_thread(service.analyze, text)
    tasks = [task(t) for t in transcripts if t.strip()]
    return await asyncio.gather(*tasks)
