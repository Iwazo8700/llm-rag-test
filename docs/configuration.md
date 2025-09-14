# Configuration Reference

Complete reference for all configuration options in the RAG System.

## Environment Variables

### Required Configuration

#### API Keys
```bash
# OpenRouter API Key (Required for LLM functionality)
OPENROUTER_API_KEY=sk-or-your-api-key-here
# Get your key from: https://openrouter.ai/
# Format: Must start with "sk-or-"
```

### Optional Configuration

#### API Settings
```bash
# OpenRouter API endpoint
OPENROUTER_API_URL=https://openrouter.ai/api/v1/chat/completions
# Default: https://openrouter.ai/api/v1/chat/completions

# HTTP Referer header for API requests
OPENROUTER_HTTP_REFERER=https://github.com/your-username/rag-system
# Default: https://github.com/your-username/rag-system

# Application title for API requests
OPENROUTER_APP_TITLE=RAG System
# Default: RAG System
```

#### Database Configuration
```bash
# ChromaDB storage path
CHROMADB_PATH=./chroma_db
# Default: ./chroma_db
# Can be absolute or relative path

# Collection name
COLLECTION_NAME=documents
# Default: documents
# Name for the document collection in ChromaDB
```

#### Model Configuration
```bash
# Embedding model name
EMBEDDING_MODEL=all-MiniLM-L6-v2
# Default: all-MiniLM-L6-v2
# Options: See "Model Options" section below

# LLM model identifier
MODEL_SLUG=openai/gpt-3.5-turbo
# Default: openai/gpt-3.5-turbo
# Options: See "LLM Models" section below

# Use mock LLM responses (for testing)
USE_MOCK_LLM=false
# Default: false
# Set to true to use mock responses instead of real API calls
```

#### Performance Configuration
```bash
# API request timeout (seconds)
REQUEST_TIMEOUT=30
# Default: 30
# Timeout for external API calls

# Maximum document length (characters)
MAX_DOCUMENT_LENGTH=50000
# Default: 50000
# Documents longer than this will be rejected

# Default search result limit
DEFAULT_SEARCH_LIMIT=5
# Default: 5
# Default number of results returned by search endpoint

# Maximum search result limit
MAX_SEARCH_RESULTS=20
# Default: 20
# Maximum number of results that can be requested

# Maximum chat context documents
MAX_CHAT_RESULTS=10
# Default: 10
# Maximum number of context documents for chat endpoint
```

#### Logging Configuration
```bash
# Log level
LOG_LEVEL=INFO
# Default: INFO
# Options: DEBUG, INFO, WARNING, ERROR, CRITICAL

# Log format
LOG_FORMAT=%(asctime)s - %(name)s - %(levelname)s - %(message)s
# Default: %(asctime)s - %(name)s - %(levelname)s - %(message)s

# Log file path (optional)
LOG_FILE=/var/log/rag-system/app.log
# Default: None (console only)
# Set to enable file logging
```

#### OpenTelemetry Configuration
```bash
# Service name for tracing
OTEL_SERVICE_NAME=rag-system
# Default: rag-system

# Service version
OTEL_SERVICE_VERSION=1.0.0
# Default: 1.0.0

# Environment name
OTEL_ENVIRONMENT=development
# Default: development
# Options: development, staging, production

# Jaeger tracing endpoint
JAEGER_ENDPOINT=http://localhost:14268/api/traces
# Default: http://localhost:14268/api/traces

# Export traces to console
OTEL_CONSOLE_EXPORT=true
# Default: true
# Set to false to disable console trace export

# Resource attributes
OTEL_RESOURCE_ATTRIBUTES=service.name=rag-system,service.version=1.0.0
# Default: service.name=rag-system,service.version=1.0.0
```

## Model Options

### Embedding Models

#### Recommended Models
```bash
# All-MiniLM-L6-v2 (Default)
EMBEDDING_MODEL=all-MiniLM-L6-v2
# Size: ~90MB, Dimensions: 384
# Performance: Fast, good quality
# Best for: General purpose, balanced speed/quality

# All-mpnet-base-v2
EMBEDDING_MODEL=all-mpnet-base-v2
# Size: ~420MB, Dimensions: 768
# Performance: Higher quality, slower
# Best for: Maximum quality, semantic similarity

# Multi-qa-MiniLM-L6-cos-v1
EMBEDDING_MODEL=multi-qa-MiniLM-L6-cos-v1
# Size: ~90MB, Dimensions: 384
# Performance: Optimized for Q&A
# Best for: Question-answering applications
```

