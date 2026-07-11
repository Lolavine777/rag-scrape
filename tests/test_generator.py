import pytest
from unittest.mock import MagicMock
from src.graph.generator import generate_answer
from src.graph.state import AgentState

def test_generate_answer_success(mocker):
    mock_llm = MagicMock()
    mock_response = MagicMock()
    mock_response.content = "Đây là thông tin về Python 3.12 từ Voz."
    mock_llm.invoke.return_value = mock_response

    mock_class = mocker.patch("src.graph.generator.ChatGoogleGenerativeAI")
    mock_class.return_value = mock_llm

    state = AgentState(
        question="Python 3.12 có gì mới?",
        loop_count=0,
        url=None,
        retrieved_context="Dữ liệu cào từ Voz về Python 3.12: Tốc độ cải thiện 5-10%.",
        answer=None,
        route_decision=None
    )
    result = generate_answer(state)

    assert result["answer"] == "Đây là thông tin về Python 3.12 từ Voz."
    mock_llm.invoke.assert_called_once()

def test_generate_answer_error_fallback(mocker):
    mock_class = mocker.patch("src.graph.generator.ChatGoogleGenerativeAI")
    mock_class.return_value.invoke.side_effect = Exception("API Quota Exceeded")

    state = AgentState(
        question="Học Python ở đâu?",
        loop_count=0,
        url=None,
        retrieved_context=None,
        answer=None,
        route_decision=None
    )
    result = generate_answer(state)

    assert "Đã xảy ra lỗi khi tạo câu trả lời" in result["answer"]
    assert "API Quota Exceeded" in result["answer"]
