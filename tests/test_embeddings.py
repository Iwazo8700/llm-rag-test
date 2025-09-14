"""
Unit tests for the embedding generator component.
"""

import shutil
import tempfile
from unittest.mock import Mock, patch

import pytest

from app.embeddings import EmbeddingGenerator


class TestEmbeddingGenerator:
    """Test cases for EmbeddingGenerator class."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    @patch("sentence_transformers.SentenceTransformer")
    def test_init_with_successful_model_load(self, mock_st):
        """Test initialization with successful model loading."""
        mock_model = Mock()
        # Mock the encode method that's called during initialization to test the model
        mock_model.encode.return_value = [[0.1] * 384]  # Return test embedding
        mock_st.return_value = mock_model

        generator = EmbeddingGenerator("all-MiniLM-L6-v2")
        assert generator.use_fallback is False
        assert generator.model_name == "all-MiniLM-L6-v2"
        assert generator.embedding_dim == 384
        assert generator.model is not None
        # Verify the test encoding was called during initialization
        mock_model.encode.assert_called()

    @patch("sentence_transformers.SentenceTransformer")
    def test_init_with_failed_model_load(self, mock_st):
        """Test initialization with failed model loading (fallback mode)."""
        mock_st.side_effect = Exception("Model download failed")

        generator = EmbeddingGenerator("test-model")
        assert generator.use_fallback is True
        assert generator.model_name == "test-model"
        assert generator.embedding_dim == 384
        assert generator.model is None

    @patch("sentence_transformers.SentenceTransformer")
    def test_fallback_embeddings_generation(self, mock_st):
        """Test fallback embedding generation."""
        mock_st.side_effect = Exception("Model load failed")
        generator = EmbeddingGenerator("test-model")

        texts = ["hello world", "test document"]
        embeddings = generator.generate_embeddings(texts)

        assert len(embeddings) == 2
        assert len(embeddings[0]) == 384
        assert len(embeddings[1]) == 384
        assert all(isinstance(val, float) for val in embeddings[0])

    @patch("sentence_transformers.SentenceTransformer")
    def test_model_embeddings_generation(self, mock_st):
        """Test model-based embedding generation."""
        mock_model = Mock()
        # Mock the initialization call
        mock_model.encode.side_effect = [
            [[0.1] * 384],  # First call during initialization
            [[0.1] * 384, [0.2] * 384],  # Second call during actual generation
        ]
        mock_st.return_value = mock_model

        generator = EmbeddingGenerator("all-MiniLM-L6-v2")
        texts = ["hello world", "test document"]
        embeddings = generator.generate_embeddings(texts)

        assert len(embeddings) == 2
        assert len(embeddings[0]) == 384
        # The model.encode should be called twice (initialization + generation)
        assert mock_model.encode.call_count == 2

    @patch("sentence_transformers.SentenceTransformer")
    def test_empty_text_handling(self, mock_st):
        """Test handling of empty texts."""
        mock_st.side_effect = Exception("Model load failed")
        generator = EmbeddingGenerator("test-model")

        texts = ["", "  ", "valid text"]
        embeddings = generator.generate_embeddings(texts)

        assert len(embeddings) == 3
        assert all(len(emb) == 384 for emb in embeddings)

    @patch("sentence_transformers.SentenceTransformer")
    def test_large_text_handling(self, mock_st):
        """Test handling of very large texts."""
        mock_st.side_effect = Exception("Model load failed")
        generator = EmbeddingGenerator("test-model")

        large_text = "word " * 1000  # 1000 words
        embeddings = generator.generate_embeddings([large_text])

        assert len(embeddings) == 1
        assert len(embeddings[0]) == 384

    @patch("sentence_transformers.SentenceTransformer")
    def test_deterministic_fallback_embeddings(self, mock_st):
        """Test that fallback embeddings are deterministic."""
        mock_st.side_effect = Exception("Model load failed")
        generator = EmbeddingGenerator("test-model")

        text = "test deterministic"
        embedding1 = generator.generate_embeddings([text])[0]
        embedding2 = generator.generate_embeddings([text])[0]

        assert embedding1 == embedding2

    @patch("sentence_transformers.SentenceTransformer")
    def test_different_texts_different_embeddings(self, mock_st):
        """Test that different texts produce different embeddings."""
        mock_st.side_effect = Exception("Model load failed")
        generator = EmbeddingGenerator("test-model")

        embedding1 = generator.generate_embeddings(["text one"])[0]
        embedding2 = generator.generate_embeddings(["text two"])[0]

        assert embedding1 != embedding2

    @patch("sentence_transformers.SentenceTransformer")
    def test_ssl_configuration(self, mock_st):
        """Test SSL configuration during initialization."""
        mock_model = Mock()
        mock_model.encode.return_value = [[0.1] * 384]  # Mock the test encoding
        mock_st.return_value = mock_model

        # Should not raise any SSL-related exceptions
        generator = EmbeddingGenerator("all-MiniLM-L6-v2")
        assert generator is not None

    @patch("sentence_transformers.SentenceTransformer")
    def test_numpy_array_conversion(self, mock_st):
        """Test conversion of numpy arrays to lists."""
        import numpy as np

        mock_model = Mock()
        # Return numpy array for initialization and actual generation
        mock_model.encode.side_effect = [
            np.array([[0.1] * 384]),  # Initialization call
            np.array([[0.1] * 384, [0.2] * 384]),  # Generation call
        ]
        mock_st.return_value = mock_model

        generator = EmbeddingGenerator("all-MiniLM-L6-v2")
        embeddings = generator.generate_embeddings(["test1", "test2"])

        assert isinstance(embeddings, list)
        assert isinstance(embeddings[0], list)
        assert all(isinstance(val, float) for val in embeddings[0])
