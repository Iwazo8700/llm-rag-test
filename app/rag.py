import logging
import time
from typing import Any

import requests

from .config import config
from .telemetry_simple import (
    metrics_collector,
    set_span_attribute,
    traced_operation,
)

logger = logging.getLogger(__name__)


class RAGPipeline:
    """
    Implements the Retrieval-Augmented Generation pipeline.

    This class orchestrates the RAG workflow: retrieval of relevant context
    from the vector database and generation of answers using an LLM.
    """

    @traced_operation("rag_init", component="rag")
    def __init__(
        self,
        db_manager,
        embedding_generator,
        api_key: str,
        model_slug: str = "openai/gpt-3.5-turbo",
    ):
        """
        Initialize the RAG pipeline with required components.

        Args:
            db_manager: ChromaDB manager instance
            embedding_generator: Embedding generator instance
            api_key (str): OpenRouter API key
            model_slug (str): Model identifier for OpenRouter
        """
        set_span_attribute("model_slug", model_slug)

        self.db_manager = db_manager
        self.embedding_generator = embedding_generator
        self.model_slug = model_slug
        self.api_key = api_key

        self.api_url = config.OPENROUTER_API_URL
        self.http_referer = config.OPENROUTER_HTTP_REFERER
        self.app_title = config.OPENROUTER_APP_TITLE
        self.request_timeout = config.REQUEST_TIMEOUT

        has_valid_api_key = config.is_api_key_configured()
        set_span_attribute("has_valid_api_key", has_valid_api_key)

        if not has_valid_api_key:
            logger.warning(
                "No valid OpenRouter API key provided - answers will be simulated"
            )
            self.use_mock_llm = True
        else:
            self.use_mock_llm = False
            logger.info("OpenRouter API key configured")

        set_span_attribute("use_mock_llm", self.use_mock_llm)

        logger.info(f"RAG Pipeline initialized with model: {model_slug}")

        counter = metrics_collector.get_counter(
            "rag_pipelines_created", "RAG pipeline instances created"
        )
        counter.add(1, {"model_slug": model_slug, "mock_mode": str(self.use_mock_llm)})

    @traced_operation("rag_generate_answer", component="rag")
    def generate_answer(self, question: str, max_results: int = 3) -> dict[str, Any]:
        """
        Generate an answer using the RAG pipeline.

        This method performs the complete RAG workflow:
        1. Generate embedding for the question
        2. Retrieve relevant documents from vector database
        3. Construct context-aware prompt
        4. Generate answer using LLM
        5. Return answer with sources and metadata

        Args:
            question (str): User's question
            max_results (int): Maximum number of context documents to retrieve

        Returns:
            dict[str, Any]: Answer with sources and metadata
        """
        start_time = time.time()

        set_span_attribute("question_length", len(question))
        set_span_attribute("max_results", max_results)
        set_span_attribute("mock_mode", self.use_mock_llm)
        set_span_attribute("model_slug", self.model_slug)

        try:
            if not question or not question.strip():
                set_span_attribute("validation_error", "empty_question")
                return self._create_error_response("Question cannot be empty")

            set_span_attribute("question_preview", question[:100])

            set_span_attribute("pipeline_stage", "generating_embedding")

            query_embedding = self.embedding_generator.generate_embeddings([question])[
                0
            ]

            set_span_attribute("embedding_dimension", len(query_embedding))
            set_span_attribute("pipeline_stage", "retrieving_documents")

            search_results = self.db_manager.search(
                query_embedding=query_embedding, n_results=max_results
            )

            context_docs = search_results["documents"]
            sources = search_results["metadatas"]
            distances = search_results["distances"]

            set_span_attribute("documents_retrieved", len(context_docs))
            set_span_attribute(
                "avg_distance", sum(distances) / len(distances) if distances else 0
            )

            set_span_attribute("pipeline_stage", "generating_answer")

            if self.use_mock_llm:
                set_span_attribute("generation_method", "mock")
                answer = self._generate_mock_answer(question, context_docs)
                tokens_used = 0
            else:
                set_span_attribute("generation_method", "openrouter_api")
                answer, tokens_used = self._call_openrouter_api(question, context_docs)

            set_span_attribute("tokens_used", tokens_used)
            set_span_attribute("answer_length", len(answer))

            processing_time = round(time.time() - start_time, 2)
            response = {
                "answer": answer,
                "sources": self._format_sources(context_docs, sources, distances),
                "model_used": self.model_slug,
                "tokens_used": tokens_used,
                "processing_time": processing_time,
                "context_documents_found": len(context_docs),
            }

            set_span_attribute("processing_time", processing_time)
            set_span_attribute("pipeline_success", True)

            counter = metrics_collector.get_counter(
                "rag_questions_answered", "Questions answered by RAG pipeline"
            )
            counter.add(
                1,
                {
                    "status": "success",
                    "mock_mode": str(self.use_mock_llm),
                    "model": self.model_slug,
                },
            )

            histogram = metrics_collector.get_histogram(
                "rag_processing_time", "RAG pipeline processing time"
            )
            histogram.record(
                response["processing_time"], {"mock_mode": str(self.use_mock_llm)}
            )

            context_histogram = metrics_collector.get_histogram(
                "rag_context_documents", "Number of context documents retrieved"
            )
            context_histogram.record(
                len(context_docs), {"max_results": str(max_results)}
            )

            return response

        except Exception as e:
            logger.error(f"RAG pipeline failed: {e}")

            set_span_attribute("pipeline_success", False)
            set_span_attribute("error_type", type(e).__name__)
            set_span_attribute("error_message", str(e))

            counter = metrics_collector.get_counter(
                "rag_questions_answered", "Questions answered by RAG pipeline"
            )
            counter.add(
                1,
                {
                    "status": "error",
                    "mock_mode": str(self.use_mock_llm),
                    "model": self.model_slug,
                },
            )

            return self._create_error_response(f"Failed to generate answer: {str(e)}")

    @traced_operation("rag_openrouter_api_call", component="rag")
    def _call_openrouter_api(
        self, question: str, context_docs: list[str]
    ) -> tuple[str, int]:
        """
        Call OpenRouter API to generate an answer.

        Args:
            question (str): User's question
            context_docs (list[str]): Retrieved context documents

        Returns:
            tuple[str, int]: Generated answer and token usage
        """
        set_span_attribute("model", self.model_slug)
        set_span_attribute("context_docs_count", len(context_docs))
        set_span_attribute("question_length", len(question))

        if context_docs:
            context_str = "\n---\n".join(context_docs)
            prompt = f"""Based on the following context, answer the question. If the context doesn't contain enough information, say so clearly.

Context:
{context_str}

Question: {question}

Please provide a helpful answer based on the context above. If you reference specific information, mention which part of the context it comes from."""
            set_span_attribute("has_context", True)
            set_span_attribute("context_length", len(context_str))
        else:
            prompt = f"""Question: {question}

I don't have any specific context documents to reference. Please provide a general answer based on your knowledge, but mention that this is without specific context."""
            set_span_attribute("has_context", False)

        set_span_attribute("prompt_length", len(prompt))

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": self.http_referer,
            "X-Title": self.app_title,
        }

        payload = {
            "model": self.model_slug,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a helpful assistant that answers questions based on provided context. Always be honest about the limitations of the information available.",
                },
                {"role": "user", "content": prompt},
            ],
            "max_tokens": 500,
            "temperature": 0.1,
        }

        set_span_attribute("max_tokens", 500)
        set_span_attribute("temperature", 0.1)

        try:
            set_span_attribute("api_call_stage", "sending_request")
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=self.request_timeout,
            )
            response.raise_for_status()

            set_span_attribute("api_call_stage", "parsing_response")
            set_span_attribute("response_status_code", response.status_code)

            data = response.json()
            answer = data["choices"][0]["message"]["content"]
            tokens_used = data.get("usage", {}).get("total_tokens", 0)

            set_span_attribute("api_call_success", True)
            set_span_attribute("answer_length", len(answer))
            set_span_attribute("tokens_used", tokens_used)

            counter = metrics_collector.get_counter(
                "openrouter_api_calls", "OpenRouter API calls"
            )
            counter.add(1, {"status": "success", "model": self.model_slug})

            token_histogram = metrics_collector.get_histogram(
                "openrouter_tokens_used", "Tokens used by OpenRouter API"
            )
            token_histogram.record(tokens_used, {"model": self.model_slug})

            return answer, tokens_used

        except requests.RequestException as e:
            logger.error(f"OpenRouter API call failed: {e}")

            set_span_attribute("api_call_success", False)
            set_span_attribute("error_type", "request_exception")
            set_span_attribute("error_message", str(e))

            counter = metrics_collector.get_counter(
                "openrouter_api_calls", "OpenRouter API calls"
            )
            counter.add(
                1,
                {
                    "status": "error",
                    "model": self.model_slug,
                    "error_type": "request",
                },
            )

            return f"API Error: {str(e)}", 0

        except KeyError as e:
            logger.error(f"Unexpected API response format: {e}")

            set_span_attribute("api_call_success", False)
            set_span_attribute("error_type", "key_error")
            set_span_attribute("error_message", str(e))

            counter = metrics_collector.get_counter(
                "openrouter_api_calls", "OpenRouter API calls"
            )
            counter.add(
                1,
                {
                    "status": "error",
                    "model": self.model_slug,
                    "error_type": "format",
                },
            )

            return "Error: Unexpected response format from API", 0

    def _generate_mock_answer(self, question: str, context_docs: list[str]) -> str:
        """
        Generate a mock answer when no API key is available.

        Args:
            question (str): User's question
            context_docs (list[str]): Retrieved context documents

        Returns:
            str: Mock answer
        """
        if context_docs:
            return f"""Based on the retrieved context, I found {len(context_docs)} relevant document(s) related to your question: "{question[:100]}..."

Context summary: The documents contain information that appears relevant to your query.

Note: This is a simulated response because no OpenRouter API key was provided. In a real deployment, this would contain an AI-generated answer based on the context documents."""

        return f"""I couldn't find any relevant documents in the database for your question: "{question[:100]}..."

Note: This is a simulated response because no OpenRouter API key was provided. In a real deployment, this would contain an AI-generated answer."""

    def _format_sources(
        self, documents: list[str], metadatas: list[dict], distances: list[float]
    ) -> list[dict[str, Any]]:
        """
        Format source information for the response.

        Args:
            documents (list[str]): Document content
            metadatas (list[dict]): Document metadata
            distances (list[float]): Similarity distances

        Returns:
            list[dict[str, Any]]: Formatted source information
        """
        sources = []
        for _, (content, metadata, distance) in enumerate(
            zip(documents, metadatas, distances)
        ):
            similarity_score = max(0.0, 1.0 - (distance / 2.0))
            source = {
                "content": content,
                "score": round(similarity_score, 3),
                "metadata": metadata,
            }
            sources.append(source)

        return sources

    def _create_error_response(self, error_message: str) -> dict[str, Any]:
        """Create a standardized error response."""
        return {
            "answer": f"Error: {error_message}",
            "sources": [],
            "model_used": self.model_slug,
            "tokens_used": 0,
            "processing_time": 0,
            "context_documents_found": 0,
        }
