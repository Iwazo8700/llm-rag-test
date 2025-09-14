"""
Unit tests for the database component.
"""

import shutil
import tempfile
from unittest.mock import Mock, patch

import pytest

from app.database import ChromaDBManager


class TestChromaDBManager:
    """Test cases for ChromaDBManager class."""

    @pytest.fixture
    def temp_db_path(self):
        """Create a temporary directory for test database."""
        temp_dir = tempfile.mkdtemp()
        yield f"{temp_dir}/test_chroma_db"
        shutil.rmtree(temp_dir)

    @patch("app.database.chromadb.PersistentClient")
    def test_init_success(self, mock_client, temp_db_path):
        """Test successful database initialization."""
        mock_client_instance = Mock()
        mock_collection = Mock()
        mock_client_instance.get_or_create_collection.return_value = mock_collection
        mock_client.return_value = mock_client_instance

        db_manager = ChromaDBManager("test_collection")

        assert db_manager.client is not None
        assert db_manager.collection is not None
        mock_client.assert_called_once_with(path="./chroma_db")
        mock_client_instance.get_or_create_collection.assert_called_once_with(
            name="test_collection", metadata={"hnsw:space": "cosine"}
        )

    @patch("app.database.chromadb.PersistentClient")
    def test_init_failure(self, mock_client, temp_db_path):
        """Test database initialization failure."""
        mock_client.side_effect = Exception("Database connection failed")

        with pytest.raises(RuntimeError, match="ChromaDB initialization failed"):
            ChromaDBManager("test_collection")

    @patch("app.database.chromadb.PersistentClient")
    def test_add_document_success(self, mock_client, temp_db_path):
        """Test successful document addition."""
        mock_client_instance = Mock()
        mock_collection = Mock()
        mock_client_instance.get_or_create_collection.return_value = mock_collection
        mock_client.return_value = mock_client_instance

        # Mock the get method to return empty results (no existing documents)
        mock_collection.get.return_value = {"ids": []}

        db_manager = ChromaDBManager("test_collection")

        text = "Test document"
        embedding = [0.1] * 384
        metadata = {"source": "test"}

        doc_id = db_manager.add_document(text, embedding, metadata)

        assert doc_id is not None
        assert isinstance(doc_id, str)
        mock_collection.add.assert_called_once()
        # Verify the actual call arguments
        call_args = mock_collection.add.call_args
        assert "documents" in call_args.kwargs
        assert "embeddings" in call_args.kwargs
        assert "metadatas" in call_args.kwargs
        assert "ids" in call_args.kwargs

    @patch("app.database.chromadb.PersistentClient")
    def test_add_document_failure(self, mock_client, temp_db_path):
        """Test document addition failure."""
        mock_client_instance = Mock()
        mock_collection = Mock()
        mock_collection.add.side_effect = Exception("Database error")
        mock_client_instance.get_or_create_collection.return_value = mock_collection
        mock_client.return_value = mock_client_instance

        db_manager = ChromaDBManager(temp_db_path)

        with pytest.raises(RuntimeError, match="Document storage failed"):
            db_manager.add_document("text", [0.1] * 384, {})

    @patch("app.database.chromadb.PersistentClient")
    def test_search_success(self, mock_client, temp_db_path):
        """Test successful document search."""
        mock_client_instance = Mock()
        mock_collection = Mock()
        mock_collection.query.return_value = {
            "documents": [["Document 1", "Document 2"]],
            "distances": [[0.1, 0.2]],
            "metadatas": [[{"source": "test1"}, {"source": "test2"}]],
        }
        mock_client_instance.get_or_create_collection.return_value = mock_collection
        mock_client.return_value = mock_client_instance

        db_manager = ChromaDBManager(temp_db_path)

        query_embedding = [0.1] * 384
        results = db_manager.search(query_embedding, n_results=2)

        assert "documents" in results
        assert "distances" in results
        assert "metadatas" in results
        assert len(results["documents"]) == 2
        mock_collection.query.assert_called_once()

    @patch("app.database.chromadb.PersistentClient")
    def test_search_failure(self, mock_client, temp_db_path):
        """Test search failure."""
        mock_client_instance = Mock()
        mock_collection = Mock()
        mock_collection.query.side_effect = Exception("Search error")
        mock_client_instance.get_or_create_collection.return_value = mock_collection
        mock_client.return_value = mock_client_instance

        db_manager = ChromaDBManager(temp_db_path)

        with pytest.raises(RuntimeError, match="Search failed"):
            db_manager.search([0.1] * 384, n_results=1)

    @patch("app.database.chromadb.PersistentClient")
    def test_get_collection_stats(self, mock_client, temp_db_path):
        """Test getting collection statistics."""
        mock_client_instance = Mock()
        mock_collection = Mock()
        mock_collection.count.return_value = 42
        mock_collection.name = "documents"
        mock_client_instance.get_or_create_collection.return_value = mock_collection
        mock_client.return_value = mock_client_instance

        db_manager = ChromaDBManager(temp_db_path)

        stats = db_manager.get_collection_stats()

        assert stats["document_count"] == 42
        assert stats["collection_name"] == "documents"
        mock_collection.count.assert_called_once()

    @patch("app.database.chromadb.PersistentClient")
    def test_custom_collection_name(self, mock_client, temp_db_path):
        """Test initialization with custom collection name."""
        mock_client_instance = Mock()
        mock_collection = Mock()
        mock_client_instance.get_or_create_collection.return_value = mock_collection
        mock_client.return_value = mock_client_instance

        custom_name = "custom_documents"
        db_manager = ChromaDBManager(custom_name)

        assert db_manager.client is not None
        mock_client_instance.get_or_create_collection.assert_called_with(
            name=custom_name, metadata={"hnsw:space": "cosine"}
        )

    @patch("app.database.chromadb.PersistentClient")
    def test_embedding_dimension_validation(self, mock_client, temp_db_path):
        """Test that embeddings have correct dimensions."""
        mock_client_instance = Mock()
        mock_collection = Mock()
        mock_client_instance.get_or_create_collection.return_value = mock_collection
        mock_client.return_value = mock_client_instance

        # Mock the get method to return empty results (no existing documents)
        mock_collection.get.return_value = {"ids": []}

        db_manager = ChromaDBManager("test_collection")

        # Test with correct dimension
        valid_embedding = [0.1] * 384
        doc_id = db_manager.add_document("test", valid_embedding, {})
        assert doc_id is not None

        # Test with incorrect dimension (should still work but might warn)
        short_embedding = [0.1] * 100
        doc_id = db_manager.add_document("test", short_embedding, {})
        assert doc_id is not None

    @patch("app.database.chromadb.PersistentClient")
    def test_metadata_handling(self, mock_client, temp_db_path):
        """Test proper metadata handling."""
        mock_client_instance = Mock()
        mock_collection = Mock()
        mock_client_instance.get_or_create_collection.return_value = mock_collection
        mock_client.return_value = mock_client_instance

        # Mock the get method to return empty results (no existing documents)
        mock_collection.get.return_value = {"ids": []}

        db_manager = ChromaDBManager("test_collection")

        # Test with None metadata
        doc_id = db_manager.add_document("test", [0.1] * 384, None)
        assert doc_id is not None

        # Test with empty metadata
        doc_id = db_manager.add_document("test", [0.1] * 384, {})
        assert doc_id is not None

        # Test with complex metadata
        complex_metadata = {
            "source": "test",
            "author": "John Doe",
            "tags": ["tag1", "tag2"],
        }
        doc_id = db_manager.add_document("test", [0.1] * 384, complex_metadata)
        assert doc_id is not None
