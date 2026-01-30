"""Tests for API routes."""

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.adapters.in_memory_repo import InMemoryTranscriptRepository
from app.api.dependencies import get_repository, get_transcript_service
from app.application.dtos import AnalysisLLMResponse
from app.application.services import TranscriptService
from app.main import app
from app.ports.llm import LLm
from app.ports.repository import TranscriptRepository


class MockLLm(LLm):
    """Mock LLM adapter for testing."""

    def run_completion(self, system_prompt: str, user_prompt: str, dto: type) -> AnalysisLLMResponse:
        return AnalysisLLMResponse(
            summary="Test summary",
            action_items=["Action 1", "Action 2"],
        )

    async def run_completion_async(self, system_prompt: str, user_prompt: str, dto: type) -> AnalysisLLMResponse:
        return AnalysisLLMResponse(
            summary="Test summary async",
            action_items=["Async Action 1", "Async Action 2"],
        )


@pytest.fixture
def test_repository() -> TranscriptRepository:
    """Create a fresh repository for each test."""
    return InMemoryTranscriptRepository()


@pytest.fixture
def mock_service(test_repository: TranscriptRepository) -> TranscriptService:
    """Create a service with mock LLM."""
    return TranscriptService(llm=MockLLm(), repository=test_repository)


@pytest.fixture
def client(mock_service: TranscriptService, test_repository: TranscriptRepository) -> TestClient:
    """Create test client with dependency overrides."""
    app.dependency_overrides[get_transcript_service] = lambda: mock_service
    app.dependency_overrides[get_repository] = lambda: test_repository
    yield TestClient(app)
    app.dependency_overrides.clear()


class TestAnalyzeEndpoint:
    """Tests for POST /transcripts/analyze."""

    def test_analyze_success(self, client: TestClient) -> None:
        """Should return analysis with 201 status."""
        response = client.post(
            "/transcripts/analyze",
            json={"transcript": "Sample transcript content"},
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert "id" in data
        assert data["summary"] == "Test summary"
        assert data["action_items"] == ["Action 1", "Action 2"]

    def test_analyze_empty_transcript(self, client: TestClient) -> None:
        """Should return 422 for empty transcript."""
        response = client.post(
            "/transcripts/analyze",
            json={"transcript": ""},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_analyze_missing_transcript(self, client: TestClient) -> None:
        """Should return 422 for missing transcript field."""
        response = client.post(
            "/transcripts/analyze",
            json={},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestGetByIdEndpoint:
    """Tests for GET /transcripts/{transcript_id}."""

    def test_get_existing_analysis(self, client: TestClient) -> None:
        """Should return analysis for existing ID."""
        # First create an analysis
        create_response = client.post(
            "/transcripts/analyze",
            json={"transcript": "Sample transcript"},
        )
        analysis_id = create_response.json()["id"]

        # Then retrieve it
        response = client.get(f"/transcripts/{analysis_id}")

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["id"] == analysis_id

    def test_get_nonexistent_analysis(self, client: TestClient) -> None:
        """Should return 404 for non-existent ID."""
        response = client.get("/transcripts/nonexistent-id")

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()["detail"] == "Transcript analysis not found"


class TestBatchAnalyzeEndpoint:
    """Tests for POST /transcripts/analyze/batch."""

    def test_batch_analyze_success(self, client: TestClient) -> None:
        """Should analyze multiple transcripts concurrently."""
        response = client.post(
            "/transcripts/analyze/batch",
            json={"transcripts": ["Transcript 1", "Transcript 2"]},
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert len(data["results"]) == 2
        assert all("id" in result for result in data["results"])

    def test_batch_analyze_empty_list(self, client: TestClient) -> None:
        """Should return 422 for empty transcripts list."""
        response = client.post(
            "/transcripts/analyze/batch",
            json={"transcripts": []},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_batch_analyze_with_empty_transcript(self, client: TestClient) -> None:
        """Should return 422 when any transcript is empty."""
        response = client.post(
            "/transcripts/analyze/batch",
            json={"transcripts": ["Valid transcript", ""]},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestHealthEndpoint:
    """Tests for GET /health."""

    def test_health_check(self, client: TestClient) -> None:
        """Should return healthy status."""
        response = client.get("/health")

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {"status": "healthy"}
