import logging
from src.graph.state import AgentState
from src.rag.core import query_vector_db

logger = logging.getLogger(__name__)

def rag_node(state: AgentState) -> dict:
    """Queries the local vector database using the user question and returns retrieved context."""
    logger.info("RAG Node querying database for: %s", state["question"])
    results = query_vector_db(state["question"])
    context = "\n\n".join([r["content"] for r in results])
    return {"retrieved_context": context}
