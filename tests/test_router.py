import pytest
from unittest.mock import MagicMock
from src.graph.router import route_query
from src.graph.state import AgentState
from src.graph.schemas import RouterDecision

def test_route_query_to_rag():
    state = AgentState(question="Python 3.10 release date?", loop_count=0, url=None, retrieved_context=None, answer=None, route_decision=None)
    next_node = route_query(state, mock_decision="RAG")
    assert next_node == "rag_node"

def test_route_query_to_scraper():
    state = AgentState(question="What are people saying about the new iPhone on Voz today?", loop_count=0, url=None, retrieved_context=None, answer=None, route_decision=None)
    next_node = route_query(state, mock_decision="SCRAPER")
    assert next_node == "scraper_node"

def test_route_query_prevents_infinite_loop():
    state = AgentState(question="Latest news?", loop_count=2, url=None, retrieved_context=None, answer=None, route_decision=None)
    next_node = route_query(state, mock_decision="SCRAPER")
    assert next_node == "generator_node"

def test_route_query_by_url():
    # If URL is set, should route directly to scraper without calling LLM
    state = AgentState(question="Check thread", loop_count=0, url="https://voz.vn/t/123", retrieved_context=None, answer=None, route_decision=None)
    next_node = route_query(state)
    assert next_node == "scraper_node"

def test_route_query_via_gemini_mock(mocker):
    # Mock ChatGoogleGenerativeAI
    mock_llm = MagicMock()
    # Mock the return value of with_structured_output(RouterDecision)
    mock_decision = RouterDecision(
        reasoning="Query asks for live forum feedback",
        next_node="scraper_node",
        confidence=0.95
    )
    mock_llm.invoke.return_value = mock_decision
    
    mock_class = mocker.patch("src.graph.router.ChatGoogleGenerativeAI")
    mock_class.return_value.with_structured_output.return_value = mock_llm
    
    state = AgentState(question="Is Voz down?", loop_count=0, url=None, retrieved_context=None, answer=None, route_decision=None)
    next_node = route_query(state)
    
    assert next_node == "scraper_node"
    mock_llm.invoke.assert_called_once()

def test_route_query_llm_failure_fallback(mocker):
    # Mock LLM raising an exception to verify fallback to rag_node
    mock_class = mocker.patch("src.graph.router.ChatGoogleGenerativeAI")
    mock_class.return_value.with_structured_output.side_effect = Exception("API Key Error")
    
    state = AgentState(question="What is Python?", loop_count=0, url=None, retrieved_context=None, answer=None, route_decision=None)
    next_node = route_query(state)
    
    assert next_node == "rag_node"

