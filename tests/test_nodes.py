import pytest
from unittest.mock import MagicMock
from src.graph.state import AgentState
from src.graph.nodes.scraper_node import scraper_node
from src.graph.nodes.rag_node import rag_node

def test_scraper_node_with_url(mocker):
    # Mock network fetching and parsing
    mock_fetch = mocker.patch("src.graph.nodes.scraper_node.fetch_voz_thread", return_value="<html>Mock Thread</html>")
    mock_parse = mocker.patch("src.graph.nodes.scraper_node.format_voz_thread", return_value="Thread Title: Python 101\nAdmin: Hello World")
    
    # Mock chunking and database upserting
    mock_chunk = mocker.patch("src.graph.nodes.scraper_node.chunk_document", return_value=[
        {"content": "Chunk 1", "metadata": {"url": "https://voz.vn/t/123", "id": "t123-chunk-0", "chunk_index": 0}}
    ])
    mock_upsert = mocker.patch("src.graph.nodes.scraper_node.upsert_document")
    
    state = AgentState(
        question="Python 101",
        loop_count=0,
        url="https://voz.vn/t/123",
        retrieved_context=None,
        answer=None,
        route_decision="scraper_node"
    )
    
    result = scraper_node(state)
    
    # Verify mock invocations
    mock_fetch.assert_called_once_with("https://voz.vn/t/123")
    mock_parse.assert_called_once_with("<html>Mock Thread</html>")
    mock_chunk.assert_called_once()
    mock_upsert.assert_called_once()
    
    assert "Thread Title: Python 101" in result["retrieved_context"]
    assert "Admin: Hello World" in result["retrieved_context"]

def test_scraper_node_extract_url_from_question(mocker):
    mock_fetch = mocker.patch("src.graph.nodes.scraper_node.fetch_voz_thread", return_value="<html>Mock</html>")
    mock_parse = mocker.patch("src.graph.nodes.scraper_node.format_voz_thread", return_value="Thread Content")
    mock_chunk = mocker.patch("src.graph.nodes.scraper_node.chunk_document", return_value=[])
    mock_upsert = mocker.patch("src.graph.nodes.scraper_node.upsert_document")
    
    # The URL is embedded inside the question text
    state = AgentState(
        question="Đọc thớt này nhé https://voz.vn/t/thread-moi.98765/page-2",
        loop_count=0,
        url=None,
        retrieved_context=None,
        answer=None,
        route_decision="scraper_node"
    )
    
    result = scraper_node(state)
    
    mock_fetch.assert_called_once_with("https://voz.vn/t/thread-moi.98765/page-2")
    assert result["retrieved_context"] == "Thread Content"

def test_scraper_node_no_url_fallback_to_rag(mocker):
    # Mock RAG query database
    mock_query_db = mocker.patch("src.graph.nodes.scraper_node.query_vector_db", return_value=[
        {"content": "Dữ liệu lịch sử về Python", "metadata": {"id": "doc1"}}
    ])
    
    # State has no URL
    state = AgentState(
        question="Python 3.12 có gì mới?",
        loop_count=0,
        url=None,
        retrieved_context=None,
        answer=None,
        route_decision="scraper_node"
    )
    
    result = scraper_node(state)
    
    mock_query_db.assert_called_once_with("Python 3.12 có gì mới?")
    assert result["retrieved_context"] == "Dữ liệu lịch sử về Python"

def test_rag_node(mocker):
    # Mock RAG database query
    mock_query_db = mocker.patch("src.graph.nodes.rag_node.query_vector_db", return_value=[
        {"content": "Chunk A từ DB", "metadata": {"id": "1"}},
        {"content": "Chunk B từ DB", "metadata": {"id": "2"}}
    ])
    
    state = AgentState(
        question="Học Python?",
        loop_count=0,
        url=None,
        retrieved_context=None,
        answer=None,
        route_decision="rag_node"
    )
    
    result = rag_node(state)
    
    mock_query_db.assert_called_once_with("Học Python?")
    assert "Chunk A từ DB" in result["retrieved_context"]
    assert "Chunk B từ DB" in result["retrieved_context"]
