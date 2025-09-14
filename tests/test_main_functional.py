"""
Simple functional tests for the main FastAPI application.
These tests use TestClient with a clean app instance.
"""

from fastapi.testclient import TestClient
import pytest

from app.main import app


class TestMainAppFunctional:
    """Functional tests for the main FastAPI application."""

    @pytest.fixture
    def client(self):
        """Create a test client for the FastAPI app."""
        return TestClient(app)

    def test_root_endpoint_structure(self, client):
        """Test that the root endpoint has the expected structure."""
        # Note: This test doesn't mock anything, so it tests the actual app
        # It may fail if components aren't initialized, but tests the structure
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()

        # Test expected keys exist
        assert "name" in data
        assert "version" in data
        assert "status" in data

        # Status should be either "healthy" or "error"
        assert data["status"] in ["healthy", "error"]

        if data["status"] == "healthy":
            assert "components" in data
            assert "statistics" in data
        else:
            assert "error" in data

    def test_openapi_schema(self, client):
        """Test that the OpenAPI schema is accessible."""
        response = client.get("/openapi.json")
        assert response.status_code == 200

        schema = response.json()
        assert "openapi" in schema
        assert "info" in schema
        assert schema["info"]["title"] == "RAG System API"
        assert schema["info"]["version"] == "1.0.0"

    def test_docs_endpoint(self, client):
        """Test that the docs endpoint is accessible."""
        response = client.get("/docs")
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")

    def test_health_endpoint_structure(self, client):
        """Test that the health endpoint has the expected structure."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()

        # Test expected keys exist
        assert "status" in data
        assert "timestamp" in data

        # Status should be "healthy", "degraded", or "error"
        assert data["status"] in ["healthy", "degraded", "error"]

        # If not error, should have components
        if data["status"] != "error":
            assert "components" in data
            # Components should include database and embeddings
            assert "database" in data["components"]
            assert "embeddings" in data["components"]
        else:
            # Error response should have error field
            assert "error" in data

    def test_add_document_validation(self, client):
        """Test validation on add document endpoint."""
        # Test with missing text
        response = client.post("/add_document", json={})
        assert response.status_code == 422  # Validation error

        # Test with empty text (should be caught by custom validator)
        response = client.post("/add_document", json={"text": ""})
        assert response.status_code == 422  # Validation error

    def test_search_validation(self, client):
        """Test validation on search endpoint."""
        # Test with missing query
        response = client.get("/search")
        assert response.status_code == 422  # Missing required parameter

        # Test with invalid limit
        response = client.get("/search", params={"query": "test", "limit": 0})
        assert response.status_code == 422  # Validation error

        response = client.get("/search", params={"query": "test", "limit": 25})
        assert response.status_code == 422  # Validation error

    def test_chat_validation(self, client):
        """Test validation on chat endpoint."""
        # Test with missing question
        response = client.post("/chat", json={})
        assert response.status_code == 422  # Validation error

        # Test with invalid max_results
        response = client.post("/chat", json={"question": "test", "max_results": 0})
        assert response.status_code == 422  # Validation error

        response = client.post("/chat", json={"question": "test", "max_results": 15})
        assert response.status_code == 422  # Validation error


class TestMainAppWithMocking:
    """Tests using mocking to control component behavior."""

    def test_app_info_constants(self):
        """Test that app constants are correctly defined."""
        from app.config import config

        assert config.APP_NAME == "RAG System API"
        assert config.APP_VERSION == "1.0.0"
        assert hasattr(config, "MAX_SEARCH_RESULTS")
        assert hasattr(config, "MAX_CHAT_RESULTS")
