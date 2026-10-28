import json
import logging

import chromadb

from src.config import settings
from .bm25 import bm25_scores
from .embeddings import get_embedding

logger = logging.getLogger(__name__)

_client: chromadb.ClientAPI | None = None


def _get_client() -> chromadb.ClientAPI:
    """Lazy-initialize and return the ChromaDB client singleton.

    If chroma_server_host is set in settings, uses HttpClient to connect to a standalone server.
    Otherwise, uses PersistentClient for local development.
    """
    global _client
    if _client is None:
        if settings.chroma_server_host:
            _client = chromadb.HttpClient(
                host=settings.chroma_server_host,
                port=settings.chroma_server_port,
            )
            logger.info(
                "ChromaDB Standalone HttpClient initialized connecting to %s:%d",
                settings.chroma_server_host,
                settings.chroma_server_port,
            )
        else:
            _client = chromadb.PersistentClient(
                path=settings.chroma_persist_directory,
            )
            logger.info(
                "ChromaDB PersistentClient initialized: %s",
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

    We explicitly generate the vector embedding using Gemini API
    and pass it manually to ChromaDB.
    """
    collection = _get_collection()
    doc_id = metadata.get("id", "")
    embedding = get_embedding(content)

    # ChromaDB stores metadata as flat key-value pairs.
    # We serialize the full metadata dict as a JSON string
    # to preserve nested structures.
    collection.upsert(
        ids=[doc_id],
        embeddings=[embedding],
        documents=[content],
        metadatas=[{"id": doc_id, "raw": json.dumps(metadata)}],
    )
    logger.info("Upserted document id=%s with Gemini embedding", doc_id)


def query_vector_db(query: str, n_results: int = 10) -> list[dict]:
    """Query the vector store and return matching documents.

    Returns a list of dicts with 'content' and 'metadata' keys.
    We explicitly generate the query embedding vector using Gemini API.
    """
    collection = _get_collection()
    embedding = get_embedding(query)

    results = collection.query(
        query_embeddings=[embedding],
        n_results=n_results,
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


def build_context(docs: list[dict]) -> dict:
    """Number chunks as sources [1], [2], ... so the answer can cite them.

    Returns the state update: the numbered context text and the matching source list.
    """
    parts: list[str] = []
    sources: list[dict] = []
    for n, doc in enumerate(docs, 1):
        meta = doc.get("metadata", {})
        source = {key: meta.get(key, "") for key in ("url", "author", "timestamp")}
        sources.append(source)
        byline = ", ".join(v for v in (source["author"], source["timestamp"]) if v)
        parts.append(f"[{n}] {byline}\n{doc['content']}" if byline else f"[{n}]\n{doc['content']}")
    return {"retrieved_context": "\n\n".join(parts), "sources": sources}


RRF_K = 60  # standard reciprocal rank fusion constant; damps the weight of top ranks


def search(query: str, n_results: int = 10) -> list[dict]:
    """Hybrid retrieval: fuse vector and BM25 keyword rankings with reciprocal rank fusion.

    Vector search finds paraphrases; BM25 finds exact names, numbers and slang that embeddings blur.
    """
    vector_hits = query_vector_db(query, n_results)

    # shortcut: BM25 rescans the whole collection per query; fine for a personal forum index,
    # build a persistent keyword index if it grows past roughly 100k chunks
    stored = _get_collection().get(include=["documents", "metadatas"])
    docs = [
        {"content": doc, "metadata": json.loads(meta.get("raw", "{}"))}
        for doc, meta in zip(stored["documents"], stored["metadatas"])
    ]
    scores = bm25_scores(query, [d["content"] for d in docs])
    keyword_hits = [d for score, d in sorted(zip(scores, docs), key=lambda p: -p[0]) if score > 0][:n_results]

    fused: dict[str, float] = {}
    by_key: dict[str, dict] = {}
    for hits in (vector_hits, keyword_hits):
        for rank, doc in enumerate(hits, 1):
            key = doc["metadata"].get("id") or doc["content"]
            fused[key] = fused.get(key, 0.0) + 1.0 / (RRF_K + rank)
            by_key.setdefault(key, doc)

    ranked = sorted(fused, key=fused.get, reverse=True)[:n_results]
    logger.info("Hybrid search: %d vector, %d keyword, %d fused", len(vector_hits), len(keyword_hits), len(ranked))
    return [by_key[key] for key in ranked]
