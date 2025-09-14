"""
Pydantic models for API request/response validation.
"""

from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator


class DocumentRequest(BaseModel):
    """Request model for adding a document."""

    text: str = Field(..., description="Document text content")
    metadata: Optional[dict[str, Any]] = Field(
        default_factory=dict, description="Optional metadata for the document"
    )

    @field_validator("text")
    @classmethod
    def validate_text(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Text cannot be empty")
        return v.strip()


class SearchRequest(BaseModel):
    """Request model for document search."""

    query: str = Field(..., description="Search query")
    limit: int = Field(
        default=5, ge=1, le=20, description="Number of results to return"
    )

    @field_validator("query")
    @classmethod
    def validate_query(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Query cannot be empty")
        return v.strip()


class ChatRequest(BaseModel):
    """Request model for chat/question answering."""

    question: str = Field(..., description="Question to ask")
    max_results: int = Field(
        default=5, ge=1, le=10, description="Maximum number of context documents to use"
    )

    @field_validator("question")
    @classmethod
    def validate_question(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Question cannot be empty")
        return v.strip()


class DocumentResponse(BaseModel):
    """Response model for document operations."""

    success: bool = Field(description="Whether the operation was successful")
    id: Optional[str] = Field(None, description="Document ID if successful")
    message: str = Field(description="Response message")
    metadata: Optional[dict[str, Any]] = Field(None, description="Additional metadata")


class SearchResult(BaseModel):
    """Individual search result."""

    content: str = Field(description="Document content")
    score: float = Field(description="Similarity score")
    metadata: dict[str, Any] = Field(description="Document metadata")


class ChatResponse(BaseModel):
    """Response model for chat/question answering."""

    answer: str = Field(description="Generated answer")
    sources: list[SearchResult] = Field(description="Source documents used")
    model_used: str = Field(description="LLM model used for generation")
    tokens_used: int = Field(description="Number of tokens used")
    processing_time: float = Field(description="Processing time in seconds")
    context_documents_found: int = Field(
        description="Number of context documents found"
    )


class HealthResponse(BaseModel):
    """Response model for health check."""

    status: str = Field(description="Overall system status")
    timestamp: str = Field(description="Health check timestamp")
    components: dict[str, dict[str, Any]] = Field(
        description="Component status details"
    )
    version: str = Field(description="Application version")
    uptime: float = Field(description="System uptime in seconds")


class BulkAddRequest(BaseModel):
    """Request model for bulk document addition."""

    documents: list[dict[str, Any]] = Field(
        ..., description="List of documents with text, metadata fields"
    )
    allow_duplicates: bool = Field(
        default=False, description="Whether to allow duplicate documents"
    )
