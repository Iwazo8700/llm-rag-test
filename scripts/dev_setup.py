#!/usr/bin/env python3
"""
Development setup script for the RAG system.

This script helps set up the development environment and populate
the database with sample data for testing.
"""

import logging
from pathlib import Path
import time

import requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:8000"

# Sample documents for testing
SAMPLE_DOCUMENTS = [
    {
        "text": "Python is a high-level, interpreted programming language with dynamic semantics. Its high-level built-in data structures, combined with dynamic typing and dynamic binding, make it very attractive for Rapid Application Development.",
        "metadata": {
            "topic": "programming",
            "language": "python",
            "difficulty": "beginner",
        },
    },
    {
        "text": "Machine learning is a method of data analysis that automates analytical model building. It is a branch of artificial intelligence based on the idea that systems can learn from data, identify patterns and make decisions with minimal human intervention.",
        "metadata": {
            "topic": "ai",
            "subtopic": "machine_learning",
            "difficulty": "intermediate",
        },
    },
    {
        "text": "FastAPI is a modern, fast (high-performance) web framework for building APIs with Python 3.7+ based on standard Python type hints. It's one of the fastest Python frameworks available.",
        "metadata": {
            "topic": "web_development",
            "framework": "fastapi",
            "language": "python",
        },
    },
    {
        "text": "Vector databases are specialized databases designed to store, index, and query high-dimensional vector data efficiently. They are essential for AI applications that work with embeddings.",
        "metadata": {
            "topic": "databases",
            "subtopic": "vector_databases",
            "difficulty": "advanced",
        },
    },
    {
        "text": "Natural Language Processing (NLP) enables computers to understand, interpret, and generate human language in a valuable way. It combines computational linguistics with statistical and machine learning models.",
        "metadata": {"topic": "ai", "subtopic": "nlp", "difficulty": "intermediate"},
    },
    {
        "text": "REST (Representational State Transfer) is an architectural style for designing networked applications. It relies on a stateless, client-server communication protocol -- typically HTTP.",
        "metadata": {
            "topic": "web_development",
            "concept": "rest_api",
            "difficulty": "beginner",
        },
    },
    {
        "text": "Docker is a platform that uses containerization technology to package applications and their dependencies into lightweight, portable containers that can run consistently across different environments.",
        "metadata": {"topic": "devops", "tool": "docker", "difficulty": "intermediate"},
    },
    {
        "text": "Retrieval-Augmented Generation (RAG) is a technique that combines information retrieval with generative AI to provide more accurate and contextually relevant responses by grounding language models in external knowledge.",
        "metadata": {"topic": "ai", "subtopic": "rag", "difficulty": "advanced"},
    },
]


def wait_for_server(max_attempts: int = 30) -> bool:
    """Wait for the server to be available."""
    for attempt in range(max_attempts):
        try:
            response = requests.get(f"{BASE_URL}/", timeout=5)
            if response.status_code == 200:
                logger.info("Server is available")
                return True
        except requests.RequestException:
            pass

        logger.info(f"Waiting for server... (attempt {attempt + 1}/{max_attempts})")
        time.sleep(1)

    return False


def check_server_health() -> dict:
    """Check server health and return status."""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error(f"Health check failed: {e}")
        return {"status": "error", "error": str(e)}


def add_sample_documents():
    """Add sample documents to the database."""
    logger.info("Adding sample documents...")

    added_count = 0
    for i, doc in enumerate(SAMPLE_DOCUMENTS):
        try:
            response = requests.post(f"{BASE_URL}/add_document", json=doc, timeout=30)
            response.raise_for_status()

            result = response.json()
            logger.info(f"Added document {i+1}: {result.get('id', 'unknown')}")
            added_count += 1

        except requests.RequestException as e:
            logger.error(f"Failed to add document {i+1}: {e}")

    logger.info(f"Successfully added {added_count}/{len(SAMPLE_DOCUMENTS)} documents")
    return added_count


