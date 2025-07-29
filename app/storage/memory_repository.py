from typing import Dict
from app.models.transcript import AnalysisResult

class MemoryRepository:
    def __init__(self):
        self.db: Dict[str, AnalysisResult] = {}

    def save(self, result: AnalysisResult):
        self.db[result.id] = result

    def get(self, analysis_id: str):
        return self.db.get(analysis_id)
