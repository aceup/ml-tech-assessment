from contextlib import asynccontextmanager

import fastapi
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from openai import (
    AuthenticationError,
    BadRequestError,
    OpenAIError,
)

from app.dependencies import set_summary_repository
from app.repositories.in_memory import InMemorySummaryRepository
from app.routers import extras, summary


@asynccontextmanager
async def lifespan(app: FastAPI):
    repository = InMemorySummaryRepository()
    set_summary_repository(repository)

    yield


app = fastapi.FastAPI(lifespan=lifespan)


def _openai_error_response(
    request: Request, status_code: int, detail: str, exception: Exception
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"detail": detail},
    )


@app.exception_handler(AuthenticationError)
async def auth_handler(request: Request, exc: AuthenticationError) -> JSONResponse:
    return _openai_error_response(request, 401, "Invalid API credentials.", exc)


@app.exception_handler(BadRequestError)
async def bad_request_handler(request: Request, exc: BadRequestError) -> JSONResponse:
    return _openai_error_response(request, 400, "Invalid request to LLM service.", exc)


# Fallback for any other OpenAI error
@app.exception_handler(OpenAIError)
async def openai_error_handler(request: Request, exc: OpenAIError) -> JSONResponse:
    return _openai_error_response(
        request, 503, "LLM service error. Please retry later.", exc
    )


app.include_router(summary.router)
app.include_router(extras.router)


@app.get("/")
def read_root():
    return {"Hello": "World"}


if __name__ == "__main__":
    fastapi.run(app, host="[IP_ADDRESS]", port=8000)
