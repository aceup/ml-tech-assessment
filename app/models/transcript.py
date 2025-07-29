from pydantic import BaseModel
from typing import List

class AnalysisResult(BaseModel):
    id: str
    summary: str
    action_items: List[str]

class StoredAnalysis(BaseModel):
    id: str
    summary: str
    action_items: List[str]
