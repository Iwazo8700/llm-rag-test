from contextlib import asynccontextmanager
import logging
import time

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from app.models import (
    BulkAddRequest,
    ChatRequest,
    ChatResponse,
    DocumentRequest,
    SearchResult,
)

from .config import config
from .database import ChromaDBManager
from .embeddings import EmbeddingGenerator
from .rag import RAGPipeline
from .telemetry_simple import (
    TelemetryConfig,
    instrument_fastapi,
    metrics_collector,
    set_span_attribute,
    setup_telemetry,
    trace_function,
    traced_operation,
)

logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize telemetry early, before creating the FastAPI app
telemetry_config = TelemetryConfig()
setup_telemetry(telemetry_config)
logger.info("OpenTelemetry initialized")

db_manager: ChromaDBManager
embedding_generator: EmbeddingGenerator
rag_pipeline: RAGPipeline


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global db_manager, embedding_generator, rag_pipeline
    logger.info("Starting RAG application lifespan")

    try:
        # Initialize components
        db_manager = ChromaDBManager()
        embedding_generator = EmbeddingGenerator(config.EMBEDDING_MODEL)
        rag_pipeline = RAGPipeline(
            db_manager=db_manager,
            embedding_generator=embedding_generator,
            api_key=config.OPENROUTER_API_KEY,
            model_slug=config.MODEL_SLUG,
        )

        logger.info("RAG application started successfully")
        yield

    except Exception as e:
        logger.error(f"Failed to start RAG application: {e}")
        raise

    finally:
        # Cleanup
        logger.info("RAG application stopped")


@traced_operation("startup_initialization")
async def startup():
    """Initialize system components on startup."""
    global db_manager, embedding_generator, rag_pipeline

    try:
        logger.info("Initializing RAG system components...")

        set_span_attribute("stage", "ensure_directories")
        config.ensure_directories()

        set_span_attribute("stage", "initialize_database")
        set_span_attribute("db_path", str(config.CHROMADB_PATH))
        db_manager = ChromaDBManager(config.CHROMADB_PATH)

        set_span_attribute("stage", "initialize_embeddings")
        set_span_attribute("model", config.EMBEDDING_MODEL)
        embedding_generator = EmbeddingGenerator(config.EMBEDDING_MODEL)

        set_span_attribute("stage", "initialize_rag_pipeline")
        set_span_attribute("llm_model", config.MODEL_SLUG)
        rag_pipeline = RAGPipeline(
            db_manager,
            embedding_generator,
            config.OPENROUTER_API_KEY,
            config.MODEL_SLUG,
        )

        logger.info("RAG system initialized successfully")

        startup_counter = metrics_collector.get_counter(
            "rag_system_startups_total", "Total number of RAG system startups"
        )
        startup_counter.add(
            1,
            {
                "embedding_model": config.EMBEDDING_MODEL,
                "llm_model": config.MODEL_SLUG,
                "fallback_mode": str(embedding_generator.use_fallback),
            },
        )

    except Exception as e:
        logger.error(f"Failed to initialize RAG system: {e}")
        raise


# Create FastAPI app
app = FastAPI(
    title="LLM RAG API",
    description="An API for RAG (Retrieval-Augmented Generation) operations using ChromaDB and OpenAI",
    version="1.0.0",
    lifespan=lifespan,
)

# Instrument FastAPI app with OpenTelemetry
instrument_fastapi(app)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    """
    Root endpoint providing system information and health status.

    Returns:
        dict: System information including name, version, and component status
    """
    try:
        stats = db_manager.get_collection_stats()
        return {
            "name": config.APP_NAME,
            "version": config.APP_VERSION,
            "status": "healthy",
            "components": {
                "database": "ChromaDB",
                "embedding_model": embedding_generator.model_name,
                "llm_model": rag_pipeline.model_slug,
                "fallback_mode": embedding_generator.use_fallback,
                "api_key_configured": config.is_api_key_configured(),
            },
            "statistics": stats,
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "name": config.APP_NAME,
            "version": config.APP_VERSION,
            "status": "error",
            "error": str(e),
        }


