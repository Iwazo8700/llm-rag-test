#!/usr/bin/env python3
"""
Interactive CLI tool to explore your RAG database documents.
"""

import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import json

from app.database import ChromaDBManager


def print_header():
    """Print the application header."""
    print("🔍 RAG Database Explorer")
    print("=" * 50)
    print("Commands:")
    print("  all           - Show all documents")
    print("  search <query> - Search for documents")
    print("  stats         - Show database statistics")
    print("  help          - Show this help")
    print("  quit          - Exit")
    print("=" * 50)


def print_document(doc_id, content, metadata, index=None, score=None):
    """Print a document in a formatted way."""
    prefix = f"📄 Document {index}" if index else "📄 Document"
    print(f"\n{prefix}")
    print(f"   ID: {doc_id}")

    if score:
        print(f"   Score: {score:.4f}")

    if metadata:
        print(f"   Metadata: {json.dumps(metadata, indent=6)}")

    # Show preview
    preview = content[:150] + "..." if len(content) > 150 else content
    print(f"   Content: {preview}")
    print("-" * 50)


def show_all_documents(db):
    """Show all documents in the database."""
    try:
        collection = db.collection
        results = collection.get(include=["documents", "metadatas"])

        if not results["documents"]:
            print("❌ No documents found in the database.")
            return

        print(f"\n📚 Found {len(results['documents'])} documents:")

        for i, (doc_id, content, metadata) in enumerate(
            zip(results["ids"], results["documents"], results["metadatas"]), 1
        ):
            print_document(doc_id, content, metadata, index=i)

    except Exception as e:
        print(f"❌ Error: {e}")


def search_documents(db, query):
    """Search for documents using the RAG system."""
    try:
        from app.embeddings import EmbeddingGenerator

        # Initialize embedding generator
        embedding_gen = EmbeddingGenerator()

        # Generate query embedding
        query_embedding = embedding_gen.generate_embeddings([query])[0]

        # Search in database
        results = db.search_similar_documents(query_embedding, top_k=5)

        if not results:
            print(f"❌ No results found for '{query}'")
            return

        print(f"\n🔍 Found {len(results)} results for '{query}':")

        for i, result in enumerate(results, 1):
            print_document(
                result["id"],
                result["content"],
                result["metadata"],
                index=i,
                score=result["score"],
            )

    except Exception as e:
        print(f"❌ Search error: {e}")


def show_stats(db):
    """Show database statistics."""
    try:
        stats = db.get_collection_stats()
        print("\n📊 Database Statistics:")
        print(f"   Collection: {stats['collection_name']}")
        print(f"   Documents: {stats['document_count']}")
        print("   Database path: ./chroma_db")

    except Exception as e:
        print(f"❌ Stats error: {e}")


def main():
    """Main interactive loop."""
    print_header()

    try:
        db = ChromaDBManager()
        print("✅ Connected to database successfully!")

        while True:
            try:
                command = input("\n🔍 Enter command: ").strip().lower()

                if command == "quit" or command == "exit":
                    print("👋 Goodbye!")
                    break
                elif command == "help":
                    print_header()
                elif command == "all":
                    show_all_documents(db)
                elif command == "stats":
                    show_stats(db)
                elif command.startswith("search "):
                    query = command[7:].strip()
                    if query:
                        search_documents(db, query)
                    else:
                        print(
                            "❌ Please provide a search query. Example: search Python"
                        )
                elif command == "":
                    continue
                else:
                    print("❌ Unknown command. Type 'help' for available commands.")

            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")

    except Exception as e:
        print(f"❌ Failed to connect to database: {e}")


if __name__ == "__main__":
    main()