#### Multilingual Models
```bash
# Paraphrase-multilingual-MiniLM-L12-v2
EMBEDDING_MODEL=paraphrase-multilingual-MiniLM-L12-v2
# Size: ~470MB, Dimensions: 384
# Languages: 50+ languages
# Best for: Multilingual applications

# Paraphrase-multilingual-mpnet-base-v2
EMBEDDING_MODEL=paraphrase-multilingual-mpnet-base-v2
# Size: ~970MB, Dimensions: 768
# Languages: 50+ languages
# Best for: Multilingual, high quality
```

#### Specialized Models
```bash
# msmarco-distilbert-base-tas-b
EMBEDDING_MODEL=msmarco-distilbert-base-tas-b
# Size: ~250MB, Dimensions: 768
# Optimized for: Information retrieval
# Best for: Document search applications

# all-distilroberta-v1
EMBEDDING_MODEL=all-distilroberta-v1
# Size: ~290MB, Dimensions: 768
# Performance: Good quality, reasonable speed
# Best for: English text similarity
```

### LLM Models

#### OpenAI Models
```bash
# GPT-3.5 Turbo (Default)
MODEL_SLUG=openai/gpt-3.5-turbo
# Speed: Fast, Cost: Low
# Context: 4k tokens, Quality: Good
# Best for: General purpose, cost-effective

# GPT-4
MODEL_SLUG=openai/gpt-4
# Speed: Moderate, Cost: High
# Context: 8k tokens, Quality: Excellent
# Best for: Complex reasoning, high quality

# GPT-4 Turbo
MODEL_SLUG=openai/gpt-4-turbo
# Speed: Fast, Cost: Moderate
# Context: 128k tokens, Quality: Excellent
# Best for: Long context, latest features
```

#### Anthropic Models
```bash
# Claude 3 Haiku
MODEL_SLUG=anthropic/claude-3-haiku
# Speed: Very fast, Cost: Low
# Context: 200k tokens, Quality: Good
# Best for: Fast responses, long documents

# Claude 3 Sonnet
MODEL_SLUG=anthropic/claude-3-sonnet
# Speed: Moderate, Cost: Moderate
# Context: 200k tokens, Quality: Very good
# Best for: Balanced performance

# Claude 3 Opus
MODEL_SLUG=anthropic/claude-3-opus
# Speed: Slow, Cost: High
# Context: 200k tokens, Quality: Excellent
# Best for: Complex tasks, highest quality
```

#### Open Source Models
```bash
# Llama 2 70B Chat
MODEL_SLUG=meta-llama/llama-2-70b-chat
# Speed: Moderate, Cost: Low
# Context: 4k tokens, Quality: Good
# Best for: Open source, privacy

# Mixtral 8x7B Instruct
MODEL_SLUG=mistralai/mixtral-8x7b-instruct
# Speed: Fast, Cost: Low
# Context: 32k tokens, Quality: Good
# Best for: Multilingual, long context

# Code Llama 34B Instruct
MODEL_SLUG=codellama/codellama-34b-instruct
# Speed: Moderate, Cost: Low
# Context: 16k tokens, Quality: Good
# Best for: Code generation and analysis
```

## Configuration Examples

### Development Environment
```bash
# .env.development
OPENROUTER_API_KEY=sk-or-your-dev-key
LOG_LEVEL=DEBUG
OTEL_CONSOLE_EXPORT=true
OTEL_ENVIRONMENT=development
MAX_DOCUMENT_LENGTH=10000
DEFAULT_SEARCH_LIMIT=3
USE_MOCK_LLM=true  # For testing without API calls
```

### Staging Environment
```bash
# .env.staging
OPENROUTER_API_KEY=sk-or-your-staging-key
LOG_LEVEL=INFO
CHROMADB_PATH=/var/lib/rag-system/staging/chroma_db
OTEL_ENVIRONMENT=staging
JAEGER_ENDPOINT=http://jaeger.staging.internal:14268/api/traces
REQUEST_TIMEOUT=45
```

