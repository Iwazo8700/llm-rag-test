# RAG System Usage Documentation

## Table of Contents
1. [Installation & Setup](#installation--setup)
2. [Quick Start](#quick-start)
3. [API Endpoints](#api-endpoints)
4. [Usage Examples](#usage-examples)
5. [Client Libraries](#client-libraries)
6. [Common Use Cases](#common-use-cases)
7. [Development & Deployment](#development--deployment)
8. [Troubleshooting](#troubleshooting)
9. [Performance Tips](#performance-tips)

---

## Installation & Setup

### Prerequisites
- **Python**: 3.8 or higher
- **Memory**: 1GB+ RAM available
- **Storage**: 2GB+ free disk space
- **Network**: Internet connection for model downloads

### Local Installation

#### 1. Clone and Setup Environment
```bash
# Clone repository
git clone <your-repo-url>
cd llm-rag-test

# Create virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
make install
```

#### 2. Configuration
```bash
# Create environment file
cp .env.example .env

# Edit .env with your configuration
# Required:
OPENROUTER_API_KEY=your_openrouter_api_key_here

# Optional (with defaults):
CHROMADB_PATH=./chroma_db
EMBEDDING_MODEL=all-MiniLM-L6-v2
MODEL_SLUG=openai/gpt-3.5-turbo
LOG_LEVEL=INFO
```

> **Security Note**: Get your OpenRouter API key from [openrouter.ai](https://openrouter.ai/). Never commit API keys to version control.

#### 3. Verify Installation
```bash
# Test installation
python -c "
from app.config import config
from app.database import ChromaDBManager
from app.embeddings import EmbeddingGenerator
print('All components imported successfully')
print('API key configured:', config.is_api_key_configured())
"
```

### Docker Installation

#### Quick Docker Setup
```bash
# Build and run
make docker-build
make docker-run

# Or use Docker Compose
cp .env.example .env  # Edit with your API key
docker-compose up -d
```

#### Docker with Persistent Storage
```bash
# Run with volume mounting for data persistence
docker run -d \
  --name rag-system \
  -p 8000:8000 \
  --env-file .env \
  -v $(pwd)/chroma_db:/app/chroma_db \
  rag-system
```

## Quick Start

### 1. Start the Server
```bash
# Navigate to project directory
cd llm-rag-test

# Install dependencies
make install

# Start the server
make run
```

### 2. Verify System Health
```bash
curl http://localhost:8000/
```

### 3. Add Your First Document
```bash
curl -X POST "http://localhost:8000/add_document" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Python is a high-level programming language known for its simplicity and readability.",
    "metadata": {"source": "documentation", "topic": "programming"}
  }'
```

### 4. Search Documents
```bash
curl "http://localhost:8000/search?query=Python%20programming&limit=3"
```

### 5. Ask Questions
```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is Python?",
    "max_results": 2
  }'
```

---

## Installation & Setup

### Prerequisites
- Python 3.8 or higher
- 512MB+ RAM available
- Internet connection (for model downloads)

### Step-by-Step Installation

#### 1. Clone and Setup
```bash
# Clone the repository
git clone <your-repo-url>
cd llm-rag-test

# Create virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
make install
```

#### 2. Configuration
```bash
# Create configuration file
cp .env.example .env

# Edit .env with your settings
nano .env  # or your preferred editor
```

**Required Configuration:**
```bash
# OpenRouter API Key (get from https://openrouter.ai/)
OPENROUTER_API_KEY=sk-or-your-api-key-here

# Database storage path
CHROMADB_PATH=./chroma_db

# Embedding model (default recommended)
EMBEDDING_MODEL=all-MiniLM-L6-v2

# LLM model for chat responses
MODEL_SLUG=openai/gpt-3.5-turbo
```

#### 3. Start the System
```bash
# Development mode (auto-reload)
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production mode
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

#### 4. Verify Installation
```bash
# Check system health
curl http://localhost:8000/health

# Run comprehensive test
python test_system.py
```

---

## API Endpoints

### Base URL
```
http://localhost:8000
```

### 1. System Health (`GET /`)

**Purpose**: Check system status and component health

**Request**:
```bash
curl http://localhost:8000/
```

**Response**:
```json
{
  "name": "RAG System",
  "version": "1.0.0",
  "status": "healthy",
  "components": {
    "database": "ChromaDB",
    "embedding_model": "all-MiniLM-L6-v2",
    "llm_model": "openai/gpt-3.5-turbo",
    "fallback_mode": false
  },
  "statistics": {
    "document_count": 42,
    "collection_name": "documents"
  }
}
```

### 2. Add Document (`POST /add_document`)

**Purpose**: Store a document in the vector database

**Request**:
```bash
curl -X POST "http://localhost:8000/add_document" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Your document content here...",
    "metadata": {
      "source": "web",
      "author": "John Doe",
      "topic": "technology",
      "date": "2024-01-15"
    }
  }'
```

**Parameters**:
- `text` (required): Document content (max 50,000 characters)
- `metadata` (optional): Additional information about the document

**Response**:
```json
{
  "success": true,
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Document added successfully",
  "metadata": {
    "text_length": 156,
    "embedding_dimension": 384
  }
}
```

### 3. Search Documents (`GET /search`)

**Purpose**: Find similar documents using semantic search

**Request**:
```bash
curl "http://localhost:8000/search?query=machine%20learning&limit=5"
```

**Parameters**:
- `query` (required): Search query text
- `limit` (optional): Maximum results (1-20, default: 5)

**Response**:
```json
[
  {
    "content": "Machine learning is a subset of artificial intelligence...",
    "score": 0.8756,
    "metadata": {
      "source": "wikipedia",
      "topic": "AI",
      "date": "2024-01-10"
    }
  },
  {
    "content": "Deep learning algorithms use neural networks...",
    "score": 0.7432,
    "metadata": {
      "source": "textbook",
      "topic": "AI"
    }
  }
]
```

### 4. RAG Chat (`POST /chat`)

**Purpose**: Generate contextual answers using retrieved documents

**Request**:
```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is the difference between machine learning and deep learning?",
    "max_results": 3
  }'
```

**Parameters**:
- `question` (required): Your question
- `max_results` (optional): Max context documents (1-10, default: 3)

**Response**:
```json
{
  "answer": "Based on the retrieved documents, machine learning is a broader field of AI that enables computers to learn from data without explicit programming. Deep learning is a subset of machine learning that uses neural networks with multiple layers...",
  "sources": [
    {
      "source_index": 0,
      "similarity_score": 0.876,
      "metadata": {"source": "wikipedia", "topic": "AI"}
    }
  ],
  "model_used": "openai/gpt-3.5-turbo",
  "tokens_used": 245,
  "processing_time": 1.23,
  "context_documents_found": 2
}
```

### 5. Detailed Health Check (`GET /health`)

**Purpose**: Get detailed system health information

**Request**:
```bash
curl http://localhost:8000/health
```

**Response**:
```json
{
  "status": "healthy",
  "timestamp": 1641024000.0,
  "components": {
    "database": {
      "status": "healthy",
      "document_count": 42
    },
    "embeddings": {
      "status": "healthy",
      "fallback_mode": false,
      "dimension": 384
    }
  }
}
```

---

## Usage Examples

### Building a Knowledge Base

#### 1. Add Multiple Documents
```bash
# Add a programming document
curl -X POST "http://localhost:8000/add_document" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Python is an interpreted, high-level programming language with dynamic semantics. Its high-level built-in data structures make it attractive for Rapid Application Development.",
    "metadata": {"source": "python.org", "topic": "programming", "language": "python"}
  }'

# Add an AI document
curl -X POST "http://localhost:8000/add_document" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Artificial Intelligence (AI) refers to the simulation of human intelligence in machines programmed to think and learn like humans.",
    "metadata": {"source": "encyclopedia", "topic": "AI", "difficulty": "beginner"}
  }'

# Add a data science document
curl -X POST "http://localhost:8000/add_document" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Data science is an interdisciplinary field that uses scientific methods, processes, algorithms and systems to extract knowledge and insights from structured and unstructured data.",
    "metadata": {"source": "textbook", "topic": "data-science", "chapter": 1}
  }'
```

#### 2. Search and Explore
```bash
# Find programming-related content
curl "http://localhost:8000/search?query=programming%20language&limit=3"

# Search for AI content
curl "http://localhost:8000/search?query=artificial%20intelligence&limit=2"

# Look for data-related content
curl "http://localhost:8000/search?query=data%20analysis&limit=3"
```

#### 3. Interactive Q&A
```bash
# Ask about Python
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What makes Python good for rapid development?",
    "max_results": 2
  }'

# Ask about AI
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "How does AI simulate human intelligence?",
    "max_results": 2
  }'

# Ask comparative questions
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is the relationship between AI, data science, and programming?",
    "max_results": 3
  }'
```

### Batch Operations

#### Adding Multiple Documents (Python Script)
```python
import requests
import json

# List of documents to add
documents = [
    {
        "text": "React is a JavaScript library for building user interfaces...",
        "metadata": {"source": "react.dev", "topic": "frontend", "framework": "react"}
    },
    {
        "text": "Node.js is a JavaScript runtime built on Chrome's V8 engine...",
        "metadata": {"source": "nodejs.org", "topic": "backend", "runtime": "nodejs"}
    },
    {
        "text": "Docker is a platform for developing, shipping, and running applications...",
        "metadata": {"source": "docker.com", "topic": "devops", "tool": "docker"}
    }
]

# Add each document
for doc in documents:
    response = requests.post(
        "http://localhost:8000/add_document",
        json=doc
    )
    if response.status_code == 200:
        result = response.json()
        print(f"Added document: {result['id'][:8]}...")
    else:
        print(f"Failed to add document: {response.text}")
```

#### Bulk Search (Python Script)
```python
import requests

# Multiple search queries
queries = [
    "JavaScript frameworks",
    "container technology",
    "backend development",
    "web development tools"
]

for query in queries:
    response = requests.get(
        f"http://localhost:8000/search",
        params={"query": query, "limit": 2}
    )

    if response.status_code == 200:
        results = response.json()
        print(f"\nQuery: {query}")
        print(f"Found {len(results)} results:")
        for i, result in enumerate(results, 1):
            print(f"  {i}. Score: {result['score']:.3f} - {result['metadata'].get('topic', 'unknown')}")
    else:
        print(f"Search failed: {response.text}")
```

---

## Client Libraries

### Python Client Example
```python
import requests
from typing import List, Dict, Any

class RAGClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url

    def add_document(self, text: str, metadata: Dict = None) -> Dict:
        """Add a document to the RAG system."""
        payload = {"text": text}
        if metadata:
            payload["metadata"] = metadata

        response = requests.post(f"{self.base_url}/add_document", json=payload)
        response.raise_for_status()
        return response.json()

    def search(self, query: str, limit: int = 5) -> List[Dict]:
        """Search for similar documents."""
        params = {"query": query, "limit": limit}
        response = requests.get(f"{self.base_url}/search", params=params)
        response.raise_for_status()
        return response.json()

    def chat(self, question: str, max_results: int = 3) -> Dict:
        """Ask a question and get a contextual answer."""
        payload = {"question": question, "max_results": max_results}
        response = requests.post(f"{self.base_url}/chat", json=payload)
        response.raise_for_status()
        return response.json()

    def health(self) -> Dict:
        """Get system health status."""
        response = requests.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()

# Usage example
client = RAGClient()

# Add a document
result = client.add_document(
    text="FastAPI is a modern web framework for building APIs with Python.",
    metadata={"source": "fastapi.tiangolo.com", "topic": "web-framework"}
)
print(f"Document added: {result['id']}")

# Search
results = client.search("Python web framework", limit=3)
print(f"Found {len(results)} results")

# Chat
answer = client.chat("What is FastAPI good for?")
print(f"Answer: {answer['answer']}")
```

### JavaScript/Node.js Client Example
```javascript
class RAGClient {
    constructor(baseUrl = 'http://localhost:8000') {
        this.baseUrl = baseUrl;
    }

    async addDocument(text, metadata = {}) {
        const response = await fetch(`${this.baseUrl}/add_document`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text, metadata })
        });

        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return response.json();
    }

    async search(query, limit = 5) {
        const params = new URLSearchParams({ query, limit });
        const response = await fetch(`${this.baseUrl}/search?${params}`);

        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return response.json();
    }

    async chat(question, maxResults = 3) {
        const response = await fetch(`${this.baseUrl}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question, max_results: maxResults })
        });

        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return response.json();
    }
}

// Usage
const client = new RAGClient();

// Add document
const result = await client.addDocument(
    "Vue.js is a progressive framework for building user interfaces.",
    { source: "vuejs.org", topic: "frontend" }
);
console.log(`Document added: ${result.id}`);

// Search and chat
const results = await client.search("Vue framework");
const answer = await client.chat("What is Vue.js?");
console.log(answer.answer);
```

---

## Common Use Cases

### 1. Documentation Assistant
**Scenario**: Help users find information in your documentation

```bash
# Add documentation pages
curl -X POST "http://localhost:8000/add_document" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "To install the package, run: pip install my-package. This will install all dependencies automatically.",
    "metadata": {"page": "installation", "section": "quick-start"}
  }'

# Users can ask questions
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "How do I install the package?",
    "max_results": 2
  }'
```

### 2. Research Assistant
**Scenario**: Help researchers find relevant papers and information

```bash
# Add research papers
curl -X POST "http://localhost:8000/add_document" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "This paper introduces a novel approach to transformer architectures that reduces training time by 40% while maintaining accuracy.",
    "metadata": {"type": "paper", "authors": "Smith et al.", "year": 2024, "venue": "ICML"}
  }'

# Find related research
curl "http://localhost:8000/search?query=transformer%20optimization&limit=5"
```

### 3. Customer Support
**Scenario**: Automated customer support with knowledge base

```bash
# Add FAQ entries
curl -X POST "http://localhost:8000/add_document" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "If you forgot your password, click the 'Forgot Password' link on the login page. You will receive a reset email within 5 minutes.",
    "metadata": {"category": "account", "type": "faq", "priority": "high"}
  }'

# Customer questions
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "I cannot remember my password, what should I do?",
    "max_results": 2
  }'
```

### 4. Content Discovery
**Scenario**: Help users discover relevant content

```bash
# Add articles
curl -X POST "http://localhost:8000/add_document" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "10 tips for better productivity: 1. Use time blocking, 2. Eliminate distractions, 3. Take regular breaks...",
    "metadata": {"category": "productivity", "author": "Jane Doe", "tags": ["tips", "work"]}
  }'

# Discover content
curl "http://localhost:8000/search?query=productivity%20tips&limit=3"
```

---

## Development & Deployment

### Development Environment

#### Running in Development Mode
```bash
# Install development dependencies
make install-dev

# Run with auto-reload
make run

# Enable debug logging
export LOG_LEVEL=DEBUG
make run
```

#### Testing
```bash
# Run all tests
make test

# Run with coverage
make test-coverage

# Run unit tests only
make test-unit

# Run integration tests
make test-integration
```

#### Code Quality
```bash
# Format code
make format

# Run linter
make lint

# Run all code quality checks
make check
```

### Production Deployment

#### Docker Production
```bash
# Build production image
make docker-build

# Run production container
docker run -d \
  --name rag-system-prod \
  -p 8000:8000 \
  --env-file .env \
  -v /path/to/persistent/storage:/app/chroma_db \
  --restart unless-stopped \
  rag-system
```

#### Environment Variables
```bash
# Production settings
export LOG_LEVEL=INFO
export CHROMADB_PATH=/app/chroma_db
export MODEL_SLUG=openai/gpt-4
export MAX_WORKERS=4
```

#### Health Monitoring
```bash
# Check health endpoint
curl http://localhost:8000/health

# Monitor logs
docker logs -f rag-system-prod

# Resource monitoring
docker stats rag-system-prod
```

#### Scaling Considerations
- **Memory**: 512MB minimum, 2GB recommended for production
- **CPU**: 1 core minimum, 2+ cores for high traffic
- **Storage**: SSD recommended for ChromaDB performance
- **Network**: Consider rate limiting for public APIs

### Configuration Management

#### Required Environment Variables
```bash
# Essential
OPENROUTER_API_KEY=sk-or-v1-xxx  # Your OpenRouter API key

# Optional with defaults
CHROMADB_PATH=./chroma_db          # Database storage path
EMBEDDING_MODEL=all-MiniLM-L6-v2   # Sentence transformer model
MODEL_SLUG=openai/gpt-3.5-turbo    # LLM model for generation
LOG_LEVEL=INFO                     # Logging level
HOST=0.0.0.0                       # Server host
PORT=8000                          # Server port
```

#### Security Configuration
```bash
# Production security
export ALLOWED_HOSTS=yourdomain.com,api.yourdomain.com
export CORS_ORIGINS=https://yourdomain.com
export API_KEY_REQUIRED=true  # If implementing API key auth
```

---

## Troubleshooting

### Common Issues and Solutions

#### 1. Server Won't Start
**Error**: `Failed to initialize RAG system`

**Solutions**:
```bash
# Check if port is already in use
lsof -i :8000

# Try a different port
python -m uvicorn app.main:app --port 8001

# Check dependencies
make install

# Verify configuration
cat .env
```

#### 2. Embedding Model Download Fails
**Error**: `SSL: CERTIFICATE_VERIFY_FAILED`

**Solutions**:
```bash
# Update certificates
pip install --upgrade certifi

# Use fallback mode (for testing)
# The system automatically falls back to hash-based embeddings

# Manual model download
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"
```

#### 3. OpenRouter API Errors
**Error**: `API Error: 401 Unauthorized`

**Solutions**:
```bash
# Check API key format
echo $OPENROUTER_API_KEY  # Should start with 'sk-or-v1-'

# Verify key in .env file
grep OPENROUTER_API_KEY .env

# Test API key directly
curl -H "Authorization: Bearer $OPENROUTER_API_KEY" \
     -H "Content-Type: application/json" \
     https://openrouter.ai/api/v1/models
```

#### 4. ChromaDB Connection Issues
**Error**: `Failed to connect to ChromaDB`

**Solutions**:
```bash
# Check database path permissions
ls -la ./chroma_db/

# Reset database (careful - this deletes all data)
rm -rf ./chroma_db/
python -c "from app.database import ChromaDBManager; ChromaDBManager().get_or_create_collection('documents')"

# Check disk space
df -h .
```

#### 5. Memory Issues
**Error**: `MemoryError` or slow performance

**Solutions**:
```bash
# Monitor memory usage
free -h  # Linux
top -l 1 | head -n 10  # macOS

# Reduce batch size in config
export BATCH_SIZE=10  # Default is 100

# Use lighter embedding model
export EMBEDDING_MODEL=all-MiniLM-L12-v2
```

#### 6. Docker Issues
**Error**: `Container exits immediately`

**Solutions**:
```bash
# Check container logs
docker logs rag-system

# Run interactively for debugging
docker run -it --rm rag-system /bin/bash

# Check environment variables
docker exec rag-system env | grep -E "(OPENROUTER|CHROMADB|MODEL)"

# Port conflicts
docker ps  # Check if port 8000 is used
```

#### 7. Performance Issues
**Symptoms**: Slow response times, high CPU usage

**Solutions**:
```bash
# Enable performance monitoring
export LOG_LEVEL=DEBUG

# Check database size
du -sh ./chroma_db/

# Optimize ChromaDB
python -c "
from app.database import ChromaDBManager
db = ChromaDBManager()
collection = db.get_collection('documents')
print(f'Documents: {collection.count()}')
"

# Use faster model for embeddings
export EMBEDDING_MODEL=all-MiniLM-L6-v2  # Fastest
```

#### Debug Mode
Enable detailed logging for troubleshooting:

```bash
# Set debug environment
export LOG_LEVEL=DEBUG
export PYTHONPATH=$PWD

# Run with detailed output
python -m app.main 2>&1 | tee debug.log

# Check specific component
python -c "
import logging
logging.basicConfig(level=logging.DEBUG)
from app.rag import RAGSystem
rag = RAGSystem()
print('RAG system initialized successfully')
"
```
```bash
# Check your API key
echo $OPENROUTER_API_KEY

# Verify key format (should start with sk-or-)
# Get a new key from https://openrouter.ai/

# Test without API key (uses mock responses)
# Comment out OPENROUTER_API_KEY in .env
```

#### 4. ChromaDB Issues
**Error**: `Failed to create collection`

**Solutions**:
```bash
# Check permissions
ls -la ./chroma_db/

# Reset database
rm -rf ./chroma_db/
# Restart the server

# Check disk space
df -h
```

#### 5. Memory Issues
**Error**: `Out of memory`

**Solutions**:
```bash
# Reduce batch size in embeddings
# Monitor memory usage
htop

# Use smaller embedding model
# Edit .env: EMBEDDING_MODEL=all-MiniLM-L6-v2

# Restart with memory limits
docker run --memory=2g ...
```

### Debug Mode

Enable debug logging:
```bash
export LOG_LEVEL=DEBUG
python -m uvicorn app.main:app --log-level debug
```

### Health Checks

Monitor system health:
```bash
# Basic health
curl http://localhost:8000/

# Detailed health
curl http://localhost:8000/health

# Test embeddings
curl -X POST "http://localhost:8000/add_document" \
  -H "Content-Type: application/json" \
  -d '{"text": "test"}'
```

---

## Performance Tips

### 1. Optimize Document Loading
```bash
# Add documents in batches
# Use shorter, focused documents
# Include relevant metadata for filtering
```

### 2. Search Optimization
```bash
# Use specific queries rather than generic ones
# Limit results to what you need
curl "http://localhost:8000/search?query=specific%20topic&limit=3"

# Use metadata for filtering (if implemented)
```

### 3. Chat Performance
```bash
# Limit context documents
curl -X POST "http://localhost:8000/chat" \
  -d '{"question": "...", "max_results": 2}'  # Instead of 5+

# Use shorter questions when possible
# Be specific in your questions
```

### 4. System Optimization
```bash
# Use SSD storage for ChromaDB
# Allocate sufficient RAM (1GB+ recommended)
# Use multiple workers in production
python -m uvicorn app.main:app --workers 4

# Enable HTTP caching (nginx/cloudflare)
# Use persistent connections
```

### 5. Monitoring
```bash
# Monitor response times
curl -w "@curl-format.txt" http://localhost:8000/health

# Monitor memory usage
ps aux | grep uvicorn

# Check database size
du -sh ./chroma_db/
```

---

## Advanced Usage

### Custom Metadata Schemas
```json
{
  "text": "Document content...",
  "metadata": {
    "title": "Document Title",
    "author": "Author Name",
    "date": "2024-01-15",
    "tags": ["tag1", "tag2"],
    "category": "category_name",
    "language": "en",
    "source_url": "https://example.com",
    "confidence": 0.95,
    "version": "1.0"
  }
}
```

### Bulk Operations Script
```bash
# Save as bulk_upload.py
python bulk_upload.py documents.jsonl
```

### Integration with Web Scrapers
```python
import requests
from bs4 import BeautifulSoup

def scrape_and_add(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    text = soup.get_text()

    # Add to RAG system
    client.add_document(
        text=text,
        metadata={"source": url, "scraped_at": "2024-01-15"}
    )
```
