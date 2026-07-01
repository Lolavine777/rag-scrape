import pytest
from src.graph.router import route_query
from src.graph.state import AgentState

def test_route_query_to_rag():
    state = AgentState(question="Python 3.10 release date?", loop_count=0)
    next_node = route_query(state, mock_decision="RAG")
    assert next_node == "rag_node"

def test_route_query_to_scraper():
    state = AgentState(question="What are people saying about the new iPhone on Voz today?", loop_count=0)
    next_node = route_query(state, mock_decision="SCRAPER")
    assert next_node == "scraper_node"

def test_route_query_prevents_infinite_loop():
    # loop_count = 2 nghĩa là đã cào thất bại 2 lần
    state = AgentState(question="Latest news?", loop_count=2)
    next_node = route_query(state, mock_decision="SCRAPER")
    
    # Bắt buộc bẻ nhánh về generator thay vì lặp lại scraper
    assert next_node == "generator_node"