@app.post("/add_document")
@trace_function("add_document_endpoint")
async def add_document(request: DocumentRequest):
    """
    Add a document to the vector database.

    This endpoint:
    1. Validates the input text
    2. Generates embeddings for the text
    3. Stores the document and embeddings in ChromaDB

    Args:
        request (AddDocumentRequest): Document text and optional metadata

    Returns:
        dict: Success status and document ID

    Raises:
        HTTPException: If document processing fails
    """
    request_counter = metrics_collector.get_counter(
        "rag_documents_added_total", "Total number of documents added"
    )

    document_size_histogram = metrics_collector.get_histogram(
        "rag_document_size_chars", "Size of documents in characters"
    )

    try:
        if not request.text or not request.text.strip():
            raise HTTPException(status_code=400, detail="Document text cannot be empty")

        if len(request.text) > config.MAX_DOCUMENT_LENGTH:
            raise HTTPException(
                status_code=400,
                detail=f"Document text too long (max {config.MAX_DOCUMENT_LENGTH:,} characters)",
            )

        document_size_histogram.record(len(request.text))

        set_span_attribute("stage", "generate_embedding")
        set_span_attribute("text_length", len(request.text))
        set_span_attribute("has_metadata", bool(request.metadata))
        embedding = embedding_generator.generate_embeddings([request.text])[0]

        set_span_attribute("stage", "store_document")
        set_span_attribute("embedding_dimension", len(embedding))
        doc_id = db_manager.add_document(
            text=request.text, embedding=embedding, metadata=request.metadata or {}
        )
        set_span_attribute("document_id", doc_id)

        request_counter.add(1, {"status": "success"})

        return {
            "success": True,
            "id": doc_id,
            "message": "Document added successfully",
            "metadata": {
                "text_length": len(request.text),
                "embedding_dimension": len(embedding),
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to add document: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to add document: {str(e)}"
        ) from e


@app.get("/search", response_model=list[SearchResult])
@trace_function("search_endpoint")
async def search(
    query: str = Query(..., description="Search query text"),
    limit: int = Query(
        default=5,
        ge=1,
        le=config.MAX_SEARCH_RESULTS,
        description=f"Maximum number of results (1-{config.MAX_SEARCH_RESULTS})",
    ),
):
    """
    Search for similar documents in the vector database.

    This endpoint:
    1. Validates the search query
    2. Generates embedding for the query
    3. Performs similarity search in ChromaDB
    4. Returns ranked results with similarity scores

    Args:
        query (str): Search query text
        limit (int): Maximum number of results (1-20)

    Returns:
        list[SearchResult]: List of matching documents with scores

    Raises:
        HTTPException: If search fails
    """
    search_counter = metrics_collector.get_counter(
        "rag_searches_total", "Total number of search requests"
    )

    search_latency = metrics_collector.get_histogram(
        "rag_search_duration_seconds", "Search request duration in seconds"
    )

    start_time = time.time()

    try:
        if not query or not query.strip():
            raise HTTPException(status_code=400, detail="Search query cannot be empty")

        set_span_attribute("stage", "generate_query_embedding")
        set_span_attribute("query_length", len(query))
        set_span_attribute("limit", limit)
        query_embedding = embedding_generator.generate_embeddings([query])[0]

        set_span_attribute("stage", "vector_search")
        set_span_attribute("embedding_dimension", len(query_embedding))
        results = db_manager.search(query_embedding, n_results=limit)
        set_span_attribute("results_found", len(results.get("documents", [])))

        search_results = []
        documents = results["documents"]
        distances = results["distances"]
        metadatas = results["metadatas"]

        for doc, distance, metadata in zip(documents, distances, metadatas):
            # ChromaDB returns squared euclidean distance, convert to similarity score
            # For normalized vectors, similarity = 1 - (distance / 2)
            # But since ChromaDB uses squared distance, we need: similarity = 1 - (distance / 2)
            similarity_score = max(0.0, 1.0 - (distance / 2.0))
            search_results.append(
                SearchResult(
                    content=doc,
                    score=round(similarity_score, 4),
                    metadata=metadata or {},
                )
            )

        duration = time.time() - start_time
        search_latency.record(duration)
        search_counter.add(
            1, {"status": "success", "result_count": str(len(search_results))}
        )

        return search_results

    except HTTPException:
        search_counter.add(1, {"status": "client_error"})
        raise
    except Exception as e:
        search_counter.add(1, {"status": "server_error"})
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}") from e


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Generate an answer using the RAG pipeline.

    This endpoint:
    1. Validates the question
    2. Retrieves relevant context using vector search
    3. Generates an answer using the LLM
    4. Returns the answer with sources and metadata

    Args:
        request (ChatRequest): Question and search parameters

    Returns:
        ChatResponse: Generated answer with sources and metadata

    Raises:
        HTTPException: If answer generation fails
    """
    try:
        if not request.question or not request.question.strip():
            raise HTTPException(status_code=400, detail="Question cannot be empty")

        if request.max_results < 1 or request.max_results > config.MAX_CHAT_RESULTS:
            raise HTTPException(
                status_code=400,
                detail=f"max_results must be between 1 and {config.MAX_CHAT_RESULTS}",
            )

        result = rag_pipeline.generate_answer(
            question=request.question, max_results=request.max_results
        )

        if result["answer"].startswith("Error:"):
            raise HTTPException(status_code=500, detail=result["answer"])

        return ChatResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat request failed: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to generate answer: {str(e)}"
        ) from e


@app.put("/documents/{doc_id}")
async def update_document(doc_id: str, request: DocumentRequest):
    """
    Update an existing document.

    Args:
        doc_id (str): Document ID to update
        request (AddDocumentRequest): New document content

    Returns:
        dict: Update status
    """
    try:
        embeddings = embedding_generator.generate_embeddings([request.text])

        success = db_manager.update_document(
            doc_id=doc_id,
            text=request.text,
            embedding=embeddings[0],
            metadata=request.metadata,
        )

        if not success:
            raise HTTPException(status_code=404, detail="Document not found")

        return {"message": "Document updated successfully", "document_id": doc_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update document {doc_id}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to update document: {str(e)}"
        ) from e


@app.delete("/documents/{doc_id}")
async def delete_document(doc_id: str):
    """
    Delete a document by ID.

    Args:
        doc_id (str): Document ID to delete

    Returns:
        dict: Deletion status
    """
    try:
        success = db_manager.delete_document(doc_id)

        if not success:
            raise HTTPException(status_code=404, detail="Document not found")

        return {"message": "Document deleted successfully", "document_id": doc_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete document {doc_id}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to delete document: {str(e)}"
        ) from e


@app.get("/documents/{doc_id}")
async def get_document(doc_id: str):
    """
    Retrieve a document by ID.

    Args:
        doc_id (str): Document ID to retrieve

    Returns:
        dict: Document data
    """
    try:
        document = db_manager.get_document(doc_id)

        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        return document

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get document {doc_id}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve document: {str(e)}"
        ) from e


@app.post("/documents/bulk")
async def bulk_add_documents(request: BulkAddRequest):
    """
    Add multiple documents in a single operation.

    Args:
        request (BulkAddRequest): Bulk document addition request

    Returns:
        dict: Bulk addition results
    """
    try:
        texts = [doc.get("text", "") for doc in request.documents]

        if not all(texts):
            raise HTTPException(
                status_code=400, detail="All documents must have 'text' field"
            )

        embeddings = embedding_generator.generate_embeddings(texts)

        docs_with_embeddings = []
        for i, doc in enumerate(request.documents):
            docs_with_embeddings.append(
                {
                    "text": doc["text"],
                    "embedding": embeddings[i],
                    "metadata": doc.get("metadata", {}),
                }
            )

        added_ids = db_manager.bulk_add_documents(
            documents=docs_with_embeddings, allow_duplicates=request.allow_duplicates
        )

        return {
            "message": "Bulk add completed",
            "documents_added": len(added_ids),
            "document_ids": added_ids,
            "total_requested": len(request.documents),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Bulk add failed: {e}")
        raise HTTPException(status_code=500, detail=f"Bulk add failed: {str(e)}") from e


@app.get("/health")
async def health_check():
    """
    Detailed health check endpoint.

    Returns:
        dict: Detailed system health information
    """
    try:
        health_status = {
            "status": "healthy",
            "timestamp": time.time(),
            "components": {},
        }

        try:
            stats = db_manager.get_collection_stats()
            health_status["components"]["database"] = {
                "status": "healthy",
                "document_count": stats["document_count"],
            }
        except Exception as e:
            health_status["components"]["database"] = {
                "status": "error",
                "error": str(e),
            }
            health_status["status"] = "degraded"

        try:
            test_embedding = embedding_generator.generate_embeddings(["test"])
            health_status["components"]["embeddings"] = {
                "status": "healthy",
                "fallback_mode": embedding_generator.use_fallback,
                "dimension": len(test_embedding[0]),
            }
        except Exception as e:
            health_status["components"]["embeddings"] = {
                "status": "error",
                "error": str(e),
            }
            health_status["status"] = "degraded"

        return health_status

    except Exception as e:
        return {"status": "error", "error": str(e), "timestamp": time.time()}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app, host=config.HOST, port=config.PORT, log_level=config.LOG_LEVEL.lower()
    )
