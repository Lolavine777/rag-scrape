import pytest
from unittest.mock import MagicMock
from src.graph.state import AgentState
from src.graph.nodes.scraper_node import scraper_node
from src.graph.nodes.rag_node import rag_node

THREAD_HTML = """
<h1 class="p-title-value">Python 101</h1>
<article class="message message--post" data-content="post-1">
    <span class="username">Admin</span>
    <time class="u-dt" datetime="2026-07-01T10:00:00+0700">Jul 1</time>
    <div class="bbWrapper">Hello World, đây là bài viết đầu tiên.</div>
</article>
"""


def make_state(question, url=None):
    return AgentState(question=question, loop_count=0, url=url, retrieved_context=None,
                      answer=None, route_decision="scraper_node", sources=None)


def test_scraper_node_with_url(mocker):
    mock_fetch = mocker.patch("src.graph.nodes.scraper_node.fetch_voz_thread", return_value=THREAD_HTML)
    mock_upsert = mocker.patch("src.graph.nodes.scraper_node.upsert_document")

    result = scraper_node(make_state("Python 101", url="https://voz.vn/t/123"))

    mock_fetch.assert_called_once_with("https://voz.vn/t/123")
    mock_upsert.assert_called_once()
    assert result["retrieved_context"].startswith("[1] Admin, 2026-07-01T10:00:00+0700\nPython 101\nAdmin: Hello World")
    assert result["sources"] == [
        {"url": "https://voz.vn/t/123#post-1", "author": "Admin", "timestamp": "2026-07-01T10:00:00+0700"}
    ]

def test_scraper_node_extract_url_from_question(mocker):
    mock_fetch = mocker.patch("src.graph.nodes.scraper_node.fetch_voz_thread", return_value=THREAD_HTML)
    mocker.patch("src.graph.nodes.scraper_node.upsert_document")

    result = scraper_node(make_state("Đọc thớt này nhé https://voz.vn/t/thread-moi.98765/page-2"))

    mock_fetch.assert_called_once_with("https://voz.vn/t/thread-moi.98765/page-2")
    assert "Hello World" in result["retrieved_context"]

def test_scraper_node_indexes_non_xenforo_pages_as_plain_text(mocker):
    page = "<html><body><article>Một trang diễn đàn khác, không có cấu trúc bài viết XenForo.</article></body></html>"
    mocker.patch("src.graph.nodes.scraper_node.fetch_voz_thread", return_value=page)
    mock_upsert = mocker.patch("src.graph.nodes.scraper_node.upsert_document")

    result = scraper_node(make_state("Tóm tắt", url="https://forum.example/t/1"))

    mock_upsert.assert_called_once()
    assert "không có cấu trúc bài viết XenForo" in result["retrieved_context"]
    assert result["sources"][0]["url"] == "https://forum.example/t/1"

def test_scraper_node_no_url_fallback_to_rag(mocker):
    mock_query_db = mocker.patch("src.graph.nodes.scraper_node.query_vector_db", return_value=[
        {"content": "Dữ liệu lịch sử về Python", "metadata": {"id": "doc1"}}
    ])

    result = scraper_node(make_state("Python 3.12 có gì mới?"))

    mock_query_db.assert_called_once_with("Python 3.12 có gì mới?")
    assert result["retrieved_context"] == "[1]\nDữ liệu lịch sử về Python"

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
    assert "[1]\nChunk A từ DB" in result["retrieved_context"]
    assert "[2]\nChunk B từ DB" in result["retrieved_context"]
    assert len(result["sources"]) == 2
