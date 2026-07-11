import logging
from langchain_google_genai import ChatGoogleGenerativeAI
from src.config import settings
from .state import AgentState
from .schemas import RouterDecision

logger = logging.getLogger(__name__)

def route_query(state: AgentState, mock_decision: str = "") -> str:
    # If loop_count >= 2, force routing to generator to prevent infinite loops
    if state.get("loop_count", 0) >= 2:
        logger.warning("Loop count limit reached. Routing to generator_node.")
        return "generator_node"
    
    # If a specific URL is provided, route directly to scraper
    if state.get("url"):
        logger.info("Direct URL provided in state. Routing to scraper_node.")
        return "scraper_node"

    # Support mock decision for tests
    if mock_decision == "SCRAPER":
        return "scraper_node"
    elif mock_decision == "RAG":
        return "rag_node"

    try:
        llm = ChatGoogleGenerativeAI(
            model=settings.gemini_model,
            google_api_key=settings.gemini_api_key,
            temperature=0.0
        ).with_structured_output(RouterDecision)
        
        prompt = (
            f"Analyze the user query: '{state['question']}'\n"
            "Decide if we need to scrape Voz forum for live content ('scraper_node') "
            "or query our local RAG database for existing knowledge ('rag_node')."
        )
        decision = llm.invoke(prompt)
        logger.info("Gemini routing decision: %s (reasoning: %s, confidence: %.2f)", 
                    decision.next_node, decision.reasoning, decision.confidence)
        return decision.next_node
    except Exception as e:
        logger.error("Error calling LLM for routing: %s. Defaulting to rag_node.", e)
        return "rag_node"
