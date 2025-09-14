# API Reference

Complete reference for all RAG System API endpoints with detailed examples and response schemas.

## Base Information

- **Base URL**: `http://localhost:8000`
- **API Version**: v1
- **Content Type**: `application/json`
- **Authentication**: API key via environment variables

## Endpoint Overview

| Endpoint | Method | Purpose | Authentication |
|----------|--------|---------|----------------|
| `/` | GET | System information and health | None |
| `/health` | GET | Detailed health check | None |
| `/add_document` | POST | Add document to database | None |
| `/search` | GET | Search similar documents | None |
| `/chat` | POST | RAG-powered Q&A | None |
| `/documents/{doc_id}` | GET | Get specific document | None |
| `/documents/{doc_id}` | PUT | Update specific document | None |
| `/documents/{doc_id}` | DELETE | Delete specific document | None |
| `/documents/bulk` | POST | Add multiple documents | None |
| `/docs` | GET | Interactive API documentation | None |

## Detailed Endpoint Reference

### 1. System Information

#### `GET /`

**Purpose**: Get basic system information and health status.

**Parameters**: None

**Request Example**:
```bash
curl http://localhost:8000/
```

**Response Schema**:
```json
{
  "name": "string",
  "version": "string",
  "status": "string",
  "components": {
    "database": "string",
    "embedding_model": "string",
    "llm_model": "string",
    "fallback_mode": "boolean"
  },
  "statistics": {
    "document_count": "integer",
    "collection_name": "string"
  }
}
```

**Response Example**:
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

**Status Codes**:
- `200 OK`: System is healthy
- `503 Service Unavailable`: System has issues

### 2. Health Check

#### `GET /health`

**Purpose**: Detailed health check with component status.

**Parameters**: None

**Request Example**:
```bash
curl http://localhost:8000/health
```

**Response Schema**:
```json
{
  "status": "string",
  "timestamp": "number",
  "components": {
    "database": {
      "status": "string",
      "document_count": "integer",
      "collection_name": "string"
    },
    "embeddings": {
      "status": "string",
      "fallback_mode": "boolean",
      "dimension": "integer",
      "model": "string"
    },
    "api": {
      "status": "string",
      "configured": "boolean"
    }
  }
}
```

**Response Example**:
```json
{
  "status": "healthy",
  "timestamp": 1641024000.0,
  "components": {
    "database": {
      "status": "healthy",
      "document_count": 42,
      "collection_name": "documents"
    },
    "embeddings": {
      "status": "healthy",
      "fallback_mode": false,
      "dimension": 384,
      "model": "all-MiniLM-L6-v2"
    },
    "api": {
      "status": "healthy",
      "configured": true
    }
  }
}
```

**Status Codes**:
- `200 OK`: All components healthy
- `503 Service Unavailable`: One or more components unhealthy

### 3. Add Document

#### `POST /add_document`

**Purpose**: Add a new document to the vector database.

**Request Schema**:
```json
{
  "text": "string (required, max 50000 chars)",
  "metadata": "object (optional)"
}
```

**Request Example**:
```bash
curl -X POST "http://localhost:8000/add_document" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Python is a high-level programming language known for its simplicity and readability. It supports multiple programming paradigms and has a vast ecosystem of libraries.",
    "metadata": {
      "source": "documentation",
      "topic": "programming",
      "language": "python",
      "author": "system",
      "created_at": "2024-01-15T10:00:00Z"
    }
  }'
```

**Response Schema**:
```json
{
  "success": "boolean",
  "id": "string",
  "message": "string",
  "metadata": {
    "text_length": "integer",
    "embedding_dimension": "integer",
    "timestamp": "number"
  }
}
```

**Response Example**:
```json
{
  "success": true,
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Document added successfully",
  "metadata": {
    "text_length": 156,
    "embedding_dimension": 384,
    "timestamp": 1641024000.0
  }
}
```

**Status Codes**:
- `200 OK`: Document added successfully
- `400 Bad Request`: Invalid input (empty text, too long, invalid JSON)
- `500 Internal Server Error`: Processing failed

**Error Response Example**:
```json
{
  "detail": "Document text cannot be empty"
}
```

### 4. Search Documents

#### `GET /search`

