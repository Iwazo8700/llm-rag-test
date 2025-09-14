"""
Unit tests for the main FastAPI application.
"""

from unittest.mock import Mock, patch

from fastapi.testclient import TestClient
import pytest

from app.database import ChromaDBManager
from app.embeddings import EmbeddingGenerator
import app.main as main_module

# Import app and main module directly
from app.main import app
from app.rag import RAGPipeline


class TestMainApp:
    """Test cases for the main FastAPI application."""

    @pytest.fixture
    def client(self):
        """Create a test client for the FastAPI app."""
        return TestClient(app)

    @pytest.fixture(autouse=True)
    def mock_startup(self):
        """Mock the startup process to avoid actual component initialization."""
        with patch("app.main.startup") as mock_startup_func:
            # Make startup async function do nothing
            mock_startup_func.return_value = None
            yield

    @pytest.fixture
    def mock_components(self):
        """Mock all system components."""
        # Create mock instances
        mock_db = Mock(spec=ChromaDBManager)
        mock_emb = Mock(spec=EmbeddingGenerator)
        mock_rag = Mock(spec=RAGPipeline)

        # Setup mock database
        mock_db.get_collection_stats.return_value = {
            "document_count": 10,
            "collection_name": "documents",
        }
        mock_db.add_document.return_value = "test-doc-id"
        mock_db.search.return_value = {
            "documents": ["Document 1", "Document 2"],
            "distances": [0.1, 0.2],
            "metadatas": [{"source": "test1"}, {"source": "test2"}],
        }

        # Setup mock embedding generator
        mock_emb.model_name = "all-MiniLM-L6-v2"
        mock_emb.use_fallback = False
        mock_emb.generate_embeddings.return_value = [[0.1] * 384]

        # Setup mock RAG pipeline
        mock_rag.model_slug = "openai/gpt-3.5-turbo"
        mock_rag.generate_answer.return_value = {
            "answer": "Test answer",
            "sources": [],
            "model_used": "openai/gpt-3.5-turbo",
            "tokens_used": 50,
            "processing_time": 1.5,
            "context_documents_found": 2,
        }

        # Patch the global variables in the main module
        with patch.object(main_module, "db_manager", mock_db, create=True), patch.object(
            main_module, "embedding_generator", mock_emb, create=True
        ), patch.object(main_module, "rag_pipeline", mock_rag, create=True):
            yield {"db": mock_db, "embeddings": mock_emb, "rag": mock_rag}

    def test_root_endpoint_success(self, client, mock_components):
        """Test the root endpoint returns system information."""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "RAG System API"
        assert data["version"] == "1.0.0"
        assert data["status"] == "healthy"
        assert "components" in data
        assert "statistics" in data

    def test_root_endpoint_with_error(self, client):
        """Test root endpoint when there's an error getting stats."""
        mock_db = Mock()
        mock_db.get_collection_stats.side_effect = Exception("Database error")

        with patch.object(main_module, "db_manager", mock_db, create=True):
            response = client.get("/")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "error"
            assert "error" in data

    def test_add_document_success(self, client, mock_components):
        """Test successful document addition."""
        mock_components["db"].add_document.return_value = "test-doc-id"

        response = client.post(
            "/add_document",
            json={"text": "Test document content", "metadata": {"source": "test"}},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["id"] == "test-doc-id"
        assert "message" in data
        assert "metadata" in data

    def test_add_document_empty_text(self, client, mock_components):
        """Test document addition with empty text."""
        response = client.post("/add_document", json={"text": "", "metadata": {}})

        assert response.status_code == 422
        assert "empty" in response.json()["detail"][0]["msg"].lower()

    def test_add_document_too_long(self, client, mock_components):
        """Test document addition with text that's too long."""
        long_text = "a" * 50001  # Over the 50,000 character limit

        response = client.post(
            "/add_document", json={"text": long_text, "metadata": {}}
        )

        assert response.status_code == 400
        assert "too long" in response.json()["detail"]

    def test_add_document_database_error(self, client, mock_components):
        """Test document addition with database error."""
        mock_components["db"].add_document.side_effect = Exception("Database error")

        response = client.post(
            "/add_document", json={"text": "Test document", "metadata": {}}
        )

        assert response.status_code == 500
        assert "Failed to add document" in response.json()["detail"]

    def test_search_success(self, client, mock_components):
        """Test successful document search."""
        mock_components["db"].search.return_value = {
            "documents": ["Document 1", "Document 2"],
            "distances": [0.1, 0.2],
            "metadatas": [{"source": "test1"}, {"source": "test2"}],
        }

        response = client.get("/search", params={"query": "test query", "limit": 2})

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert all("content" in item for item in data)
        assert all("score" in item for item in data)
        assert all("metadata" in item for item in data)

    def test_search_empty_query(self, client, mock_components):
        """Test search with empty query."""
        response = client.get("/search", params={"query": "", "limit": 5})

        assert response.status_code == 400
        assert "empty" in response.json()["detail"]

    def test_search_invalid_limit(self, client, mock_components):
        """Test search with invalid limit parameters."""
        # Test limit too low
        response = client.get("/search", params={"query": "test", "limit": 0})
        assert response.status_code == 422  # Validation error

        # Test limit too high
        response = client.get("/search", params={"query": "test", "limit": 25})
        assert response.status_code == 422  # Validation error

    def test_search_database_error(self, client, mock_components):
        """Test search with database error."""
        mock_components["db"].search.side_effect = Exception("Search error")

        response = client.get("/search", params={"query": "test query", "limit": 5})

        assert response.status_code == 500
        assert "Search failed" in response.json()["detail"]

    def test_chat_success(self, client, mock_components):
        """Test successful chat request."""
        response = client.post(
            "/chat", json={"question": "What is machine learning?", "max_results": 3}
        )

        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
        assert "sources" in data
        assert "model_used" in data
        assert "tokens_used" in data
        assert "processing_time" in data

    def test_chat_empty_question(self, client, mock_components):
        """Test chat with empty question."""
        response = client.post("/chat", json={"question": "", "max_results": 3})

        assert response.status_code == 422
        assert "empty" in response.json()["detail"][0]["msg"].lower()

    def test_chat_invalid_max_results(self, client, mock_components):
        """Test chat with invalid max_results."""
        # Test too low
        response = client.post(
            "/chat", json={"question": "test question", "max_results": 0}
        )
        assert response.status_code == 422

        # Test too high
        response = client.post(
            "/chat", json={"question": "test question", "max_results": 15}
        )
        assert response.status_code == 422

    def test_chat_rag_error(self, client, mock_components):
        """Test chat with RAG pipeline error."""
        mock_components["rag"].generate_answer.side_effect = Exception("RAG error")

        response = client.post(
            "/chat", json={"question": "test question", "max_results": 3}
        )

        assert response.status_code == 500
        assert "Failed to generate answer" in response.json()["detail"]

    def test_chat_rag_error_response(self, client, mock_components):
        """Test chat when RAG returns error in response."""
        mock_components["rag"].generate_answer.return_value = {
            "answer": "Error: Something went wrong",
            "sources": [],
            "model_used": "openai/gpt-3.5-turbo",
            "tokens_used": 0,
            "processing_time": 0.1,
            "context_documents_found": 0,
        }

        response = client.post(
            "/chat", json={"question": "test question", "max_results": 3}
        )

        assert response.status_code == 500
        assert "Error: Something went wrong" in response.json()["detail"]

    def test_health_endpoint_success(self, client, mock_components):
        """Test health check endpoint with all components healthy."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "components" in data
        assert "database" in data["components"]
        assert "embeddings" in data["components"]

    def test_health_endpoint_with_component_errors(self, client):
        """Test health check with component errors."""
        mock_db = Mock()
        mock_emb = Mock()
        mock_db.get_collection_stats.side_effect = Exception("DB error")
        mock_emb.generate_embeddings.side_effect = Exception("Embedding error")

        with patch.object(main_module, "db_manager", mock_db, create=True), patch.object(
            main_module, "embedding_generator", mock_emb, create=True
        ):
            response = client.get("/health")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "degraded"
            assert data["components"]["database"]["status"] == "error"
            assert data["components"]["embeddings"]["status"] == "error"

    def test_health_endpoint_complete_failure(self, client):
        """Test health check with complete system failure."""
        mock_db = Mock()
        mock_emb = Mock()
        mock_db.get_collection_stats.side_effect = Exception("Critical error")
        mock_emb.generate_embeddings.side_effect = Exception("Critical error")

        with patch.object(main_module, "db_manager", mock_db, create=True), patch.object(
            main_module, "embedding_generator", mock_emb, create=True
        ):
            response = client.get("/health")

            assert response.status_code == 200
            # Should still return status, even if degraded