def test_search_functionality():
    """Test the search functionality with sample queries."""
    logger.info("Testing search functionality...")

    test_queries = [
        "Python programming",
        "machine learning",
        "web development",
        "vector database",
        "artificial intelligence",
    ]

    for query in test_queries:
        try:
            response = requests.get(
                f"{BASE_URL}/search", params={"query": query, "limit": 3}, timeout=10
            )
            response.raise_for_status()

            results = response.json()
            logger.info(f"Search '{query}': found {len(results)} results")

            if results:
                best_result = results[0]
                logger.info(
                    f"  Best match (score: {best_result['score']:.3f}): {best_result['content'][:100]}..."
                )

        except requests.RequestException as e:
            logger.error(f"Search failed for '{query}': {e}")


def test_chat_functionality():
    """Test the chat/RAG functionality."""
    logger.info("Testing chat functionality...")

    test_questions = [
        "What is Python?",
        "How does machine learning work?",
        "What are the benefits of using FastAPI?",
        "Explain vector databases",
    ]

    for question in test_questions:
        try:
            response = requests.post(
                f"{BASE_URL}/chat",
                json={"question": question, "max_results": 3},
                timeout=30,
            )
            response.raise_for_status()

            result = response.json()
            logger.info(f"Chat '{question}':")
            logger.info(f"  Answer: {result['answer'][:150]}...")
            logger.info(f"  Sources: {len(result['sources'])}")
            logger.info(f"  Processing time: {result['processing_time']:.2f}s")

        except requests.RequestException as e:
            logger.error(f"Chat failed for '{question}': {e}")


def create_sample_env_file():
    """Create a sample .env file if it doesn't exist."""
    env_file = Path(".env")

    if not env_file.exists():
        logger.info("Creating sample .env file...")

        env_content = """# RAG System Configuration
# Copy this file and update the values as needed

# OpenRouter API Key (get from https://openrouter.ai/)
OPENROUTER_API_KEY=your_openrouter_api_key_here

# Database Configuration
CHROMADB_PATH=./chroma_db

# Model Configuration
EMBEDDING_MODEL=all-MiniLM-L6-v2
MODEL_SLUG=openai/gpt-3.5-turbo

# Application Configuration
APP_NAME=RAG System API
APP_VERSION=1.0.0
LOG_LEVEL=INFO

# Server Configuration
HOST=0.0.0.0
PORT=8000

# Limits
MAX_DOCUMENT_LENGTH=50000
MAX_SEARCH_RESULTS=20
MAX_CHAT_RESULTS=10
REQUEST_TIMEOUT=30
"""

        with env_file.open("w") as f:
            f.write(env_content)

        logger.info("Sample .env file created. Please update with your actual API key.")
    else:
        logger.info(".env file already exists")


def main():
    """Main development setup function."""
    logger.info("Starting RAG System development setup...")

    # Create sample .env file
    create_sample_env_file()

    # Wait for server to be available
    if not wait_for_server():
        logger.error("Server is not available. Please start the server first:")
        logger.error("uvicorn app.main:app --reload")
        return

    # Check server health
    health = check_server_health()
    logger.info(f"Server health: {health.get('status', 'unknown')}")

    if health.get("status") != "healthy":
        logger.warning("Server is not healthy, but continuing with setup...")

    # Add sample documents
    added_count = add_sample_documents()

    if added_count == 0:
        logger.warning(
            "No documents were added. Database functionality may be impaired."
        )
        return

    # Test functionality
    test_search_functionality()
    test_chat_functionality()

    logger.info("Development setup completed successfully!")
    logger.info("\nYou can now:")
    logger.info("- Visit http://localhost:8000/docs for API documentation")
    logger.info("- Use the /search endpoint to find documents")
    logger.info("- Use the /chat endpoint for RAG-based Q&A")
    logger.info("- Check /health for system status")


if __name__ == "__main__":
    main()