**Purpose**: Find documents similar to a query using semantic search.

**Parameters**:
- `query` (required): Search query text
- `limit` (optional): Maximum results to return (1-20, default: 5)

**Request Example**:
```bash
# Basic search
curl "http://localhost:8000/search?query=machine%20learning"

# With limit
curl "http://localhost:8000/search?query=Python%20programming&limit=3"

# URL encoding for complex queries
curl "http://localhost:8000/search?query=artificial%20intelligence%20and%20neural%20networks&limit=10"
```

**Response Schema**:
```json
[
  {
    "content": "string",
    "score": "number (0.0-1.0)",
    "metadata": "object"
  }
]
```

**Response Example**:
```json
[
  {
    "content": "Machine learning is a subset of artificial intelligence that enables computers to learn and improve from experience without being explicitly programmed.",
    "score": 0.8756,
    "metadata": {
      "source": "wikipedia",
      "topic": "AI",
      "author": "system",
      "created_at": "2024-01-10T15:30:00Z"
    }
  },
  {
    "content": "Deep learning algorithms use neural networks with multiple layers to model and understand complex patterns in data.",
    "score": 0.7432,
    "metadata": {
      "source": "textbook",
      "topic": "AI",
      "chapter": "Neural Networks"
    }
  }
]
```

**Status Codes**:
- `200 OK`: Search completed successfully (may return empty array)
- `400 Bad Request`: Invalid parameters (empty query, invalid limit)
- `422 Unprocessable Entity`: Parameter validation failed

**Error Response Example**:
```json
{
  "detail": [
    {
      "loc": ["query", "limit"],
      "msg": "ensure this value is less than or equal to 20",
      "type": "value_error.number.not_le",
      "ctx": {"limit_value": 20}
    }
  ]
}
```

### 5. Chat (RAG Q&A)

#### `POST /chat`

**Purpose**: Generate contextual answers using retrieved documents and LLM.

**Request Schema**:
```json
{
  "question": "string (required)",
  "max_results": "integer (optional, 1-10, default: 3)"
}
```

**Request Example**:
```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is the difference between machine learning and deep learning?",
    "max_results": 3
  }'
```

**Response Schema**:
```json
{
  "answer": "string",
  "sources": [
    {
      "content": "string",
      "score": "number (0.0-1.0)",
      "metadata": "object"
    }
  ],
  "model_used": "string",
  "tokens_used": "integer",
  "processing_time": "number",
  "context_documents_found": "integer"
}
```

**Response Example**:
```json
{
  "answer": "Based on the retrieved documents, machine learning is a broader field of artificial intelligence that enables computers to learn from data without explicit programming. Deep learning is a subset of machine learning that uses neural networks with multiple layers (deep neural networks) to model complex patterns in data. The key difference is that deep learning specifically uses layered neural network architectures, while machine learning encompasses various algorithms including decision trees, linear regression, and neural networks.",
  "sources": [
    {
      "content": "Machine learning is a subset of artificial intelligence that enables computers to learn and improve from experience without being explicitly programmed.",
      "score": 0.876,
      "metadata": {
        "source": "wikipedia",
        "topic": "AI"
      }
    },
    {
      "content": "Deep learning algorithms use neural networks with multiple layers to model and understand complex patterns in data.",
      "score": 0.743,
      "metadata": {
        "source": "textbook",
        "topic": "AI",
        "chapter": "Neural Networks"
      }
    }
  ],
  "model_used": "openai/gpt-3.5-turbo",
  "tokens_used": 245,
  "processing_time": 1.23,
  "context_documents_found": 2
}
```

**Status Codes**:
- `200 OK`: Answer generated successfully
- `400 Bad Request`: Invalid input (empty question, invalid max_results)
- `500 Internal Server Error`: LLM API error or processing failed

**Error Response Example**:
```json
{
  "detail": "Failed to generate answer: API Error: 401 Unauthorized"
}
```

### 6. Get Document

#### `GET /documents/{doc_id}`

**Purpose**: Retrieve a specific document by its ID.

**Parameters**:
- `doc_id` (path): Document ID returned from add_document

**Request Example**:
```bash
curl http://localhost:8000/documents/doc_45b8cab79bca06e0_d1f15b2a
```

