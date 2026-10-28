import logging
from src.graph.state import AgentState
from src.rag.core import build_context, search

logger = logging.getLogger(__name__)

def rag_node(state: AgentState) -> dict:
    """Runs hybrid (vector plus keyword) search over the local index and returns numbered context."""
    logger.info("RAG Node querying database for: %s", state["question"])
    return build_context(search(state["question"]))
