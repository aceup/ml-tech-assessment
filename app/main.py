from fastapi import FastAPI
from app.routes.endpoints import router, initialize_service

app = FastAPI(title="Transcript Analyzer API")

initialize_service()
app.include_router(router, prefix="/aceup")