**Response Schema**:
```json
{
  "id": "string",
  "document": "string",
  "metadata": "object",
  "embedding": "array[number]"
}
```

**Response Example**:
```json
{
  "id": "doc_45b8cab79bca06e0_d1f15b2a",
  "document": "Python is a high-level programming language...",
  "metadata": {
    "source": "documentation",
    "topic": "programming",
    "text_length": 156,
    "timestamp": 1641024000.0
  },
  "embedding": [0.0796, 0.0206, 0.0100, ...]
}
```

**Status Codes**:
- `200 OK`: Document found
- `404 Not Found`: Document not found

### 7. Update Document

#### `PUT /documents/{doc_id}`

**Purpose**: Update an existing document.

**Parameters**:
- `doc_id` (path): Document ID to update

**Request Schema**:
```json
{
  "text": "string (required)",
  "metadata": "object (optional)"
}
```

**Request Example**:
```bash
curl -X PUT "http://localhost:8000/documents/doc_45b8cab79bca06e0_d1f15b2a" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Updated Python is a high-level programming language...",
    "metadata": {"source": "updated_documentation", "version": "2.0"}
  }'
```

**Response Schema**:
```json
{
  "success": "boolean",
  "message": "string",
  "id": "string"
}
```

**Status Codes**:
- `200 OK`: Document updated successfully
- `404 Not Found`: Document not found
- `400 Bad Request`: Invalid input

### 8. Delete Document

#### `DELETE /documents/{doc_id}`

**Purpose**: Delete a specific document.

**Parameters**:
- `doc_id` (path): Document ID to delete

**Request Example**:
```bash
curl -X DELETE "http://localhost:8000/documents/doc_45b8cab79bca06e0_d1f15b2a"
```

**Response Schema**:
```json
{
  "success": "boolean",
  "message": "string"
}
```

**Status Codes**:
- `200 OK`: Document deleted successfully
- `404 Not Found`: Document not found

### 9. Bulk Add Documents

#### `POST /documents/bulk`

**Purpose**: Add multiple documents in a single request.

**Request Schema**:
```json
{
  "documents": [
    {
      "text": "string (required)",
      "metadata": "object (optional)"
    }
  ],
  "allow_duplicates": "boolean (optional, default: false)"
}
```

**Request Example**:
```bash
curl -X POST "http://localhost:8000/documents/bulk" \
  -H "Content-Type: application/json" \
  -d '{
    "documents": [
      {
        "text": "First document content...",
        "metadata": {"source": "batch1", "topic": "science"}
      },
      {
        "text": "Second document content...",
        "metadata": {"source": "batch1", "topic": "technology"}
      }
    ],
    "allow_duplicates": true
  }'
```

**Response Schema**:
```json
{
  "message": "string",
  "documents_added": "integer",
  "document_ids": "array[string]",
  "total_requested": "integer"
}
```

**Response Example**:
```json
{
  "message": "Bulk add completed",
  "documents_added": 2,
  "document_ids": [
    "doc_45b8cab79bca06e0_d1f15b2a",
    "doc_a89b3f014427ad52_ddd23eba"
  ],
  "total_requested": 2
}
```

**Status Codes**:
- `200 OK`: Bulk operation completed (check documents_added vs total_requested)
- `400 Bad Request`: Invalid input format

## Advanced Usage Examples

### Batch Document Addition

```python
import requests

documents = [
    {
        "text": "FastAPI is a modern web framework for building APIs with Python.",
        "metadata": {"source": "fastapi.tiangolo.com", "topic": "web-framework"}
    },
    {
        "text": "Vue.js is a progressive framework for building user interfaces.",
        "metadata": {"source": "vuejs.org", "topic": "frontend"}
    },
    {
        "text": "Docker is a platform for developing, shipping, and running applications in containers.",
        "metadata": {"source": "docker.com", "topic": "devops"}
    }
]

# Add documents sequentially
for doc in documents:
    response = requests.post("http://localhost:8000/add_document", json=doc)
    if response.status_code == 200:
        result = response.json()
        print(f"Added: {result['id'][:8]}... ({result['metadata']['text_length']} chars)")
    else:
        print(f"Failed: {response.status_code} - {response.text}")
```

