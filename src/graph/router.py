from .state import AgentState

def route_query(state: AgentState, mock_decision: str = "") -> str:
    # Nếu đã lặp 2 lần, bắt buộc chuyển sang generator để tránh infinite loop
    if state.get("loop_count", 0) >= 2:
        return "generator_node"
    
    if mock_decision == "SCRAPER":
        return "scraper_node"
    return "rag_node"
