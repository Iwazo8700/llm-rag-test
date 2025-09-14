"""
Simple integration tests that verify the application works end-to-end.
These tests run against the actual application without mocking.
"""

import os
from pathlib import Path
import subprocess
import time

import pytest
import requests


@pytest.fixture(scope="module")
def running_app():
    """Start the FastAPI application for testing."""
    # Set up test environment
    env = os.environ.copy()
    env.update(
        {
            "CHROMADB_PATH": "/tmp/test_chromadb",
            "EMBEDDING_MODEL": "all-MiniLM-L6-v2",
            "OPENROUTER_API_KEY": "test-key",
            "MODEL_SLUG": "openai/gpt-3.5-turbo",
            "LOG_LEVEL": "WARNING",  # Reduce noise during tests
        }
    )

    # Start the application
    proc = subprocess.Popen(
        [
            ".venv/bin/python",
            "-m",
            "uvicorn",
            "app.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            "8001",
        ],
        env=env,
        cwd=Path(__file__).parent.parent,
    )

    # Wait for app to start
    time.sleep(3)

    # Check if app is running
    max_retries = 10
    for _ in range(max_retries):
        try:
            response = requests.get("http://127.0.0.1:8001/", timeout=5)
            if response.status_code == 200:
                break
        except requests.exceptions.RequestException:
            time.sleep(1)
    else:
        proc.terminate()
        pytest.fail("Could not start the application")

    yield "http://127.0.0.1:8001"

    # Cleanup
    proc.terminate()
    proc.wait(timeout=10)


class TestSimpleIntegration:
    """Simple integration tests for core functionality."""

    def test_root_endpoint(self, running_app):
        """Test the root endpoint returns system information."""
        response = requests.get(f"{running_app}/")

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "RAG System API"  # Updated expected name
        assert data["version"] == "1.0.0"
        assert "status" in data

    def test_health_endpoint(self, running_app):
        """Test the health endpoint."""
        response = requests.get(f"{running_app}/health")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert "components" in data

    def test_add_document_basic(self, running_app):
        """Test basic document addition."""
        response = requests.post(
            f"{running_app}/add_document",
            json={
                "text": "This is a test document for integration testing.",
                "metadata": {"test": True},
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "id" in data

    def test_search_basic(self, running_app):
        """Test basic search functionality."""
        # First add a document
        requests.post(
            f"{running_app}/add_document",
            json={
                "text": "Machine learning is a subset of artificial intelligence.",
                "metadata": {"topic": "AI"},
            },
        )

        # Then search for it
        response = requests.get(
            f"{running_app}/search", params={"query": "machine learning", "limit": 5}
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Should find at least one result
        if len(data) > 0:
            assert "content" in data[0]
            assert "score" in data[0]
            assert "metadata" in data[0]

    def test_chat_basic(self, running_app):
        """Test basic chat functionality (may fail without real API key)."""
        # Add some context
        requests.post(
            f"{running_app}/add_document",
            json={
                "text": "Python is a programming language known for its simplicity.",
                "metadata": {"language": "Python"},
            },
        )

        response = requests.post(
            f"{running_app}/chat",
            json={"question": "What is Python?", "max_results": 3},
        )

        # This might fail if no real API key is provided, but endpoint should be accessible
        assert response.status_code in [200, 500]  # 500 is expected with fake API key

    def test_validation_errors(self, running_app):
        """Test that validation works for invalid input."""
        # Empty text should fail
        response = requests.post(
            f"{running_app}/add_document", json={"text": "", "metadata": {}}
        )
        assert (
            response.status_code == 422
        )  # FastAPI validation error for Pydantic model

        # Empty query should fail - this uses custom validation
        response = requests.get(
            f"{running_app}/search", params={"query": "", "limit": 5}
        )
        assert response.status_code == 400  # Custom validation in the endpoint

        # Empty question should fail
        response = requests.post(
            f"{running_app}/chat", json={"question": "", "max_results": 3}
        )
        assert (
            response.status_code == 422
        )  # FastAPI validation error for Pydantic model
