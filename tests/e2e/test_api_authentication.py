"""
E2E tests for API key authentication.

Tests API key requirement on protected endpoints.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


class TestAPIKeyAuthentication:
    """Test API key authentication on protected endpoints."""

    @pytest.fixture
    def app_with_api_key(self):
        """Create app with API key enabled."""
        import os
        # Set API key in environment
        os.environ["API_KEY"] = "test-api-key-12345"

        app = create_app()
        yield app

        # Cleanup
        if "API_KEY" in os.environ:
            del os.environ["API_KEY"]

    @pytest.fixture
    def client_with_auth(self, app_with_api_key):
        """Create test client with API key auth enabled."""
        return TestClient(app_with_api_key)

    def test_request_without_api_key_returns_401(self, client_with_auth):
        """Test that requests without API key are rejected with 401."""
        response = client_with_auth.get("/api/v1/analyses")

        assert response.status_code == 401
        assert response.json() == {"detail": "API key required. Provide X-API-Key header."}

    def test_request_with_invalid_api_key_returns_401(self, client_with_auth):
        """Test that requests with invalid API key are rejected with 401."""
        response = client_with_auth.get(
            "/api/v1/analyses",
            headers={"X-API-Key": "wrong-key"}
        )

        assert response.status_code == 401
        assert response.json() == {"detail": "Invalid API key"}

    def test_request_with_valid_api_key_succeeds(self, client_with_auth):
        """Test that requests with valid API key succeed."""
        response = client_with_auth.get(
            "/api/v1/analyses",
            headers={"X-API-Key": "test-api-key-12345"}
        )

        # Should get 200, not 401
        assert response.status_code == 200
        # Should return empty list (no analyses yet)
        assert response.json() == []

    def test_health_endpoints_dont_require_api_key(self, client_with_auth):
        """Test that health endpoints work without API key."""
        # Health endpoints should be public
        live_response = client_with_auth.get("/api/v1/health/live")
        assert live_response.status_code == 200

        ready_response = client_with_auth.get("/api/v1/health/ready")
        assert ready_response.status_code == 200

    def test_docs_endpoints_dont_require_api_key(self, client_with_auth):
        """Test that documentation endpoints work without API key."""
        # Docs should be public
        docs_response = client_with_auth.get("/docs")
        assert docs_response.status_code == 200

        redoc_response = client_with_auth.get("/redoc")
        assert redoc_response.status_code == 200
