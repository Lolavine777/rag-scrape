import pytest
from unittest.mock import MagicMock
from main import main

def test_cli_reset_db(mocker):
    # Mock the reset_collection call in RAG core
    mock_reset = mocker.patch("main.reset_collection")
    
    # Run the main entry point with --reset-db argument
    main(args=["--reset-db"])
    
    mock_reset.assert_called_once()

def test_cli_ask_question(mocker):
    # Mock the graph compilation and execution
    mock_app = MagicMock()
    mock_app.invoke.return_value = {
        "question": "Python 3.12?",
        "loop_count": 1,
        "url": None,
        "retrieved_context": "Some context",
        "answer": "Đây là câu trả lời."
    }
    
    mock_build = mocker.patch("main.build_graph", return_value=mock_app)
    
    # Run the main entry point to ask a question
    main(args=["ask", "Python 3.12?"])
    
    mock_build.assert_called_once()
    mock_app.invoke.assert_called_once()
    
    # Verify the state passed to graph has the correct question and url=None
    called_state = mock_app.invoke.call_args[0][0]
    assert called_state["question"] == "Python 3.12?"
    assert called_state["url"] is None

def test_cli_ask_question_with_url(mocker):
    # Mock the graph compilation and execution
    mock_app = MagicMock()
    mock_app.invoke.return_value = {
        "question": "Review thớt",
        "loop_count": 1,
        "url": "https://voz.vn/t/123",
        "retrieved_context": "HTML content parsed",
        "answer": "Đã tóm tắt thớt."
    }
    
    mock_build = mocker.patch("main.build_graph", return_value=mock_app)
    
    # Run the main entry point with an optional url parameter
    main(args=["ask", "Review thớt", "--url", "https://voz.vn/t/123"])
    
    mock_build.assert_called_once()
    mock_app.invoke.assert_called_once()
    
    called_state = mock_app.invoke.call_args[0][0]
    assert called_state["question"] == "Review thớt"
    assert called_state["url"] == "https://voz.vn/t/123"


def test_cli_search(mocker):
    # Mock search_voz_threads to return a couple of threads
    mock_search = mocker.patch("src.scraper.voz_search.search_voz_threads")

    mock_search.return_value = [
        {"title": "Thread 1", "url": "https://voz.vn/t/1"},
        {"title": "Thread 2", "url": "https://voz.vn/t/2"}
    ]
    
    # Mock the graph compilation and execution for auto-indexing
    mock_app = MagicMock()
    mock_build = mocker.patch("main.build_graph", return_value=mock_app)
    
    # Run CLI search command
    main(args=["search", "python"])
    
    mock_search.assert_called_once_with("python")
    mock_build.assert_called_once()
    mock_app.invoke.assert_called_once()
    
    # Verify it auto-indexed the top thread URL
    called_state = mock_app.invoke.call_args[0][0]
    assert called_state["url"] == "https://voz.vn/t/1"
    assert "Thread 1" in called_state["question"]

