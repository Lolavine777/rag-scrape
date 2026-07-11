import pytest
from src.rag.chunker import chunk_document

def test_chunk_document_splits_and_preserves_metadata():
    # Long text exceeding chunk_size
    text = (
        "Python 3.12 is here. It brings many new features.\n\n"
        "One of the major improvements is in the performance department, which sees 5-10% speedup.\n\n"
        "Another key update is the addition of structured type parameters for classes and functions."
    )
    metadata = {"url": "https://voz.vn/t/123", "id": "thread-123"}
    
    # Use small chunk_size to force splitting
    chunks = chunk_document(text, metadata, chunk_size=50, chunk_overlap=10)
    
    assert len(chunks) > 1
    # Check that metadata fields are preserved
    for i, chunk in enumerate(chunks):
        assert chunk["metadata"]["url"] == "https://voz.vn/t/123"
        assert chunk["metadata"]["id"] == f"thread-123-chunk-{i}"
        assert chunk["metadata"]["chunk_index"] == i
        assert len(chunk["content"]) > 0

def test_chunk_document_no_split_for_short_text():
    text = "Short text."
    metadata = {"url": "https://voz.vn/t/123", "id": "thread-123"}
    
    chunks = chunk_document(text, metadata, chunk_size=500, chunk_overlap=50)
    
    assert len(chunks) == 1
    assert chunks[0]["content"] == "Short text."
    assert chunks[0]["metadata"]["id"] == "thread-123-chunk-0"
    assert chunks[0]["metadata"]["chunk_index"] == 0