### Advanced Search with Filtering

```python
import requests

def search_with_context(query, limit=5):
    """Search documents and return with enhanced context."""
    response = requests.get(
        "http://localhost:8000/search",
        params={"query": query, "limit": limit}
    )

    if response.status_code == 200:
        results = response.json()
        print(f"Query: {query}")
        print(f"Found {len(results)} results:\n")

        for i, result in enumerate(results, 1):
            print(f"{i}. Score: {result['score']:.3f}")
            print(f"   Content: {result['content'][:100]}...")
            if result['metadata']:
                print(f"   Metadata: {result['metadata']}")
            print()
    else:
        print(f"Search failed: {response.status_code} - {response.text}")

# Example usage
search_with_context("Python web frameworks", 3)
search_with_context("container deployment", 5)
```

### Conversational Chat Interface

```python
import requests

class RAGChat:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url

    def ask(self, question, max_results=3):
        """Ask a question and get a contextual answer."""
        response = requests.post(
            f"{self.base_url}/chat",
            json={"question": question, "max_results": max_results}
        )

        if response.status_code == 200:
            result = response.json()
            print(f"Answer: {result['answer']}\n")
            print(f"Sources ({len(result['sources'])}):")
            for i, source in enumerate(result['sources'], 1):
                print(f"   {i}. Score: {source['similarity_score']:.3f}")
                if source['metadata']:
                    print(f"      Source: {source['metadata'].get('source', 'unknown')}")
            print(f"\nModel: {result['model_used']} | Tokens: {result['tokens_used']} | Time: {result['processing_time']:.2f}s")
        else:
            print(f"Chat failed: {response.status_code} - {response.text}")

# Example usage
chat = RAGChat()
chat.ask("How do I deploy a web application using containers?")
chat.ask("What are the benefits of using modern web frameworks?")
```

## Query Parameters Reference

### Search Endpoint Parameters

| Parameter | Type | Required | Default | Range | Description |
|-----------|------|----------|---------|-------|-------------|
| `query` | string | Yes | - | 1-1000 chars | Search query text |
| `limit` | integer | No | 5 | 1-20 | Max results to return |

### Chat Endpoint Parameters

| Field | Type | Required | Default | Range | Description |
|-------|------|----------|---------|-------|-------------|
| `question` | string | Yes | - | 1-1000 chars | Question to answer |
| `max_results` | integer | No | 3 | 1-10 | Max context documents |

## 🚨 Error Handling

### Common Error Responses

#### 400 Bad Request
```json
{
  "detail": "Question cannot be empty"
}
```

#### 422 Unprocessable Entity
```json
{
  "detail": [
    {
      "loc": ["body", "text"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

#### 500 Internal Server Error
```json
{
  "detail": "Failed to generate answer: Connection timeout"
}
```

### Error Code Reference

| Status Code | Meaning | Common Causes |
|-------------|---------|---------------|
| 400 | Bad Request | Empty fields, invalid format |
| 422 | Unprocessable Entity | Validation errors, type mismatches |
| 500 | Internal Server Error | Database errors, API failures |
| 503 | Service Unavailable | System unhealthy, dependencies down |

## Client SDK Examples

### Python Client
```python
import requests
from typing import List, Dict, Optional

class RAGClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip('/')

    def health(self) -> Dict:
        """Check system health."""
        response = requests.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()

    def add_document(self, text: str, metadata: Optional[Dict] = None) -> Dict:
        """Add a document."""
        payload = {"text": text}
        if metadata:
            payload["metadata"] = metadata

        response = requests.post(f"{self.base_url}/add_document", json=payload)
        response.raise_for_status()
        return response.json()

    def search(self, query: str, limit: int = 5) -> List[Dict]:
        """Search documents."""
        params = {"query": query, "limit": limit}
        response = requests.get(f"{self.base_url}/search", params=params)
        response.raise_for_status()
        return response.json()

    def chat(self, question: str, max_results: int = 3) -> Dict:
        """Ask a question."""
        payload = {"question": question, "max_results": max_results}
        response = requests.post(f"{self.base_url}/chat", json=payload)
        response.raise_for_status()
        return response.json()
```
