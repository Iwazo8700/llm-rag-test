__version__ = "1.0.0"
__author__ = "Your Name"
__description__ = "Vector Database API with RAG capabilities"

from .database import ChromaDBManager
from .embeddings import EmbeddingGenerator
from .rag import RAGPipeline

__all__ = ["ChromaDBManager", "EmbeddingGenerator", "RAGPipeline"]
