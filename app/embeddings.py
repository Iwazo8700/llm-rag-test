import hashlib
import logging
import math
import ssl
from typing import Optional

import certifi
import numpy as np
from sentence_transformers import SentenceTransformer

from .telemetry_simple import (
    metrics_collector,
    set_span_attribute,
    traced_operation,
)

logger = logging.getLogger(__name__)


class EmbeddingGenerator:
    """
    Generates text embeddings using SentenceTransformer models.

    This class handles the loading of embedding models and provides
    methods to generate embeddings for text inputs. It includes
    fallback mechanisms for cases where model download fails.
    """

    @traced_operation("embedding_init", component="embeddings")
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize the embedding generator with specified model.

        Args:
            model_name (str): Name of the SentenceTransformer model to use

        Raises:
            RuntimeError: If model loading fails completely
        """
        set_span_attribute("model_name", model_name)

        self.model_name = model_name
        self.embedding_dim = 384
        self.model: Optional[object] = None
        self.use_fallback = True

        self._configure_ssl()

        self._load_model()

        set_span_attribute("embedding_dim", self.embedding_dim)
        set_span_attribute("use_fallback", self.use_fallback)
        set_span_attribute("model_loaded", self.model is not None)

        counter = metrics_collector.get_counter(
            "embedding_generators_created", "Embedding generator instances created"
        )
        counter.add(
            1, {"model_name": model_name, "fallback_mode": str(self.use_fallback)}
        )

    def _configure_ssl(self) -> None:
        """Configure SSL context to handle certificate issues."""
        try:
            ssl_context = ssl.create_default_context(cafile=certifi.where())
            ssl._create_default_https_context = lambda: ssl_context
            logger.debug("SSL context configured with certifi certificates")
        except ImportError:
            logger.warning(
                "certifi not available, trying alternative SSL configuration"
            )
            try:
                ssl._create_default_https_context = ssl._create_unverified_context
                logger.warning(
                    "SSL verification disabled - not recommended for production"
                )
            except Exception as e:
                logger.error(f"Failed to configure SSL: {e}")

    @traced_operation("embedding_load_model", component="embeddings")
    def _load_model(self) -> None:
        """Load the SentenceTransformer model with proper error handling."""
        set_span_attribute("model_name", self.model_name)

        try:
            logger.info(f"Attempting to load embedding model: {self.model_name}")
            set_span_attribute("loading_stage", "downloading_model")

            self.model = SentenceTransformer(self.model_name)
            self.use_fallback = False
            set_span_attribute("model_download_success", True)

            set_span_attribute("loading_stage", "testing_model")
            test_embedding = self.model.encode(["test"], convert_to_numpy=True)
            self.embedding_dim = len(test_embedding[0])

            set_span_attribute("embedding_dim", self.embedding_dim)
            set_span_attribute("use_fallback", self.use_fallback)
            set_span_attribute("model_test_success", True)

            logger.info(
                f"Successfully loaded model: {self.model_name} (dim: {self.embedding_dim})"
            )

            counter = metrics_collector.get_counter(
                "embedding_model_loads", "Embedding model load attempts"
            )
            counter.add(1, {"status": "success", "model_name": self.model_name})

        except ImportError as e:
            logger.error(f"sentence-transformers not installed: {e}")
            set_span_attribute("error_type", "import_error")
            set_span_attribute("error_message", str(e))

            counter = metrics_collector.get_counter(
                "embedding_model_loads", "Embedding model load attempts"
            )
            counter.add(1, {"status": "import_error", "model_name": self.model_name})
            self._fallback_to_simple_embeddings()

        except Exception as e:
            logger.warning(f"Failed to load model '{self.model_name}': {e}")
            set_span_attribute("error_type", "general_error")
            set_span_attribute("error_message", str(e))

            counter = metrics_collector.get_counter(
                "embedding_model_loads", "Embedding model load attempts"
            )
            counter.add(1, {"status": "error", "model_name": self.model_name})
            self._fallback_to_simple_embeddings()

    def _fallback_to_simple_embeddings(self) -> None:
        """Set up fallback embedding generation."""
        self.model = None
        self.use_fallback = True
        self.embedding_dim = 384
        logger.info("Using deterministic fallback embedding generator")

    @traced_operation("embedding_generate", component="embeddings")
    def generate_embeddings(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings for a list of text inputs.

        Args:
            texts (list[str]): list of text strings to embed

        Returns:
            list[list[float]]: list of embedding vectors

        Raises:
            ValueError: If input texts are invalid
            RuntimeError: If embedding generation fails
        """
        if not texts:
            set_span_attribute("text_count", 0)
            set_span_attribute("early_return", "empty_input")
            return []

        if not all(isinstance(text, str) for text in texts):
            set_span_attribute("validation_error", "non_string_input")
            raise ValueError("All inputs must be strings")

        processed_texts = [text.strip() for text in texts if text.strip()]
        if not processed_texts:
            set_span_attribute("text_count", len(texts))
            set_span_attribute("processed_count", 0)
            set_span_attribute("early_return", "all_empty_strings")
            return [[0.0] * self.embedding_dim for _ in texts]

        set_span_attribute("text_count", len(texts))
        set_span_attribute("processed_count", len(processed_texts))
        set_span_attribute("use_fallback", self.use_fallback)
        set_span_attribute("model_name", self.model_name)
        set_span_attribute("embedding_dim", self.embedding_dim)

        try:
            if self.use_fallback:
                set_span_attribute("generation_method", "fallback")
                embeddings = self._generate_fallback_embeddings(texts)
            else:
                set_span_attribute("generation_method", "model")
                embeddings = self._generate_model_embeddings(processed_texts)

            set_span_attribute("embeddings_generated", len(embeddings))
            set_span_attribute("generation_success", True)

            counter = metrics_collector.get_counter(
                "embeddings_generated", "Text embeddings generated"
            )
            counter.add(
                len(texts),
                {
                    "status": "success",
                    "fallback_mode": str(self.use_fallback),
                    "model_name": self.model_name,
                },
            )

            histogram = metrics_collector.get_histogram(
                "embedding_batch_size", "Size of embedding batches"
            )
            histogram.record(len(texts), {"fallback_mode": str(self.use_fallback)})

            return embeddings

        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            set_span_attribute("generation_success", False)
            set_span_attribute("error_type", type(e).__name__)
            set_span_attribute("error_message", str(e))

            counter = metrics_collector.get_counter(
                "embeddings_generated", "Text embeddings generated"
            )
            counter.add(
                len(texts),
                {
                    "status": "error",
                    "fallback_mode": str(self.use_fallback),
                    "model_name": self.model_name,
                },
            )

            raise RuntimeError(f"Failed to generate embeddings: {e}") from e

    @traced_operation("embedding_model_encode", component="embeddings")
    def _generate_model_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings using the loaded model."""
        if self.model is None:
            set_span_attribute("error_type", "model_not_loaded")
            raise RuntimeError("Model not loaded")

        set_span_attribute("text_count", len(texts))
        set_span_attribute("model_name", self.model_name)
        set_span_attribute("generation_method", "sentence_transformer")

        embeddings = self.model.encode(  # type: ignore
            texts,
            show_progress_bar=False,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )

        set_span_attribute("embedding_type", type(embeddings).__name__)
        if hasattr(embeddings, "shape"):
            set_span_attribute("embedding_shape", str(embeddings.shape))

        if isinstance(embeddings, np.ndarray):
            result = embeddings.tolist()
        else:
            result = [[float(x) for x in emb] for emb in embeddings]

        set_span_attribute("result_count", len(result))
        set_span_attribute("embedding_dimension", len(result[0]) if result else 0)

        return result

    @traced_operation("embedding_fallback_generate", component="embeddings")
    def _generate_fallback_embeddings(self, texts: list[str]) -> list[list[float]]:
        """
        Generate deterministic fallback embeddings based on text content.
        This is used when the main model cannot be loaded.
        """

        set_span_attribute("text_count", len(texts))
        set_span_attribute("embedding_dim", self.embedding_dim)
        set_span_attribute("generation_method", "deterministic_fallback")

        embeddings = []
        empty_text_count = 0

        for text in texts:
            if not text.strip():
                embeddings.append([0.0] * self.embedding_dim)
                empty_text_count += 1
                continue

            text_lower = text.lower().strip()

            text_hash = hashlib.sha256(text_lower.encode()).hexdigest()

            embedding: list[float] = []

            for i in range(0, min(len(text_hash), self.embedding_dim * 2), 2):
                if len(embedding) >= self.embedding_dim:
                    break

                hex_pair = text_hash[i : i + 2]
                base_value = int(hex_pair, 16) / 255.0  # Normalize to [0,1]

                char_index = len(embedding) % len(text_lower)
                char_value = ord(text_lower[char_index]) / 255.0

                length_factor = math.log(len(text_lower) + 1) / 10.0

                final_value = base_value * 0.6 + char_value * 0.3 + length_factor * 0.1

                # Apply sine transformation for more variation
                final_value = (math.sin(final_value * math.pi * 2) + 1) / 2

                embedding.append(final_value)

            while len(embedding) < self.embedding_dim:
                pos = len(embedding)
                pos_value = math.sin((pos * len(text_lower)) / 100.0)
                embedding.append((pos_value + 1) / 2)

            magnitude = math.sqrt(sum(x * x for x in embedding))
            if magnitude > 0:
                embedding = [x / magnitude for x in embedding]

            embeddings.append(embedding[: self.embedding_dim])

        set_span_attribute("empty_text_count", empty_text_count)
        set_span_attribute("processed_text_count", len(texts) - empty_text_count)
        set_span_attribute("embeddings_generated", len(embeddings))

        return embeddings

    def get_embedding_dimension(self) -> int:
        """
        Get the dimension of embeddings produced by this generator.

        Returns:
            int: Embedding dimension
        """
        return self.embedding_dim
