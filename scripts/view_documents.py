#!/usr/bin/env python3
"""
Script to view all documents stored in the ChromaDB database.
"""

from datetime import datetime, timezone
from pathlib import Path
import sys

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from app.database import ChromaDBManager


def view_all_documents():
    """View all documents in the database with detailed information."""
    try:
        # Initialize database manager
        db = ChromaDBManager()

        # Get collection stats
        stats = db.get_collection_stats()
        print("📊 Database Statistics:")
        print(f"   Total documents: {stats['document_count']}")
        print(f"   Collection name: {stats['collection_name']}")
        print("=" * 80)

        if stats["document_count"] == 0:
            print("No documents found in the database.")
            return

        # Get all documents (using a dummy embedding)
        dummy_embedding = [0.1] * 384  # Standard embedding dimension
        results = db.search(query_embedding=dummy_embedding, n_results=50)

        print(f"\n📚 All Documents ({len(results['documents'])} found):")
        print("=" * 80)

        for i, (doc_id, text, metadata, distance) in enumerate(
            zip(
                results["ids"],
                results["documents"],
                results["metadatas"],
                results["distances"],
            ),
            1,
        ):
            print(f"\n{i}. Document ID: {doc_id}")

            # Display text (truncate if too long)
            if len(text) > 300:
                print(f"   📄 Text: {text[:300]}...")
                print(f"      [Full length: {len(text)} characters]")
            else:
                print(f"   📄 Text: {text}")

            # Display metadata
            if metadata:
                print("   📝 Metadata:")
                for key, value in metadata.items():
                    if key == "timestamp":
                        # Convert timestamp to readable format
                        dt = datetime.fromtimestamp(value, tz=timezone.utc)
                        print(f"      - {key}: {dt.strftime('%Y-%m-%d %H:%M:%S')}")
                    else:
                        print(f"      - {key}: {value}")

            print(f"   🔍 Search Distance: {distance:.4f}")
            print("-" * 80)

    except Exception as e:
        print(f"❌ Error accessing database: {e}")
        import traceback

        traceback.print_exc()


def search_documents(query_text: str, limit: int = 5):
    """Search for documents containing specific text."""
    try:
        from app.embeddings import EmbeddingGenerator

        # Initialize components
        db = ChromaDBManager()
        embedder = EmbeddingGenerator()

        # Generate embedding for the query
        query_embedding = embedder.generate_embeddings([query_text])[0]

        # Search for similar documents
        results = db.search(query_embedding=query_embedding, n_results=limit)

        print(f"\n🔍 Search Results for: '{query_text}'")
        print("=" * 80)

        if not results["documents"]:
            print("No matching documents found.")
            return

        for i, (doc_id, text, metadata, distance) in enumerate(
            zip(
                results["ids"],
                results["documents"],
                results["metadatas"],
                results["distances"],
            ),
            1,
        ):
            print(
                f"\n{i}. Similarity Score: {1 - distance:.4f} (Distance: {distance:.4f})"
            )
            print(f"   Document ID: {doc_id}")

            if len(text) > 200:
                print(f"   📄 Text: {text[:200]}...")
            else:
                print(f"   📄 Text: {text}")

            if metadata:
                print(
                    f"   📝 Added: {datetime.fromtimestamp(metadata.get('timestamp', 0), tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}"
                )

            print("-" * 40)

    except Exception as e:
        print(f"❌ Search error: {e}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="View documents in the RAG database")
    parser.add_argument(
        "--search", "-s", type=str, help="Search for documents containing this text"
    )
    parser.add_argument(
        "--limit", "-l", type=int, default=5, help="Limit number of search results"
    )

    args = parser.parse_args()

    if args.search:
        search_documents(args.search, args.limit)
    else:
        view_all_documents()
