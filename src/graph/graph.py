import logging
from langgraph.graph import StateGraph, END
from .state import AgentState
from .router import route_query
from .generator import generate_answer
from .nodes.scraper_node import scraper_node
from .nodes.rag_node import rag_node

logger = logging.getLogger(__name__)


def build_graph() -> StateGraph:
    """Build and compile the LangGraph StateGraph pipeline."""
    workflow = StateGraph(AgentState)
    
    # Define Nodes
    workflow.add_node("router_node", lambda state: {"route_decision": route_query(state)})
    workflow.add_node("scraper_node", scraper_node)
    workflow.add_node("rag_node", rag_node)
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

