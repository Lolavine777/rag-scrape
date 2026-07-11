import logging
from langgraph.graph import StateGraph, END
from .state import AgentState
from .router import route_query
from .generator import generate_answer

logger = logging.getLogger(__name__)

def dummy_scraper_node(state: AgentState) -> dict:
    logger.info("Dummy Scraper Node executing.")
    # Return mock retrieved context for testing
    return {"retrieved_context": "Dữ liệu cào từ Voz về Python 3.12: Tốc độ cải thiện 5-10%."}

def dummy_rag_node(state: AgentState) -> dict:
    logger.info("Dummy RAG Node executing.")
    # Return mock retrieved context for testing
    return {"retrieved_context": "Dữ liệu từ CSDL RAG về Python 3.12."}

def build_graph() -> StateGraph:
    """Build and compile the LangGraph StateGraph pipeline."""
    workflow = StateGraph(AgentState)
    
    # Define Nodes
    workflow.add_node("router_node", lambda state: {"route_decision": route_query(state)})
    workflow.add_node("scraper_node", dummy_scraper_node)
    workflow.add_node("rag_node", dummy_rag_node)
    workflow.add_node("generator_node", generate_answer)
    
    # Set Entry Point
    workflow.set_entry_point("router_node")
    
    # Set Conditional Edges
    workflow.add_conditional_edges(
        "router_node",
        lambda state: state.get("route_decision", "rag_node"),
        {
            "scraper_node": "scraper_node",
            "rag_node": "rag_node",
            "generator_node": "generator_node"
        }
    )
    
    # Set Normal Edges
    workflow.add_edge("scraper_node", "generator_node")
    workflow.add_edge("rag_node", "generator_node")
    workflow.add_edge("generator_node", END)
    
    return workflow.compile()