### Production Environment
```bash
# .env.production
OPENROUTER_API_KEY=sk-or-your-prod-key
LOG_LEVEL=INFO
LOG_FILE=/var/log/rag-system/app.log
CHROMADB_PATH=/var/lib/rag-system/chroma_db
OTEL_ENVIRONMENT=production
OTEL_CONSOLE_EXPORT=false
JAEGER_ENDPOINT=http://jaeger.prod.internal:14268/api/traces
REQUEST_TIMEOUT=60
MAX_DOCUMENT_LENGTH=100000
MAX_SEARCH_RESULTS=50
```

### High-Performance Configuration
```bash
# .env.performance
EMBEDDING_MODEL=all-MiniLM-L6-v2  # Fastest model
MODEL_SLUG=openai/gpt-3.5-turbo   # Fastest LLM
DEFAULT_SEARCH_LIMIT=3            # Fewer results
MAX_CHAT_RESULTS=5                # Less context
REQUEST_TIMEOUT=30                # Shorter timeout
```

### High-Quality Configuration
```bash
# .env.quality
EMBEDDING_MODEL=all-mpnet-base-v2    # Best embeddings
MODEL_SLUG=openai/gpt-4              # Best LLM
DEFAULT_SEARCH_LIMIT=10              # More results
MAX_CHAT_RESULTS=10                  # More context
REQUEST_TIMEOUT=120                  # Longer timeout
```

## Configuration Validation

### Validation Script
```python
#!/usr/bin/env python3
# save as validate_config.py

import os
from app.config import config

def validate_config():
    """Validate current configuration."""
    issues = []

    # Check required settings
    if not config.is_api_key_configured():
        issues.append("OPENROUTER_API_KEY is not configured")

    # Check paths
    if not os.path.exists(os.path.dirname(config.chromadb_path)):
        issues.append(f"ChromaDB directory does not exist: {config.chromadb_path}")

    # Check numeric values
    if config.request_timeout <= 0:
        issues.append("REQUEST_TIMEOUT must be positive")

    if config.max_document_length <= 0:
        issues.append("MAX_DOCUMENT_LENGTH must be positive")

    # Print results
    if issues:
        print("Configuration issues found:")
        for issue in issues:
            print(f"  - {issue}")
        return False
    else:
        print("Configuration validation passed")
        return True

if __name__ == "__main__":
    import sys
    sys.exit(0 if validate_config() else 1)
```

### Health Check Configuration
```python
# Check configuration via API
curl -s http://localhost:8000/health | jq .

# Expected response structure:
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
    },
    "config": {
      "api_key_configured": true,
      "embedding_model": "all-MiniLM-L6-v2",
      "llm_model": "openai/gpt-3.5-turbo"
    }
  }
}
```

## Security Configuration

### Secure API Key Management
```bash
# Using Docker secrets
echo "sk-or-your-api-key" | docker secret create openrouter_api_key -

# Using Kubernetes secrets
kubectl create secret generic rag-secrets \
  --from-literal=openrouter-api-key=sk-or-your-api-key

# Using AWS Systems Manager
aws ssm put-parameter \
  --name "/rag-system/openrouter-api-key" \
  --value "sk-or-your-api-key" \
  --type "SecureString"
```

### Environment File Security
```bash
# Set proper permissions
chmod 600 .env
chown app-user:app-group .env

# Verify no secrets in git
git secrets --scan
grep -r "sk-or-" . --exclude-dir=.git || echo "No API keys found in code"
```

## Performance Tuning

### Memory Optimization
```bash
# Reduce memory usage
EMBEDDING_MODEL=all-MiniLM-L6-v2  # Smaller model
DEFAULT_SEARCH_LIMIT=3            # Fewer results
MAX_CHAT_RESULTS=5                # Less context
```

### Speed Optimization
```bash
# Optimize for speed
MODEL_SLUG=openai/gpt-3.5-turbo   # Fastest LLM
REQUEST_TIMEOUT=30                # Quick timeouts
DEFAULT_SEARCH_LIMIT=3            # Fewer database operations
```

### Quality Optimization
```bash
# Optimize for quality
EMBEDDING_MODEL=all-mpnet-base-v2  # Best embeddings
MODEL_SLUG=openai/gpt-4            # Best reasoning
DEFAULT_SEARCH_LIMIT=10            # More context
MAX_CHAT_RESULTS=10                # More sources
```

---

*This configuration reference covers all available options. Choose settings based on your specific requirements for performance, quality, and resource constraints.*
