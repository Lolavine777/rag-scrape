import pytest
from unittest.mock import MagicMock
from src.graph.graph import build_graph
from src.graph.state import AgentState
from src.graph.schemas import RouterDecision

def test_full_graph_execution_path_to_scraper(mocker):
    # Mock Router LLM call to return scraper_node
    mock_router_llm = MagicMock()
    mock_router_llm.invoke.return_value = RouterDecision(
        reasoning="Live topic",
        next_node="scraper_node",
        confidence=0.9
    )
    # Mock Generator LLM call
    mock_generator_llm = MagicMock()
    mock_generator_response = MagicMock()
    mock_generator_response.content = "Đã cào tin tức mới nhất từ Voz."
    mock_generator_llm.invoke.return_value = mock_generator_response

    # Patch both LLM calls
    mock_chat = mocker.patch("src.graph.router.ChatGoogleGenerativeAI")
    mock_chat.return_value.with_structured_output.return_value = mock_router_llm
    
    mock_gen = mocker.patch("src.graph.generator.ChatGoogleGenerativeAI")
    mock_gen.return_value = mock_generator_llm

    # Compile the graph
    app = build_graph()
    
    # Run the graph pipeline
    initial_state = AgentState(
        question="Tin tức mới nhất về iPhone?",
        loop_count=0,
        url=None,
        retrieved_context=None,
        answer=None,
        route_decision=None
    )
    final_state = app.invoke(initial_state)

    assert final_state["route_decision"] == "scraper_node"
    assert "Dữ liệu cào từ Voz" in final_state["retrieved_context"]
    assert final_state["answer"] == "Đã cào tin tức mới nhất từ Voz."

def test_full_graph_execution_path_to_rag(mocker):
    # Mock Router LLM call to return rag_node
    mock_router_llm = MagicMock()
    mock_router_llm.invoke.return_value = RouterDecision(
        reasoning="Historical query",
        next_node="rag_node",
        confidence=0.85
    )
    # Mock Generator LLM call
    mock_generator_llm = MagicMock()
    mock_generator_response = MagicMock()
    mock_generator_response.content = "Trả lời dựa trên CSDL RAG."
    mock_generator_llm.invoke.return_value = mock_generator_response

    # Patch both LLM calls
    mock_chat = mocker.patch("src.graph.router.ChatGoogleGenerativeAI")
    mock_chat.return_value.with_structured_output.return_value = mock_router_llm
    
    mock_gen = mocker.patch("src.graph.generator.ChatGoogleGenerativeAI")
    mock_gen.return_value = mock_generator_llm

    # Compile the graph
    app = build_graph()
    
    # Run the graph pipeline
    initial_state = AgentState(
        question="Python 3.12 là gì?",
        loop_count=0,
        url=None,
        retrieved_context=None,
        answer=None,
        route_decision=None
    )
    final_state = app.invoke(initial_state)

    assert final_state["route_decision"] == "rag_node"
    assert "Dữ liệu từ CSDL RAG" in final_state["retrieved_context"]
    assert final_state["answer"] == "Trả lời dựa trên CSDL RAG."
