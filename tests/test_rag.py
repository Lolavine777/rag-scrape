import pytest
from unittest.mock import MagicMock

from src.rag.core import upsert_document, query_vector_db, reset_collection, _get_client



@pytest.fixture(autouse=True)
def mock_embedding(mocker):
    # Mock get_embedding helper inside RAG core module
    mock_func = mocker.patch("src.rag.core.get_embedding")
    # Return a deterministic mock vector
    mock_func.side_effect = lambda text: [float(hash(text) % 1000) / 1000.0] * 768
    return mock_func


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


def test_get_client_persistent(mocker):
    # Mock chroma PersistentClient and HttpClient
    mock_persist = mocker.patch("chromadb.PersistentClient")
    mock_http = mocker.patch("chromadb.HttpClient")

    # Reset core client cache
    mocker.patch("src.rag.core._client", None)

    mock_settings = mocker.patch("src.rag.core.settings")
    mock_settings.chroma_server_host = None
    mock_settings.chroma_persist_directory = "./test_persist_dir"

    client = _get_client()

    mock_persist.assert_called_once_with(path="./test_persist_dir")
    mock_http.assert_not_called()


def test_get_client_http(mocker):
    mock_persist = mocker.patch("chromadb.PersistentClient")
    mock_http = mocker.patch("chromadb.HttpClient")

    mocker.patch("src.rag.core._client", None)

    mock_settings = mocker.patch("src.rag.core.settings")
    mock_settings.chroma_server_host = "test-host"
    mock_settings.chroma_server_port = 8080

    client = _get_client()

    mock_http.assert_called_once_with(host="test-host", port=8080)
    mock_persist.assert_not_called()

