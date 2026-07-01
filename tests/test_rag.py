import pytest
from src.rag.core import upsert_document, query_vector_db

def test_upsert_document_prevents_duplicates():
    doc_id = "url-123"
    metadata = {"url": "https://voz.vn/t/123", "id": doc_id}
    
    # Nạp lần 1
    upsert_document("Sample content", metadata)
    
    # Nạp lần 2 với cùng ID
    upsert_document("Updated content", metadata)
    
    results = query_vector_db("Sample")
    
    assert len(results) == 1
    assert results[0]["metadata"]["id"] == doc_id
    assert results[0]["content"] == "Updated content"
