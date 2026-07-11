import json
import logging

import chromadb

from src.config import settings

logger = logging.getLogger(__name__)

_client: chromadb.ClientAPI | None = None


def _get_client() -> chromadb.ClientAPI:
    """Lazy-initialize and return the ChromaDB client singleton.

    Uses PersistentClient for local development - data survives
    between process restarts. The persist directory is configurable
    via CHROMA_PERSIST_DIRECTORY env var.
    """
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(
            path=settings.chroma_persist_directory,
        )
        logger.info(
            "ChromaDB client initialized: %s",
            settings.chroma_persist_directory,
        )
    return _client


def _get_collection() -> chromadb.Collection:
    """Get or create the forum documents collection.

    ChromaDB's get_or_create_collection is idempotent - safe to call
    multiple times. It returns the existing collection or creates a new one.
    """
    client = _get_client()
    return client.get_or_create_collection(
        name=settings.chroma_collection_name,
    )


def reset_collection() -> None:
    """Drop and recreate the collection. Used for testing and --reset-db."""
    client = _get_client()
    collection_name = settings.chroma_collection_name
    try:
        client.delete_collection(collection_name)
        logger.info("Dropped collection: %s", collection_name)
    except Exception:
        # Collection doesn't exist yet - that's fine
        pass
    client.create_collection(name=collection_name)
    logger.info("Recreated collection: %s", collection_name)


def upsert_document(content: str, metadata: dict) -> None:
    """Insert or update a document in the vector store.

    ChromaDB's upsert is keyed by the document ID. If a document
    with the same ID already exists, it gets updated (both the
    document text and metadata are replaced).

    ChromaDB handles embedding automatically using its default
    embedding function. Phase 3 can swap this for Gemini embeddings.
    """
    collection = _get_collection()
    doc_id = metadata.get("id", "")

    # ChromaDB stores metadata as flat key-value pairs.
    # We serialize the full metadata dict as a JSON string
    # to preserve nested structures.
    collection.upsert(
        ids=[doc_id],
        documents=[content],
        metadatas=[{"id": doc_id, "raw": json.dumps(metadata)}],
    )
    logger.info("Upserted document id=%s", doc_id)


def query_vector_db(query: str) -> list[dict]:
    """Query the vector store and return matching documents.

    Returns a list of dicts with 'content' and 'metadata' keys.
    ChromaDB uses its default embedding function to embed the query
    text and find similar documents.
    """
    collection = _get_collection()

    results = collection.query(
        query_texts=[query],
        n_results=10,
    )

    documents = []
    if results["documents"] and results["metadatas"]:
        for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
            # Deserialize the raw metadata back to a dict
            raw_meta = json.loads(meta.get("raw", "{}"))
            documents.append(
                {
                    "content": doc,
                    "metadata": raw_meta,
                }
            )

    logger.info("Vector query returned %d results", len(documents))
    return documents
