# RAG System - Production Ready Implementation

A complete **Retrieval-Augmented Generation (RAG)** system built with modern software engineering practices. Combine document storage, semantic search, and AI-powered question answering in a production-ready API.

## Documentation

- **[Complete Documentation](docs/)** - Comprehensive guides and references
- **[API Reference](docs/api-reference.md)** - Complete endpoint documentation
- **[API Usage Examples](docs/api-usage.md)** - Code examples and tutorials
- **[Configuration Guide](docs/configuration.md)** - Environment variables and settings
- **[Interactive API Docs](http://localhost:8000/docs)** - Swagger UI (when running)

## Key Features

- **Semantic Search** - Find relevant documents using vector similarity
- **AI Question Answering** - Generate contextual answers using LLMs
- **Vector Database** - Efficient storage with ChromaDB
- **FastAPI Backend** - Modern API with automatic documentation
- **Docker Ready** - Container deployment included
- **OpenTelemetry** - Built-in observability and tracing
- **Production Ready** - Error handling, validation, and monitoring

## Quick Start

### 1. Installation
```bash
git clone <your-repo-url>
cd llm-rag-test
python -m venv .venv
source .venv/bin/activate
make install
```

### 2. Configuration
```bash
cp .env.example .env
# Edit .env with your OpenRouter API key
```

### 3. Start the Server
```bash
make run
```

### 4. Test the API
```bash
# Check health
curl http://localhost:8000/

# Add a document
curl -X POST "http://localhost:8000/add_document" \
  -H "Content-Type: application/json" \
  -d '{"text": "Python is a programming language", "metadata": {"source": "manual"}}'

# Ask questions
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is Python?", "max_results": 3}'
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | System health and info |
| `/health` | GET | Detailed health check |
| `/add_document` | POST | Add document to database |
| `/search` | GET | Search similar documents |
| `/chat` | POST | RAG-powered Q&A |
| `/documents/{doc_id}` | GET | Get specific document |
| `/documents/{doc_id}` | PUT | Update specific document |
| `/documents/{doc_id}` | DELETE | Delete specific document |
| `/documents/bulk` | POST | Add multiple documents |
| `/docs` | GET | Interactive API documentation |

## Docker Deployment

```bash
# Build and run with Docker
make docker-build
make docker-run

# Or use Docker Compose
docker-compose up -d
```

## Configuration

Key environment variables:
```bash
OPENROUTER_API_KEY=your_api_key_here     # Required for LLM functionality
CHROMADB_PATH=./chroma_db                # Database storage path
EMBEDDING_MODEL=all-MiniLM-L6-v2         # Embedding model
MODEL_SLUG=openai/gpt-3.5-turbo         # LLM model
```

See **[Configuration Guide](docs/configuration.md)** for complete options.

## Development

### Code Structure
```
app/
├── main.py              # FastAPI application
├── models.py            # Data models
├── config.py            # Configuration
├── database.py          # ChromaDB integration
├── embeddings.py        # Text embeddings
├── rag.py              # RAG pipeline
└── telemetry_simple.py  # OpenTelemetry setup
```

### Development Setup
```bash
# See all available commands
make help

# Install dev dependencies
make install-dev

# Run tests
make test

# Code quality
make lint
make format
make check

# Full development setup
make setup-dev
```

## Key Technologies

- **[FastAPI](https://fastapi.tiangolo.com/)** - Modern Python web framework
- **[ChromaDB](https://www.trychroma.com/)** - Vector database
- **[SentenceTransformers](https://www.sbert.net/)** - Text embeddings
- **[OpenRouter](https://openrouter.ai/)** - LLM API gateway
- **[OpenTelemetry](https://opentelemetry.io/)** - Observability framework
