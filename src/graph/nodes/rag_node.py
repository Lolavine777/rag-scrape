import logging
from src.graph.state import AgentState
from src.rag.core import build_context, query_vector_db

logger = logging.getLogger(__name__)

def rag_node(state: AgentState) -> dict:
    """Queries the local vector database using the user question and returns numbered context."""
    logger.info("RAG Node querying database for: %s", state["question"])
    return build_context(query_vector_db(state["question"]))
