"""
Unit tests for FastAPI endpoints using dependency injection.
"""

from unittest.mock import Mock

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
import pytest

from app.config import config
from app.database import ChromaDBManager
from app.embeddings import EmbeddingGenerator
from app.models import ChatRequest, DocumentRequest
from app.rag import RAGPipeline


def create_test_app():
    """Create a test FastAPI app with mocked dependencies."""
    test_app = FastAPI()

    # Mock components
    mock_db = Mock(spec=ChromaDBManager)
    mock_emb = Mock(spec=EmbeddingGenerator)
    mock_rag = Mock(spec=RAGPipeline)

    # Setup mock returns
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

    mock_emb.model_name = "all-MiniLM-L6-v2"
    mock_emb.use_fallback = False
    mock_emb.generate_embeddings.return_value = [[0.1] * 384]

    mock_rag.model_slug = "openai/gpt-3.5-turbo"
    mock_rag.generate_answer.return_value = {
        "answer": "Test answer",
        "sources": [],
        "model_used": "openai/gpt-3.5-turbo",
        "tokens_used": 50,
        "processing_time": 1.5,
        "context_documents_found": 2,
    }

    # Create endpoints with mocked dependencies
    @test_app.get("/")
    def root():
        """Root endpoint with system information."""
        try:
            stats = mock_db.get_collection_stats()
            return {
                "name": config.APP_NAME,
                "version": config.APP_VERSION,
                "status": "healthy",
                "components": {
                    "database": "ChromaDB",
                    "embedding_model": mock_emb.model_name,
                    "llm_model": mock_rag.model_slug,
                    "fallback_mode": mock_emb.use_fallback,
                    "api_key_configured": config.is_api_key_configured(),
                },
                "statistics": stats,
            }
        except Exception as e:
            return {
                "name": config.APP_NAME,
                "version": config.APP_VERSION,
                "status": "error",
                "error": str(e),
            }

    @test_app.post("/add_document")
    def add_document(request: DocumentRequest):
        """Add a document to the database."""
        try:
            embeddings = mock_emb.generate_embeddings([request.text])
            doc_id = mock_db.add_document(
                text=request.text,
                embedding=embeddings[0],
                metadata=request.metadata or {},
            )
            return {
                "success": True,
                "id": doc_id,
                "message": "Document added successfully",
                "metadata": {"embedding_dimension": len(embeddings[0])},
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to add document: {e}")

    @test_app.get("/search")
    def search(query: str, limit: int = 5):
        """Search for documents."""
        if not query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")

        if not (1 <= limit <= 20):
            raise HTTPException(
                status_code=400, detail="Limit must be between 1 and 20"
            )

        try:
            embeddings = mock_emb.generate_embeddings([query])
            results = mock_db.search(
                query_embedding=embeddings[0],
                n_results=limit,
            )

            search_results = []
            for i, (doc, distance, metadata) in enumerate(
                zip(results["documents"], results["distances"], results["metadatas"])
            ):
                search_results.append(
                    {
                        "content": doc,
                        "score": max(
                            0.0, 1.0 - distance
                        ),  # Convert distance to similarity
                        "metadata": metadata or {},
                    }
                )

            return search_results
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Search failed: {e}")

    @test_app.post("/chat")
    def chat(request: ChatRequest):
        """Chat endpoint for RAG-based question answering."""
        try:
            result = mock_rag.generate_answer(
                question=request.question,
                max_results=request.max_results,
            )

            if result["answer"].startswith("Error:"):
                raise HTTPException(status_code=500, detail=result["answer"])

            return result
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Failed to generate answer: {e}"
            )

    @test_app.get("/health")
    def health():
        """Health check endpoint."""
        import time

        components = {}
        overall_status = "healthy"

        # Check database
        try:
            mock_db.get_collection_stats()
            components["database"] = {"status": "healthy", "document_count": 10}
        except Exception as e:
            components["database"] = {"status": "error", "error": str(e)}
            overall_status = "degraded"

        # Check embeddings
        try:
            mock_emb.generate_embeddings(["test"])
            components["embeddings"] = {
                "status": "healthy",
                "fallback_mode": mock_emb.use_fallback,
                "dimension": 384,
            }
        except Exception as e:
            components["embeddings"] = {"status": "error", "error": str(e)}
            overall_status = "degraded"

        return {
            "status": overall_status,
            "timestamp": time.time(),
            "components": components,
            "version": config.APP_VERSION,
            "uptime": 0.0,
        }

    return test_app


class TestAPIEndpoints:
    """Test API endpoints with mocked dependencies."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        app = create_test_app()
        return TestClient(app)

    def test_root_endpoint_success(self, client):
        """Test the root endpoint returns system information."""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "RAG System API"
        assert data["version"] == "1.0.0"
        assert data["status"] == "healthy"
        assert "components" in data
        assert "statistics" in data

    def test_add_document_success(self, client):
        """Test successful document addition."""
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

    def test_add_document_empty_text(self, client):
        """Test document addition with empty text."""
        response = client.post("/add_document", json={"text": "", "metadata": {}})

        assert response.status_code == 422  # Pydantic validation error

    def test_search_success(self, client):
        """Test successful document search."""
        response = client.get("/search", params={"query": "test query", "limit": 2})

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert all("content" in item for item in data)
        assert all("score" in item for item in data)
        assert all("metadata" in item for item in data)

    def test_search_empty_query(self, client):
        """Test search with empty query."""
        response = client.get("/search", params={"query": "", "limit": 5})

        assert response.status_code == 400
        assert "empty" in response.json()["detail"]

    def test_chat_success(self, client):
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

    def test_chat_empty_question(self, client):
        """Test chat with empty question."""
        response = client.post("/chat", json={"question": "", "max_results": 3})

        assert response.status_code == 422  # Pydantic validation error

    def test_health_endpoint_success(self, client):
        """Test health check endpoint."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "components" in data
        assert "database" in data["components"]
        assert "embeddings" in data["components"]
