import pytest

from src.rag.core import upsert_document, query_vector_db, reset_collection


@pytest.fixture(autouse=True)
def clean_db():
    """Reset the Milvus collection before each test.

    autouse=True means this runs automatically for every test in this
    file without needing to explicitly request the fixture. This ensures
    each test starts with a clean slate - no leftover data from previous tests.
    """
    reset_collection()
    yield


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
