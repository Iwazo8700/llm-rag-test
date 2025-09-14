import hashlib
import logging
import time
from typing import Any, Optional

import chromadb

from .telemetry_simple import (
    metrics_collector,
    set_span_attribute,
    trace_function,
    traced_operation,
)

# Configure logging
logger = logging.getLogger(__name__)

MAX_SEARCH_DOCUMENTS = 50


class ChromaDBManager:
    """
    Manages ChromaDB vector storage and retrieval operations.

    This class provides a clean interface for storing document embeddings
    and performing similarity searches using ChromaDB as the backend.
    """

    @trace_function("chromadb_init")
    def __init__(self, collection_name: str = "documents"):
        """
        Initialize ChromaDB client and collection.

        Args:
            collection_name: Name of the ChromaDB collection
        """
        try:
            self.client = chromadb.PersistentClient(path="./chroma_db")

            self.collection = self.client.get_or_create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"},  # Use cosine similarity
            )

            logger.info(f"ChromaDB initialized with collection: {collection_name}")

            counter = metrics_collector.get_counter(
                "chromadb_connections", "ChromaDB connection attempts"
            )
            counter.add(1, {"status": "success", "collection": collection_name})

        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")

            counter = metrics_collector.get_counter(
                "chromadb_connections", "ChromaDB connection attempts"
            )
            counter.add(1, {"status": "error"})
            raise

    def _generate_document_id(self, text: str, metadata: dict | None = None) -> str:
        """
        Generate a deterministic document ID based on content.

        This prevents duplicate documents and allows for content-based deduplication.

        Args:
            text (str): The document text content
            metadata (dict): Optional metadata for the document

        Returns:
            str: A deterministic document ID
        """
        if metadata is None:
            metadata = {}
        content = f"{text}:{hash(str(metadata))}"

    def _document_exists(self, doc_id: str) -> bool:
        """
        Check if a document with the given ID already exists.

        Args:
            doc_id (str): Document ID to check

        Returns:
            bool: True if document exists, False otherwise
        """
        try:
            result = self.collection.get(ids=[doc_id])
            return len(result.get("ids", [])) > 0
        except Exception:
            return False

    @traced_operation("chromadb_add_document", component="database")
    def add_document(
        self,
        text: str,
        embedding: list[float],
        metadata: dict | None = None,
        allow_duplicates: bool = False,
    ) -> str:
        """
        Add a document and its embedding to the ChromaDB collection.

        Args:
            text (str): The document text content
            embedding (list[float]): The document embedding vector
            metadata (dict): Additional metadata for the document
            allow_duplicates (bool): If False, prevents adding duplicate content

        Returns:
            str: Unique document ID

        Raises:
            RuntimeError: If document storage fails
            ValueError: If duplicate document exists and allow_duplicates is False
        """
        if metadata is None:
            metadata = {}

        doc_id = self._generate_document_id(text, metadata)

        if not allow_duplicates and self._document_exists(doc_id):
            counter = metrics_collector.get_counter(
                "chromadb_documents_added", "Documents added to ChromaDB"
            )
            counter.add(1, {"status": "duplicate_skipped"})
            return doc_id

        set_span_attribute("doc_id", doc_id)
        set_span_attribute("text_length", len(text))
        set_span_attribute("embedding_dimension", len(embedding))
        set_span_attribute("allow_duplicates", allow_duplicates)

        try:
            metadata.update({"timestamp": time.time(), "text_length": len(text)})

            self.collection.add(
                ids=[doc_id],
                documents=[text],
                embeddings=[embedding],
                metadatas=[metadata],
            )

            counter = metrics_collector.get_counter(
                "chromadb_documents_added", "Documents added to ChromaDB"
            )
            counter.add(1, {"status": "success"})
            return doc_id

        except Exception as e:
            logger.error(f"Failed to add document: {e}")

            counter = metrics_collector.get_counter(
                "chromadb_documents_added", "Documents added to ChromaDB"
            )
            counter.add(1, {"status": "error"})
            raise RuntimeError(f"Document storage failed: {e}") from e

    @traced_operation("chromadb_search", component="database")
    def search(
        self, query_embedding: list[float], n_results: int = 5
    ) -> dict[str, Any]:
        """
        Search for similar documents using query embedding.

        Args:
            query_embedding (list[float]): The query embedding vector
            n_results (int): Maximum number of results to return

        Returns:
            dict[str, Any]: Search results containing documents, distances, metadata, and IDs

        Raises:
            RuntimeError: If search operation fails
        """
        n_results = max(1, min(n_results, MAX_SEARCH_DOCUMENTS))

        set_span_attribute("embedding_dimension", len(query_embedding))
        set_span_attribute("n_results", n_results)

        try:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                include=["documents", "distances", "metadatas"],
            )

            documents = results.get("documents", [[]])
            distances = results.get("distances", [[]])
            metadatas = results.get("metadatas", [[]])
            ids = results.get("ids", [[]])

            search_results = {
                "documents": documents[0] if documents and documents[0] else [],
                "distances": distances[0] if distances and distances[0] else [],
                "metadatas": metadatas[0] if metadatas and metadatas[0] else [],
                "ids": ids[0] if ids and ids[0] else [],
            }

            set_span_attribute("results_found", len(search_results["documents"]))

            counter = metrics_collector.get_counter(
                "chromadb_searches", "ChromaDB search operations"
            )
            counter.add(
                1,
                {
                    "status": "success",
                    "results_count": str(len(search_results["documents"])),
                },
            )
            return search_results

        except Exception as e:
            logger.error(f"Search operation failed: {e}")

            counter = metrics_collector.get_counter(
                "chromadb_searches", "ChromaDB search operations"
            )
            counter.add(1, {"status": "error"})
            raise RuntimeError(f"Search failed: {e}") from e

    @traced_operation("chromadb_get_stats", component="database")
    def get_collection_stats(self) -> dict[str, Any]:
        """
        Get statistics about the current collection.

        Returns:
            dict[str, Any]: Collection statistics
        """
        try:
            count = self.collection.count()
            stats = {
                "document_count": count,
                "collection_name": self.collection.name,
            }

            set_span_attribute("document_count", count)
            set_span_attribute("collection_name", self.collection.name)

            counter = metrics_collector.get_counter(
                "chromadb_stats_requests", "ChromaDB stats requests"
            )
            counter.add(1, {"status": "success"})
            return stats

        except Exception as e:
            logger.error(f"Failed to get collection stats: {e}")

            counter = metrics_collector.get_counter(
                "chromadb_stats_requests", "ChromaDB stats requests"
            )
            counter.add(1, {"status": "error"})
            return {"document_count": 0, "collection_name": "unknown"}

    @traced_operation("chromadb_update_document", component="database")
    def update_document(
        self,
        doc_id: str,
        text: Optional[str] = None,
        embedding: Optional[list[float]] = None,
        metadata: Optional[dict] = None,
    ) -> bool:
        """
        Update an existing document in the collection.

        Args:
            doc_id (str): Document ID to update
            text (str): New text content (optional)
            embedding (list[float]): New embedding vector (optional)
            metadata (dict): New metadata (optional)

        Returns:
            bool: True if update was successful, False otherwise
        """
        set_span_attribute("doc_id", doc_id)
        set_span_attribute("has_text", text is not None)
        set_span_attribute("has_embedding", embedding is not None)
        set_span_attribute("has_metadata", metadata is not None)

        try:
            if not self._document_exists(doc_id):
                logger.warning(f"Document {doc_id} does not exist for update")
                set_span_attribute("document_found", False)
                return False

            set_span_attribute("document_found", True)

            update_params = {}
            if text is not None:
                update_params["documents"] = [text]
                set_span_attribute("text_length", len(text))
            if embedding is not None:
                update_params["embeddings"] = [embedding]
                set_span_attribute("embedding_dimension", len(embedding))
            if metadata is not None:
                metadata["timestamp"] = time.time()
                if text:
                    metadata["text_length"] = len(text)
                update_params["metadatas"] = [metadata]

            self.collection.update(ids=[doc_id], **update_params)

            counter = metrics_collector.get_counter(
                "chromadb_documents_updated", "Documents updated in ChromaDB"
            )
            counter.add(1, {"status": "success"})
            return True

        except Exception as e:
            logger.error(f"Failed to update document {doc_id}: {e}")
            counter = metrics_collector.get_counter(
                "chromadb_documents_updated", "Documents updated in ChromaDB"
            )
            counter.add(1, {"status": "error"})
            return False

    @traced_operation("chromadb_delete_document", component="database")
    def delete_document(self, doc_id: str) -> bool:
        """
        Delete a document from the collection.

        Args:
            doc_id (str): Document ID to delete

        Returns:
            bool: True if deletion was successful, False otherwise
        """
        set_span_attribute("doc_id", doc_id)

        try:
            if not self._document_exists(doc_id):
                logger.warning(f"Document {doc_id} does not exist for deletion")
                set_span_attribute("document_found", False)
                return False

            set_span_attribute("document_found", True)
            self.collection.delete(ids=[doc_id])

            counter = metrics_collector.get_counter(
                "chromadb_documents_deleted", "Documents deleted from ChromaDB"
            )
            counter.add(1, {"status": "success"})
            return True

        except Exception as e:
            logger.error(f"Failed to delete document {doc_id}: {e}")
            counter = metrics_collector.get_counter(
                "chromadb_documents_deleted", "Documents deleted from ChromaDB"
            )
            counter.add(1, {"status": "error"})
            return False

    @traced_operation("chromadb_get_document", component="database")
    def get_document(self, doc_id: str) -> Optional[dict[str, Any]]:
        """
        Retrieve a specific document by ID.

        Args:
            doc_id (str): Document ID to retrieve

        Returns:
            Optional[dict]: Document data if found, None otherwise
        """
        set_span_attribute("doc_id", doc_id)

        try:
            result = self.collection.get(
                ids=[doc_id], include=["documents", "metadatas", "embeddings"]
            )

            if not result.get("ids"):
                set_span_attribute("document_found", False)
                return None

            set_span_attribute("document_found", True)

            doc_data = {
                "id": result["ids"][0],
                "document": None,
                "metadata": None,
                "embedding": None,
            }

            documents = result.get("documents")
            if documents:
                doc_data["document"] = documents[0]
                set_span_attribute("has_document_text", True)

            metadatas = result.get("metadatas")
            if metadatas:
                doc_data["metadata"] = metadatas[0]
                set_span_attribute("has_metadata", True)

            embeddings = result.get("embeddings")
            if embeddings:
                doc_data["embedding"] = embeddings[0]
                set_span_attribute("has_embedding", True)

            return doc_data

        except Exception as e:
            logger.error(f"Failed to get document {doc_id}: {e}")
            return None

    @traced_operation("chromadb_bulk_add", component="database")
    def bulk_add_documents(
        self, documents: list[dict[str, Any]], allow_duplicates: bool = False
    ) -> list[str]:
        """
        Add multiple documents in a single operation for better performance.

        Args:
            documents (list[dict]): list of document dicts with 'text', 'embedding', 'metadata'
            allow_duplicates (bool): If False, skips documents that already exist

        Returns:
            list[str]: list of document IDs that were added
        """
        set_span_attribute("document_count", len(documents))
        set_span_attribute("allow_duplicates", allow_duplicates)

        added_ids = []
        skipped_count = 0

        try:
            ids_to_add = []
            texts_to_add = []
            embeddings_to_add = []
            metadatas_to_add = []

            for doc in documents:
                text = doc["text"]
                embedding = doc["embedding"]
                metadata = doc.get("metadata", {})

                doc_id = self._generate_document_id(text, metadata)

                if not allow_duplicates and self._document_exists(doc_id):
                    skipped_count += 1
                    continue

                metadata.update({"timestamp": time.time(), "text_length": len(text)})

                ids_to_add.append(doc_id)
                texts_to_add.append(text)
                embeddings_to_add.append(embedding)
                metadatas_to_add.append(metadata)
                added_ids.append(doc_id)

            set_span_attribute("documents_added", len(added_ids))
            set_span_attribute("documents_skipped", skipped_count)

            if ids_to_add:
                self.collection.add(
                    ids=ids_to_add,
                    documents=texts_to_add,
                    embeddings=embeddings_to_add,
                    metadatas=metadatas_to_add,
                )

            counter = metrics_collector.get_counter(
                "chromadb_bulk_operations", "Bulk operations on ChromaDB"
            )
            counter.add(
                1,
                {
                    "operation": "bulk_add",
                    "documents_added": str(len(added_ids)),
                    "documents_skipped": str(skipped_count),
                },
            )

            return added_ids

        except Exception as e:
            logger.error(f"Bulk add failed: {e}")
            counter = metrics_collector.get_counter(
                "chromadb_bulk_operations", "Bulk operations on ChromaDB"
            )
            counter.add(1, {"operation": "bulk_add", "status": "error"})
            raise RuntimeError(f"Bulk add failed: {e}") from e
